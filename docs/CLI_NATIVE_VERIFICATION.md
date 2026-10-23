# CLI 原生角色、线程与模型验收 / Native CLI verification

2026-10-23，Codex CLI 0.163.0，Windows。本版使用本机 `codex app-server --listen stdio://` 的正式 JSON-RPC 接口取证，不抓取不稳定的 transcript/SQLite 内容。

## 已获得的证据

`evaluation/cli-runtime-20261023.json` 是真实运行记录的脱敏子集。父线程为 `01a1674c-8239-77f3-b5dc-7a9074d5a80a`，root model 为 gpt-6.1-sol；三个子线程的 `agentRole` 与启动活动对应如下：

| 角色 | 子线程 ID | 启动活动中的模型 |
|---|---|---|
| triad_explorer | 01a1674c-b3a9-73d2-aaa9-b2712b70eba0 | gpt-6-luna |
| triad_researcher | 01a1674c-c137-7300-9b2e-c9d8c8f4e9c9 | gpt-6-luna |
| triad_architect | 01a1674c-f38a-76b0-917d-ed963cfa0be7 | gpt-6-astra |

两 worker 执行区间重叠，advisor 在两者完成后启动，三个子线程均有完成活动；主 turn 也成功完成。模型记录是 **客户端运行时选用值**，不是服务端返回的独立模型身份证明；后者仍是 UNKNOWN。

额外做了局部 Agent 指令随机标记实验：Researcher 和 Architect 返回了只存在其角色文件中的标记；Explorer 未返回标记，因此不宣称每次都遵守角色指令。另一次普通运行已由角色/线程元数据证明三个角色被注册并执行，不能仅凭某次输出缺少标记断言配置完全未加载。

## 为什么此前 exec 输出证据不足

0.163.0 的 App Server `subAgentActivity` 包含 `agentThreadId`、`model`、`reasoningEffort` 和生命周期。此前 `codex exec --json` 的精简输出没有呈现这些活动，而 wait 的 receiverThreadIds 为空。完成通知的 model 可为 null；应按同一 child ID 关联 started 模型，不能把 null 覆盖掉之前的启动证据。`thread/list` 的 agentRole/parentThreadId 用于交叉核对角色和父子关系。线程 metadata.model 不能单独当成逐 turn 执行遥测。

正式来源：[App Server](https://learn.chatgpt.com/docs/app-server)、[Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)。使用本机 `codex app-server generate-json-schema --experimental --out PATH` 导出的协议核对字段，不能假定所有旧客户端都支持。

## 不花模型额度的离线核验

从源码或 skill 文件夹运行，Python 3.11+：

```powershell
python scripts/triad.py report --runtime-evidence evaluation/cli-runtime-20261023.json --json
```

核验器要求三个不同子线程、精确角色与模型、同一父线程和同一成功 turn、完整生命周期、worker 重叠及 advisor 顺序。模型自述、空 wait、缺失/错配的线程/模型、混合 turn 以及无效时间戳都会失败。它校验所给记录的内部一致性，不对文件来源做密码学认证。CLI 此入口默认核对历史默认模型；自定义模型请加 `--project PATH` 读取该项目的分配，或通过 Python `verify_runtime(path, settings)` 传入 Settings。

## 可复现的真实采集（消耗额度）

先用 `python scripts/triad.py init --project PATH --dry-run` 预览，再安装到可信可丢弃项目。保持原配置保护；不要为了通过烟测而覆盖已有 model/provider/权限。脚本要求已有有效的 Triad 状态清单和可用的 Codex 登录。

```powershell
python scripts/collect_runtime.py --project PATH --output NEW_PRIVATE_DIRECTORY --run
```

- 输出目录必须不存在，避免覆盖原证据。脚本仅导出核验必要的协议字段，不导出 prompts、完整配置或凭据；server.stderr.txt 仍可能有私有路径，不应直接发布。
- 如需独立环境，先单独配置并登录一个 Codex home，再传 `--codex-home PATH`；该变量只用于子进程，不会改父进程或全局 config.toml。脚本不复制凭据，不自动登录或修改 trust 配置。
- 需要继承已有系统代理时使用 `--system-proxy`，只影响子进程。不要把这里的网络设置固化为所有用户的通用配置。
- 使用持久测试会话，保留在选定 home；不启用 hook，不放宽 read-only 沙箱，不审批需要交互的操作。超时尝试 interrupt，随后结束本次 server。若协议或授权不兼容，返回原始错误而非模拟成功。
- SDK/App Server 接口经过现场核对，仍可能随版本改变；缺少字段时核验应失败，不估算模型/线程结果。API费用和整体节省尚未实测。

## Skill 与 GitHub

仓库根目录即一个自包含 `codex-triad` skill：SKILL.md、scripts/、src/ 和按需文档保持同级。无须先全局 pip 安装。发布包提供以 codex-triad/ 为顶层的 skill ZIP；未来安装时选择整个 skill 根目录，不能只复制 SKILL.md。

当前只在仓库内准备 skill，没有写入用户全局技能目录，也没有公开发布。GitHub 的最终 owner/仓库、可见性、版本与发布授权应在正式上传前明确。旧私有测试仓库的成功 CI 对应其原快照，不等同于本版新增代码已通过远端 CI。

English: the local CLI App Server now supplies observed role, parent/child thread and model activity evidence. The verifier joins startup and completion records instead of trusting assistant claims or empty waits. Model evidence is client runtime selection, not independent backend identity. Runtime collection is opt-in and quota-consuming; offline verification makes no model calls. The repository is prepared as a self-contained skill but has not been installed globally or publicly published.
