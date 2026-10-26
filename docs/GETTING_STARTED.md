# Getting started / 上手指南

Choose one route: the graphical workbench prepares and launches tasks, the bundled CLI configures project roles, and the skill teaches Codex how to use them. Installation itself does not launch agents.

选择用途：图形工作台负责选择任务和协作方式，CLI 负责项目角色配置，skill 负责工作流指引。安装本身不会启动 Agent。

## Graphical task workbench

在源码目录运行 `python scripts/triad.py gui --project PATH`，或在 Windows 双击 `scripts/triad_gui.pyw`。安装 wheel 后也可运行 `codex-triad-gui`。图形界面使用 Python 自带的 Tk；没有 Tk 的精简 Python 环境仍可使用原有 CLI。

1. 选择项目目录。左侧读取该项目的主协调、工作者和顾问模型；未配置时沿用 Codex 当前设置，不强制先安装角色。
2. 填写想完成的任务，或选“修复问题 / 开发功能 / 审查改动”模板。模板不会覆盖已经输入的内容。
3. 选择自动协作、快速处理、多人协作或只做审查。“自动”由 Codex 根据任务决定分工，“快速”要求主协调直接处理，“多人”请求独立调查与审查。
4. 点击“开始任务”打开 Codex 交互窗口；也可预览指令，或复制到已有 Codex 对话。复制内容包含选定项目路径和协作方式。点击启动才会进入实际执行并可能消耗模型额度。

Windows 使用新控制台启动当前安装的 Codex；Linux 需要 `x-terminal-emulator`。没有支持的终端启动器（包括当前 macOS 路径）时，使用“复制到当前对话”。只做审查在新窗口附加 `--sandbox read-only`；复制的指令不改变已有会话的权限。其他模式沿用客户端与项目的模型、权限和信任设置，不写入全局配置。

工作台是任务入口，执行与后续对话仍在 Codex 中。模式是协作偏好，实际子代理是否可用取决于客户端；没有可用角色时会要求如实说明并继续可完成的工作。

## Prerequisites

- Python 3.11+; runtime code has no third-party dependencies.
- Codex CLI authenticated with your normal account for model lookup or live collection. Supported role/effort fields depend on the client; CLI 0.163.0 was tested on Windows.
- An existing target project directory. Review it before granting trust. Unknown configuration is preserved, so check `doctor` after installation.

CLI walkthroughs below start in the cloned `codex-triad` source directory. The npm installation section runs in your target project. `python` means your chosen Python 3.11+ interpreter.

## Offline walkthrough

This route needs no Codex login or model access. It uses the legacy presets to demonstrate file operations, not to prove those model IDs are available to you.

```bash
mkdir ../triad-offline-demo
python scripts/triad.py init --project ../triad-offline-demo --main-model gpt-6.1-sol --worker-model gpt-6-luna --advisor-model gpt-6-astra --dry-run
python scripts/triad.py init --project ../triad-offline-demo --main-model gpt-6.1-sol --worker-model gpt-6-luna --advisor-model gpt-6-astra
python scripts/triad.py doctor --project ../triad-offline-demo --json
python scripts/triad.py smoke --phase workers
python scripts/triad.py report --runtime-evidence evaluation/cli-runtime-20261023.json --json
python scripts/triad.py uninstall --project ../triad-offline-demo --dry-run
python scripts/triad.py uninstall --project ../triad-offline-demo
```

Expected: preview prints proposed changes, install creates the role/config files, doctor reports static facts and runtime `UNKNOWN`, smoke prints a prompt, report validates the supplied historical fixture, and uninstall removes unedited managed content. None of these offline commands generates model requests. Empty directories and `.triad.lock` may remain.

`doctor` exit 0 means no static FAIL, not a verified working account. Partial uninstall can also retain exit 0 for compatibility: read `PARTIAL_UNINSTALL` messages.

## Choose models before use

For an actual project, use a fresh target directory or inspect existing settings first:

```bash
python scripts/triad.py models --project ../my-app
python scripts/triad.py models --project ../my-app --json
python scripts/triad.py init --project ../my-app --interactive --dry-run
python scripts/triad.py init --project ../my-app --interactive
python scripts/triad.py doctor --project ../my-app --json
```

Choose a catalog number or full ID and a supported reasoning effort for each responsibility. Reuse is allowed. Preview choices are not saved. Query failure or cancellation does not write project files. Catalog visibility is not proof of account permission; do not silently fall back after a failed call.

For automation use `--main-model`, `--worker-model`, `--advisor-model` and the corresponding `--*-effort` flags with IDs/options valid for your client. Existing user configuration remains protected. See [model assignment](MODEL_ASSIGNMENT.md).

Without model flags, a fresh installation selects the latest visible stable Sol/Luna/Astra for coordinator/workers/advisor. Re-running `init` refreshes roles recorded as automatic. Explicit model flags and interactive choices pin their roles; historical manifests also keep their saved choices. Compatible saved efforts and concurrency stay unchanged. Automatic efforts can adapt to a new model's capabilities; unsupported pinned efforts require explicit correction or `--interactive`. See [selection rules](MODEL_ASSIGNMENT.md).

Default discovery and `--interactive` query the local client without starting generation turns. A missing family stops automatic installation; select a model explicitly or use the interactive picker. Specifying all three models skips discovery and supports offline setup.

