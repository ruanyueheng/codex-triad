import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codex_triad import storage
from codex_triad.installer import install, uninstall
from codex_triad.templates import Settings


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def snapshot(self):
        return {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*")
                if p.is_file() and p.name != ".triad.lock"}

    def fail_once(self, target):
        original = storage.atomic_write
        failed = False

        def write(path, value):
            nonlocal failed
            if path.name == target and not failed:
                failed = True
                raise PermissionError("injected failure")
            original(path, value)
        return write

    def test_install_rolls_back_all_files_on_write_failure(self):
        (self.root / "AGENTS.md").write_bytes(b"user rules\r\n")
        before = self.snapshot()
        with patch.object(storage, "atomic_write", side_effect=self.fail_once("triad_explorer.toml")):
            with self.assertRaisesRegex(storage.InstallationError, "rolled back"):
                install(self.root, Settings())
        self.assertEqual(self.snapshot(), before)

    def test_upgrade_rolls_back_manifest_and_files(self):
        install(self.root, Settings())
        before = self.snapshot()
        with patch.object(storage, "atomic_write", side_effect=self.fail_once("triad-state.json")):
            with self.assertRaises(storage.InstallationError):
                install(self.root, Settings(worker_model="other"))
        self.assertEqual(before, self.snapshot())

    def test_uninstall_rolls_back(self):
        install(self.root, Settings())
        before = self.snapshot()
        with patch.object(storage, "atomic_write", side_effect=self.fail_once("triad_architect.toml")):
            with self.assertRaises(storage.InstallationError):
                uninstall(self.root)
        self.assertEqual(before, self.snapshot())

    def interrupt_install(self):
        code = """
import os, sys
from pathlib import Path
from codex_triad import storage
from codex_triad.installer import install
from codex_triad.templates import Settings
original = storage.atomic_write
def crash(path, value):
    original(path, value)
    if path.name == 'triad_architect.toml':
        os._exit(19)
storage.atomic_write = crash
install(Path(sys.argv[1]), Settings())
"""
        result = subprocess.run([sys.executable, "-c", code, str(self.root)], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 19, result.stderr)

    def test_process_exit_retains_recoverable_journal(self):
        (self.root / "AGENTS.md").write_bytes(b"original\r\n")
        before = self.snapshot()
        self.interrupt_install()
        with self.assertRaisesRegex(storage.InstallationError, "Interrupted"):
            install(self.root, Settings())
        self.assertTrue(storage.recover(self.root))
        self.assertEqual(before, self.snapshot())
        install(self.root, Settings())

    def test_recovery_preserves_post_crash_edits(self):
        self.interrupt_install()
        policy = self.root / "AGENTS.md"
        policy.write_text("later edit", encoding="utf-8")
        with self.assertRaisesRegex(storage.InstallationError, "later edit"):
            storage.recover(self.root)
        self.assertEqual(policy.read_text(), "later edit")
        self.assertTrue((self.root / storage.JOURNAL).exists())

    def test_recovery_rejects_path_traversal(self):
        journal = self.root / storage.JOURNAL
        journal.parent.mkdir()
        journal.write_text('{"schema_version":1,"files":{"../outside":{"before":null,"after":null}}}')
        with self.assertRaises(storage.InstallationError):
            storage.recover(self.root)

    def test_lock_excludes_other_process_and_releases(self):
        code = "from pathlib import Path; from codex_triad.installer import install; from codex_triad.templates import Settings; import sys; install(Path(sys.argv[1]), Settings())"
        with storage.project_lock(self.root):
            result = subprocess.run([sys.executable, "-c", code, str(self.root)], capture_output=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"project lock", result.stderr)
        install(self.root, Settings())

    def test_changed_snapshot_is_rejected(self):
        path = self.root / "AGENTS.md"
        path.write_bytes(b"later")
        with self.assertRaises(storage.InstallationError):
            storage.apply_changes(self.root, {path: b"new"}, {path: b"before"})
        self.assertEqual(path.read_bytes(), b"later")

    def test_hardlink_refused(self):
        original = self.root / "original"
        original.write_bytes(b"user")
        try:
            (self.root / "AGENTS.md").hardlink_to(original)
        except OSError:
            self.skipTest("hardlinks unavailable")
        with self.assertRaises(storage.InstallationError):
            install(self.root, Settings())
        self.assertEqual(original.read_bytes(), b"user")

    @unittest.skipUnless(os.name == "nt", "Windows junction")
    def test_windows_junction_refused(self):
        outside = self.root / "outside"
        project = self.root / "project"
        outside.mkdir()
        project.mkdir()
        junction = project / ".codex"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.addCleanup(junction.rmdir)
        with self.assertRaises(storage.InstallationError):
            install(project, Settings())
        self.assertEqual(list(outside.iterdir()), [])

    def test_directory_in_place_of_file_refused(self):
        (self.root / "AGENTS.md").mkdir()
        with self.assertRaises(storage.InstallationError):
            install(self.root, Settings())

    @unittest.skipUnless(os.name == "nt", "Windows DACL")
    def test_atomic_replace_preserves_windows_dacl(self):
        import ctypes
        api = ctypes.WinDLL("advapi32", use_last_error=True)
        get_security = api.GetFileSecurityW
        get_security.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_void_p,
                                 ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        get_security.restype = ctypes.c_int
        get_dacl = api.GetSecurityDescriptorDacl
        get_dacl.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int),
                            ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_int)]
        get_dacl.restype = ctypes.c_int
        set_security = api.SetNamedSecurityInfoW
        set_security.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                                ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        set_security.restype = ctypes.c_uint32
        path = self.root / "AGENTS.md"
        path.write_bytes(b"original")

        def descriptor():
            needed = ctypes.c_uint32()
            get_security(str(path), 4, None, 0, ctypes.byref(needed))
            buffer = ctypes.create_string_buffer(needed.value)
            self.assertTrue(get_security(str(path), 4, buffer, needed, ctypes.byref(needed)))
            return buffer

        storage.atomic_write(path, b"protected-new-file")
        new_file = self.root / "private-backup.json"
        storage.atomic_write(new_file, b"private backup")
        original_path = path
        path = new_file
        private_descriptor = descriptor()
        private_control = int.from_bytes(private_descriptor.raw[2:4], "little")
        self.assertTrue(private_control & 0x1000)
        present, defaulted, dacl = ctypes.c_int(), ctypes.c_int(), ctypes.c_void_p()
        self.assertTrue(get_dacl(private_descriptor, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)))
        acl = ctypes.string_at(dacl, 28)
        self.assertEqual(int.from_bytes(acl[4:6], "little"), 1)  # Only OWNER RIGHTS has access.
        self.assertEqual(acl[16:28], b"\x01\x01\x00\x00\x00\x00\x00\x03\x04\x00\x00\x00")
        path = original_path
        before = descriptor()
        present, defaulted, dacl = ctypes.c_int(), ctypes.c_int(), ctypes.c_void_p()
        self.assertTrue(get_dacl(before, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)))
        self.assertEqual(set_security(str(path), 1, 4 | 0x80000000, None, None, dacl, None), 0)
        protected = descriptor().raw
        self.assertTrue(int.from_bytes(protected[2:4], "little") & 0x1000)
        storage.atomic_write(path, b"new")
        self.assertEqual(path.read_bytes(), b"new")
        after = descriptor().raw
        self.assertTrue(int.from_bytes(after[2:4], "little") & 0x1000)
        # Auto-inherited bookkeeping may change while protection and ACEs remain identical.
        self.assertEqual(after[:3] + bytes([after[3] & ~4]) + after[4:],
                         protected[:3] + bytes([protected[3] & ~4]) + protected[4:])
