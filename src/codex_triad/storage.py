"""Project-local path guards, process lock and recoverable file transactions."""
from __future__ import annotations

import base64
import json
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .templates import AGENT_NAMES


class InstallationError(Exception):
    pass


MANAGED_PATHS = {"AGENTS.md", ".codex/config.toml", ".codex/triad-state.json",
                 *(f".codex/agents/{name}.toml" for name in AGENT_NAMES)}
JOURNAL = ".codex/.triad-transaction.json"


def assert_safe_paths(project: Path, targets: list[Path]) -> None:
    for target in targets:
        if not target.is_relative_to(project) or ".." in target.parts:
            raise InstallationError(f"Path escapes project: {target}")
        current = target
        while current != project:
            try:
                info = current.lstat()
            except FileNotFoundError:
                current = current.parent
                continue
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise InstallationError(f"Symlink/reparse point not allowed: {current}")
            if current == target:
                if not stat.S_ISREG(info.st_mode) or info.st_nlink > 1:
                    raise InstallationError(f"Expected an ordinary, unshared file: {current}")
            elif not stat.S_ISDIR(info.st_mode):
                raise InstallationError(f"Expected directory: {current}")
            current = current.parent


def read_bytes(path: Path) -> bytes | None:
    return path.read_bytes() if path.exists() else None


def read_text(path: Path) -> str:
    try:
        data = read_bytes(path)
        return data.decode("utf-8") if data is not None else ""
    except UnicodeError as exc:
        raise InstallationError(f"Expected UTF-8 at {path}") from exc


def _restrict_windows_temp(path: Path) -> None:
    """Make the empty staging file owner-only before any backup/config bytes are written."""
    import ctypes
    api = ctypes.WinDLL("advapi32", use_last_error=True)
    convert = api.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
    convert.restype = ctypes.c_int
    descriptor = ctypes.c_void_p()
    if not convert("D:P(A;;FA;;;OW)", 1, ctypes.byref(descriptor), None):
        raise ctypes.WinError(ctypes.get_last_error())
    free = ctypes.WinDLL("kernel32", use_last_error=True).LocalFree
    free.argtypes = [ctypes.c_void_p]
    free.restype = ctypes.c_void_p
    try:
        get_dacl = api.GetSecurityDescriptorDacl
        get_dacl.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int),
                            ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_int)]
        get_dacl.restype = ctypes.c_int
        present, defaulted, dacl = ctypes.c_int(), ctypes.c_int(), ctypes.c_void_p()
        if not get_dacl(descriptor, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)):
            raise ctypes.WinError(ctypes.get_last_error())
        set_security = api.SetNamedSecurityInfoW
        set_security.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                                ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        set_security.restype = ctypes.c_uint32
        error = set_security(str(path), 1, 4 | 0x80000000, None, None, dacl, None)
        if error:
            raise ctypes.WinError(error)
    finally:
        free(descriptor)


def atomic_write(path: Path, content: bytes | None) -> None:
    if content is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".triad-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            if os.name == "nt":
                _restrict_windows_temp(temporary)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            temporary.chmod(stat.S_IMODE(path.stat().st_mode))
        if os.name == "nt" and path.exists():
            # ReplaceFile preserves the existing Windows DACL; rename/replace does not.
            import ctypes
            replace = ctypes.WinDLL("kernel32", use_last_error=True).ReplaceFileW
            replace.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
                                ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p]
            replace.restype = ctypes.c_int
            if not replace(str(path), str(temporary), None, 0, None, None):
                raise ctypes.WinError(ctypes.get_last_error())
        else:
            os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def project_lock(project: Path):
    if not project.is_dir():
        raise InstallationError(f"Project directory not found: {project}")
    path = project / ".codex/.triad.lock"
    assert_safe_paths(project, [path])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if path.stat().st_size == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise InstallationError("Another Triad operation holds the project lock; retry after it exits") from exc
        try:
            yield
        finally:
            if os.name == "nt":
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def ensure_no_pending(project: Path) -> None:
    path = project / JOURNAL
    assert_safe_paths(project, [path])
    if path.exists():
        raise InstallationError("Interrupted transaction found. Review local backups, then run init/uninstall --recover")


def apply_changes(project: Path, changes: dict[Path, bytes | None], before: dict[Path, bytes | None]) -> None:
    changes = {p: value for p, value in changes.items() if value != before[p]}
    if not changes:
        return
    assert_safe_paths(project, list(before) + [project / JOURNAL])
    if any(read_bytes(p) != value for p, value in before.items()):
        raise InstallationError("Project files changed during planning; retry without concurrent editors")
    entries = {}
    for path, after in changes.items():
        relative = path.relative_to(project).as_posix()
        if relative not in MANAGED_PATHS:
            raise InstallationError(f"Unmanaged transaction path: {relative}")
        entries[relative] = {key: base64.b64encode(value).decode("ascii") if value is not None else None
                             for key, value in (("before", before[path]), ("after", after))}
    journal = project / JOURNAL
    atomic_write(journal, json.dumps({"schema_version": 1, "files": entries}).encode("utf-8"))
    try:
        for path, value in changes.items():
            assert_safe_paths(project, [path])
            if read_bytes(path) != before[path]:
                raise InstallationError("Project file changed before write; transaction stopped")
            atomic_write(path, value)
    except Exception as exc:
        try:
            _restore(project)
        except (OSError, InstallationError) as recovery:
            raise InstallationError(f"Transaction failed; recovery required: {recovery}") from exc
        raise InstallationError(f"Transaction failed and was rolled back: {exc}") from exc
    journal.unlink()


def _restore(project: Path) -> list[str]:
    journal = project / JOURNAL
    assert_safe_paths(project, [journal])
    try:
        data = json.loads(read_text(journal))
        if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
            raise ValueError("unsupported schema")
        files = data["files"]
        if not isinstance(files, dict) or not files or not set(files) <= MANAGED_PATHS:
            raise ValueError("invalid paths")
        decoded = {}
        for relative, versions in files.items():
            if not isinstance(versions, dict) or set(versions) != {"before", "after"}:
                raise ValueError("invalid backup entry")
            decoded[project / relative] = {key: base64.b64decode(value, validate=True) if value is not None else None
                                           for key, value in versions.items()}
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise InstallationError("Invalid transaction journal; inspect backups manually") from exc
    assert_safe_paths(project, list(decoded))
    for path, versions in decoded.items():
        if read_bytes(path) not in (versions["before"], versions["after"]):
            raise InstallationError(f"Recovery would overwrite a later edit: {path.name}; backup retained")
    output = []
    for path, versions in reversed(list(decoded.items())):
        if read_bytes(path) != versions["before"]:
            atomic_write(path, versions["before"])
            output.append(f"RESTORED {path.relative_to(project).as_posix()}")
    journal.unlink()
    return output or ["Recovery complete; original files already intact"]


def recover(project: Path) -> list[str]:
    project = project.resolve()
    with project_lock(project):
        if not (project / JOURNAL).exists():
            return ["No interrupted transaction to recover"]
        return _restore(project)
