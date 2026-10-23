# 自由选择三种职责的模型

三权按当前项目定义对应：主协调/实现（main）、工作者/探索（worker）、顾问/审查（advisor）。职责不与模型家族绑定，可以将同一模型分配给两种或三种职责。Explorer/Researcher/Triage 使用 worker 分配，Architect 使用 advisor 分配。

```powershell
python scripts/triad.py init --project "C:\Projects\MyApp" --interactive --dry-run
python scripts/triad.py init --project "C:\Projects\MyApp" --interactive
```

交互流程：读取客户端 `model/list` 的可见候选及推理强度 → 为三种职责逐一输入编号或模型ID → 从所选模型支持的强度中选择 → 输出分配摘要与安装结果。不会因查询失败而退回硬编码候选列表；失败或取消时不写项目文件。已有安装会作为初选值，明确传入的模型/强度参数也可作为初选值。

非交互更新同样继承已有模型、推理强度和并发数，只覆盖明确传入的参数。例如 `init --project PATH --max-subagents 2` 只调整并发数；重复执行不带覆盖参数的 init 会保留原分配。首次安装仍使用原有预设值。旧参数和清单格式保持兼容。

如使用独立登录的 Codex home，可加 `--codex-home PATH`；继承现有系统代理可加 `--system-proxy`。仅影响模型查询子进程，不修改全局 Codex 配置或系统代理。普通 init 不查询模型；只有 --interactive 显式启用目录查询，不发起生成 turn，也不推断费用。

已有项目内手工 model/权限值仍受合并保护：安装不会强制覆盖它们，可能出现配置冲突警告，doctor 会报告偏差；请先对比实际结果。--force 不会绕过用户配置保护。

自动化也可直接用原参数指定任意模型ID：

```powershell
python scripts/triad.py init --project PATH --main-model MODEL_A --worker-model MODEL_B --advisor-model MODEL_C --main-effort high --worker-effort low --advisor-effort medium
```

上面的模型和强度是占位符，自动化应使用实际客户端返回的ID与支持选项。每个模型可以有不同强度；none/minimal 仅在对应模型报告支持时用于交互选择。

自定义组合的运行证据核验读取项目分配，避免错误套用历史预设：

```powershell
python scripts/triad.py report --runtime-evidence PRIVATE_EVIDENCE.json --project PATH --json
```

客户端列表可能来自缓存，可见候选不是账户权限或真实调用成功的证明。最终以明确授权后的真实 smoke/collector 测试为准；不自动做收费探测、不静默替换失效模型，不承诺跨 provider 自由混用。官方依据：[App Server model/list](https://learn.chatgpt.com/docs/app-server)。

2026-10-23 本机现场目录查询返回8项及其不同推理强度，生成turn数为0；查询期间全局config哈希一致。只记录为当前客户端返回值，不宣称8项都已实际调用。

English: the three responsibilities are independent of model branding. The interactive picker uses the client's paginated visible catalog and reasoning capabilities, allows reuse, preserves existing configuration and supports project-specific evidence verification. Catalog visibility is not a live access guarantee; paid probes remain opt-in.

本版验证：Windows Python 3.11/3.13 各77项通过；WSL Python3.12为75通过、2个Windows专项跳过。交互单测覆盖跨职责任意分配、同模型复用、无效输入、隐藏/空/错误目录、分页、取消及dry-run不写入。skill静态校验通过；没有为本次选择功能重复发起模型生成。