The default and configured Codex homes are protected targets, including when a project would use one as its `.codex` directory. Install, uninstall and recovery refuse these targets before creating a lock. Choose a normal project directory; managed worktrees inside a Codex home remain supported.

The main model is a project configuration target: it does not switch the model of an already-running desktop chat. Open a new session in the trusted target and verify its effective settings. Workers and advisor are custom roles, not an independent security sandbox.

If a desktop configuration contains fields or MCP transports unsupported by the installed CLI, App Server startup can fail before listing models. Preserve the original configuration, configure/authenticate a separate Codex home through the normal client, and pass `--codex-home PATH`. Do not rewrite global settings to hide a client-version mismatch. See [troubleshooting](TROUBLESHOOTING.md).

## Use the skill

### Install with npm / 使用 npm 安装

From your target project, run:

```bash
npx skills add ruanyueheng/codex-triad --agent codex
```

The [skills CLI](https://github.com/vercel-labs/skills) downloads the skill from GitHub into `.agents/skills/codex-triad/`. It requires Node.js 22.20+. Python 3.11+ runs the bundled configuration helper.

For a non-interactive copy installation:

```bash
npx --yes skills add ruanyueheng/codex-triad --skill codex-triad --agent codex --copy --yes
```

Check the installation with `npx skills list --agent codex`, then invoke `$codex-triad` in Codex. Restart Codex if the new skill has not appeared yet. The npm package supplies the installer; the skill itself comes from this repository.

### ZIP or source installation

You can also reference the cloned root `SKILL.md` by absolute path, or extract the whole skill ZIP into `.agents/skills/`.

Build it locally with existing setuptools/wheel, or download the preview artifact from a successful [CI run](https://github.com/ruanyueheng/codex-triad/actions/workflows/ci.yml) (GitHub may require sign-in for artifact downloads):

```bash
python tools/build_release.py
```

PowerShell example after building 0.2.0a5; choose your actual target path:

```powershell
New-Item -ItemType Directory -Force 'C:\Projects\MyApp\.agents\skills'
Expand-Archive -LiteralPath '.\dist\codex-triad-0.2.0a5-skill.zip' -DestinationPath 'C:\Projects\MyApp\.agents\skills'
```

The destination `codex-triad` folder must not already exist; compare an existing skill before upgrading. On macOS/Linux, extract the same ZIP into the target's `.agents/skills/` with your archive tool. Preserve `SKILL.md`, `LICENSE`, `scripts/`, `src/`, `docs/` and `evaluation/` together. No global pip or Codex configuration change is required.

Check `/skills` or invoke `$codex-triad`. Codex detects local skills; restart if it does not appear. This follows [official skill discovery guidance](https://learn.chatgpt.com/docs/build-skills).

Example task:

```text
$codex-triad
Fix the CSV import regression in this repository. Keep its public interfaces.
Use the project's selected models and scoped investigations where useful.
Run the existing acceptance tests unchanged and have the advisor review the diff.
Do not commit, publish or change global settings unless I ask.
```

For installation instead of implementation:

```text
$codex-triad
Preview setup for the current repository and let me assign its three responsibilities.
Preserve existing settings. Show static diagnostics and distinguish runtime unknowns.
```

### Remove the skill

Remove Triad's project roles from your target project:

```bash
python .agents/skills/codex-triad/scripts/triad.py uninstall --project . --dry-run
python .agents/skills/codex-triad/scripts/triad.py uninstall --project .
```

Then delete `.agents/skills/codex-triad/` to remove the skill files.

## Optional Python package installation

Use a virtual environment if you prefer a `codex-triad` console command:

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m codex_triad --help
```

macOS/Linux:

```bash
.venv/bin/python -m pip install -e .
.venv/bin/python -m codex_triad --help
```

Ordinary pip installation may download build tooling. With suitable setuptools/wheel already installed, an offline build can use `--no-index --no-deps --no-build-isolation`. Do not use `pip install codex-triad` as a project installation instruction: this project has not published that package on PyPI.

## Real runtime checks and isolation

Only run paid model tests when authorized. Use a disposable trusted project and, when configuration isolation is required, a separately configured/logged-in Codex home:

```bash
python scripts/collect_runtime.py --project ../triad-demo --codex-home /path/to/isolated-codex-home --output /path/to/new-private-output --run
```

Paths are placeholders and must be replaced; the home must exist and output must be new. Configure authentication through the normal client; never put credentials in this repository. `--system-proxy` optionally inherits your existing system proxy in the child only. Do not relax global permissions to make a check pass.

The collector performs a bounded, read-only delegation fixture, not a production code repair. It checks two concurrent workers followed by an advisor. Inspect its result and original errors. Keep logs private; model runtime metadata is not independent backend identity. See [native verification](CLI_NATIVE_VERIFICATION.md) and [validation limits](VALIDATION.md).

## Conflicts and recovery

- Unknown role files: compare/move them yourself; `--force` does not claim them.
- Preserved model/provider settings: inspect the warning and effective project config, not just the requested assignment.
- Interrupted transaction: protect `.codex/.triad-transaction.json`, then run `init --project PATH --recover`. Recovery refuses later conflicting edits.
- Modified installed files: uninstall retains them and the relevant manifest entries.

[Full troubleshooting](TROUBLESHOOTING.md) · [Storage guarantees and limits](ADR-001-SAFE-INSTALL.md).
