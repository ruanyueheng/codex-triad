# 自由选择三种职责的模型

三权按当前项目定义对应：主协调/实现（main）、工作者/探索（worker）、顾问/审查（advisor）。职责不与模型家族绑定，可以将同一模型分配给两种或三种职责。Explorer/Researcher/Triage 使用 worker 分配，Architect 使用 advisor 分配。

先独立查看当前环境的模型和推理强度，再决定配置：

```powershell
python scripts/triad.py models --project PATH
python scripts/triad.py models --project PATH --json
python scripts/triad.py init --project PATH --interactive --dry-run
python scripts/triad.py init --project PATH --interactive
```

`models` 不写项目角色或启动生成 turn；输出来自客户端目录，不表示已验证实际调用权限。交互流程为每种职责分别选择模型及其报告支持的推理强度，可让同一模型承担多种职责。失败或取消不写入。`--codex-home` 和 `--system-proxy` 同样适用于独立查询。

已有项目可按需检查当前配置与客户端目录是否匹配：

```powershell
python scripts/triad.py doctor --project PATH --check-models --json
python scripts/triad.py doctor --project PATH --check-models --codex-home ISOLATED_HOME
```

默认 `doctor` 保持静态；`--check-models` 启动客户端 App Server，只查询模型目录，不启动线程或生成 turn，不修改项目配置。检查主模型、默认工作者和四个角色文件中的实际模型/强度，包括保留的用户配置及角色文件的本地编辑；存在静态 FAIL 时先修复，不查询目录。客户端可能维护自己的状态，需要隔离时指定单独的 `--codex-home`。

探测子进程从启动时禁用 hooks、apps 和 plugins，减少与目录查询无关的扩展初始化和 Git 同步；覆盖只作用于该子进程，不更改全局设置。查询结束先关闭 stdin 等待退出，超时再有界终止。

`MODEL_NOT_LISTED` 与 `MODEL_EFFORT_NOT_LISTED` 是 WARN，分别指出未列出的模型和强度；可运行 `models` 或 `init --interactive --dry-run` 核对，保持相同的 `--project`、`--codex-home` 和代理选项。查询失败为 `MODEL_CATALOG: UNKNOWN`，匹配为 `MODEL_LISTED: PASS`，均不证明或否定实际调用权限。退出码仍为静态 FAIL 时 1，其余 0；自动化需要检查 JSON 中的具体 level/code。`--codex-home` / `--system-proxy` 在 doctor 中必须与 `--check-models` 同用。

不指定模型时，首次 `init` 自动查询客户端 `model/list`，默认主协调选择最新稳定 Sol，工作者选择最新稳定 Luna，顾问选择最新稳定 Astra。只匹配客户端实际返回的 `gpt-版本-系列` ID（允许 provider 前缀），按数字版本比较，例如 6.10 高于 6.9；同版本优先 `-latest`，其次无日期滚动 ID，最后选择最新日期快照。默认不选择 preview、mini、pro 等不同变体；无法识别的命名需手动指定。这里的“最新”是客户端当前可见的稳定候选，不是全网发布或账户权限认证。

自动选择的职责记录在清单 `auto_model_roles` 中；再次运行 `init` 时重新查询并更新这些职责。传入 `--main-model` / `--worker-model` / `--advisor-model` 会将对应职责改为手动固定；交互选择固定三种职责。旧清单没有该字段时保留原有模型，不推断当初是否由用户选择。只查询缺少显式覆盖的自动职责所需系列；已有模型、provider 和权限的合并保护仍然生效。

缺少某个系列或查询失败会报错，且不写项目文件；不会将 Luna 悄悄改为 Sol。自动推理强度记录在 `auto_effort_roles`，优先保留兼容强度；新模型不支持时采用其报告的默认值。明确指定或历史清单中固定的强度不支持时要求用户更改；`--interactive` 可进入选择器修复这类冲突。安装在事务锁内核对选模依据的清单，发现并发修改时停止，避免覆盖新手动选择。预览包含清单变化，显示自动/固定状态的切换。

```powershell
python scripts/triad.py init --project "C:\Projects\MyApp" --dry-run
python scripts/triad.py init --project "C:\Projects\MyApp"
python scripts/triad.py init --project "C:\Projects\MyApp" --interactive --dry-run
python scripts/triad.py init --project "C:\Projects\MyApp" --interactive
```

交互流程：读取客户端 `model/list` 的可见候选及推理强度 → 为三种职责逐一输入编号或模型ID → 从所选模型支持的强度中选择 → 输出分配摘要与安装结果。不会因查询失败而退回硬编码候选列表；失败或取消时不写项目文件。已有安装会作为初选值，明确传入的模型/强度参数也可作为初选值。

非交互更新保留手动模型、已有推理强度和并发数，自动模型随当前目录更新。旧参数和清单格式保持兼容。

如使用独立配置的 Codex home，可加 `--codex-home PATH`；继承现有系统代理可加 `--system-proxy`。仅影响模型查询子进程，不修改全局 Codex 配置或系统代理。自动选择和 --interactive 都查询目录，不发起生成 turn；三个模型均显式指定时可离线安装。

已有项目内手工 model/权限值仍受合并保护：安装不会强制覆盖它们，可能出现配置冲突警告，doctor 会报告偏差；请先对比实际结果。--force 不会绕过用户配置保护。

自动化也可直接用原参数指定任意模型ID：

```powershell
python scripts/triad.py init --project PATH --main-model MODEL_A --worker-model MODEL_B --advisor-model MODEL_C --main-effort high --worker-effort low --advisor-effort medium
```

上面的模型和强度是占位符，自动化应使用实际客户端返回的ID与支持选项。每个模型可以有不同强度；none/minimal 仅在对应模型报告支持时用于交互选择。

Python API `install(project, settings)` 接收完整明确的分配，默认固定各职责；需要保留自动跟踪的调用者应显式传入 `auto_model_roles` 和 `auto_effort_roles`。这与交互选择固定三种职责一致。

自定义组合的运行证据核验读取项目分配，避免错误套用历史预设：

```powershell
python scripts/triad.py report --runtime-evidence PRIVATE_EVIDENCE.json --project PATH --json
```

客户端列表可能来自缓存，可见候选不是账户权限或真实调用成功的证明。最终以明确授权后的真实 smoke/collector 测试为准；不自动做收费探测、不静默替换失效模型，不承诺跨 provider 自由混用。官方依据：[App Server model/list](https://learn.chatgpt.com/docs/app-server)。

2026-10-23 本机现场目录查询返回8项及其不同推理强度，生成turn数为0；查询期间全局config哈希一致。只记录为当前客户端返回值，不宣称8项都已实际调用。

English: defaults resolve the latest visible stable Sol/Luna/Astra. Automatic roles refresh on init; explicit or interactive choices and legacy manifests remain pinned. Selection compares numeric versions and prefers rolling aliases, excludes variant IDs, and fails without writes when a family is absent. The picker still allows any model and reuse. Catalog visibility is not a live access guarantee; paid probes remain opt-in.

本版验证：Windows Python 3.11/3.13 各77项通过；WSL Python3.12为75通过、2个Windows专项跳过。交互单测覆盖跨职责任意分配、同模型复用、无效输入、隐藏/空/错误目录、分页、取消及dry-run不写入。skill静态校验通过；没有为本次选择功能重复发起模型生成。
