# Validation / 验证与兼容性

This is an alpha preview. A passing static check, a successful model call, native role metadata and a provider-side identity proof are different kinds of evidence.

## Review hardening — 2026-10-24

- Windows / Python 3.13.5: 93 unit/integration tests passed, including the new home-target, partial-update, packaging, transport, collector and paired-CSV regressions. Source compilation and the diff whitespace check (allowing the existing CRLF files) passed.
- The clean wheel and standalone skill lifecycles passed. An extracted source ZIP also passed all 93 tests without a Git checkout.
- In an isolated copy, synthetic private files were added under `evaluation/`, `docs/` and `src/codex_triad/`. Actual wheel, source ZIP, skill ZIP and setuptools source-distribution builds excluded both their names and marker contents.
- `tests/test_collector.py` replays the existing sanitized Windows CLI 0.163.0 evidence through collection, including completion buffered before the request reply and an unrelated earlier turn. `tests/test_appserver.py` uses synthetic stdio messages to cover request/response ID overlap, errors, malformed messages, disconnect and timeout. These are offline contract checks, not a new live-client compatibility claim.
- `report --paired` was tested with synthetic matched/mismatched records, repeated tasks, failed runs and unknown costs. No real A/B study or savings result was produced.

The existing Windows/Linux CI matrix will run these regressions on the submitted commit. This local check did not run macOS or a new paid Codex workflow. The historical observations below retain their original date and scope.

## Observed results — 2026-10-23

| Check | Observed scope | Meaning |
|---|---|---|
| Unit/integration suite | 77 tests on Windows; CI matrix covers Windows/Linux × Python 3.11–3.14 | Installer, recovery, conflicts, selection and offline evidence behavior |
| Package checks | Clean wheel install and standalone skill archive lifecycle | Delivered artifacts work outside the checkout |
| npm skills installation | skills CLI 1.7.4, Node 24.18.0; project installation in default and copy modes | Installed helper passed all five offline commands; CI checks npm installation and bundled imports |
| 0.2.0a4 standalone live walkthrough | Extracted 19-file skill; real interactive preview/install/doctor, two concurrent Luna roles, Astra review, uninstall | Passed with a dedicated child CODEX_HOME; global config hashes identical, temporary auth reference removed |
| CLI role runtime | Windows Codex CLI 0.163.0; configured Sol coordinator, Luna workers, Astra advisor | App Server roles, parent/child IDs, startup models, completion and ordering |
| Model reuse | One model assigned to all three responsibilities, real native runtime pass | Responsibilities are not fixed to model families |
| Independent repair exercise | CSV tool; 13 original tests improved from 3 to 13 passing; 7 added tests and 7 parent checks passed | A concrete task completed; not a general quality benchmark |
| macOS native integration | Not tested | Do not infer it from Linux CI |
| Backend identity, speed/cost advantage | Not independently verified/measured | No identity certification or savings claim |

The source of the native evidence is described in [CLI verification](CLI_NATIVE_VERIFICATION.md); the sanitized fixture is [checked in](../evaluation/cli-runtime-20261023.json). The verifier checks internal consistency, not cryptographic provenance. CI status for each actual commit is visible in [GitHub Actions](https://github.com/ruanyueheng/codex-triad/actions/workflows/ci.yml).

Runtime observations apply to the tested account, date and client. Model catalogs and authorization can differ. Native role configuration also depends on project trust. No claim is made that every listed model is callable.

## Configuration-isolation observation

During a separate desktop collaboration repair exercise, the user's global reasoning setting changed from `ultra` to `high`. The user confirmed no manual switch. Explicit command review found no global config write, but the change's source was not established. The prior bytes were restored and verified by the original SHA-256.

That desktop exercise therefore **did not pass configuration-isolation acceptance**. It is reported separately from native CLI validation. A disposable project directory alone does not isolate client preference persistence. Use a child CLI/App Server with its own `CODEX_HOME` for tests requiring isolation; do not use desktop model/effort overrides to assert that guarantee. Keep before/after hashes local rather than publishing configuration contents.

## Reproduce the offline checks

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q src tests tools scripts
python tools/build_release.py
python tools/check_wheel.py
python scripts/triad.py report --runtime-evidence evaluation/cli-runtime-20261023.json --json
```

A normal pip install may access the network for build tools. The remaining commands perform offline checks, apart from a local CLI version probe. Follow [getting started](GETTING_STARTED.md) for a no-install file lifecycle.

Live checks are optional, quota-consuming and require normal client authentication. Instructions and exact evidence requirements are in [native verification](CLI_NATIVE_VERIFICATION.md). Do not upload raw client stderr, auth data, project configuration or recovery journals.

## Historical reports

`docs/work/` and root `WORK_*` files retain earlier development snapshots. Their old test counts and NOT_VERIFIED statements are historical, not the current status table. They are not required by the standalone skill. No single-model A/B comparison or production workload study has been completed.
