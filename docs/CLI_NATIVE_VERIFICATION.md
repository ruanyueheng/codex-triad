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

## Skill 行为演练与隔离边界（2026-10-23）

另一次独立演练按本地路径加载本仓库 SKILL.md，修复可丢弃项目中的 CSV 导入、去重、分组统计与 CLI 错误处理。原始 13 项验收从 3 项通过变为全部通过；新增 7 项边界测试与父任务独立执行的 7 项检查也全部通过，其中包含 300 行数据校验。原始需求和验收测试的字节未变。

协调器通过桌面 collaboration 接口请求 gpt-6.1-sol/high，探索子任务请求 gpt-6-luna/medium，审查子任务请求 gpt-6-astra/high，均实际返回结果。探索子任务观察的是已修改源码，不能当作独立的基线缺陷诊断。审查发现 Windows stdout 重复转换 CSV 换行；父任务进一步发现文件读取会改变字段内部的 CRLF。两处修正后审查结论 APPROVE。该接口仅返回规范任务名及请求参数，没有提供可交叉核对的运行时模型元数据；这次演练不能替代上面的 App Server 线程/模型取证。

这次演练也暴露了隔离验收问题：全局 config.toml 的推理强度由测试前记录的 ultra 变为 high，用户确认没有手动切换。显式命令审计未发现写全局配置的命令，变化来源未定位，不能据此断言具体客户端或工具存在缺陷。只恢复该字段后，文件 SHA-256 与测试前完全一致。原始配置及私有运行日志未上传。

因此，“在独立项目中运行”不能证明客户端配置隔离。要求不改变全局配置时，后续真实测试应使用独立 CODEX_HOME 的子 CLI/App Server，并核对前后哈希；不要通过持久化范围尚不明确的桌面模型/推理参数覆盖来宣称满足隔离要求。这次功能修复成功，但不构成桌面配置隔离通过的证据，也没有证明比单模型更快、更省额度。

## Skill 与 GitHub

0.2.0a4 公开预览前，另从精简 skill ZIP 在独立目录实跑交互预览、选模安装、doctor、原生采集及卸载；两个 Luna 角色重叠执行，Astra 在其后审查，核验 PASS。使用独立子进程 CODEX_HOME；全局 config.toml 测试前后 SHA-256 一致，本次临时认证引用已移除。此结果只验证受控 CLI 路径，不解释或抵消此前桌面配置变化的未知根因。

仓库根目录即一个自包含 `codex-triad` skill：SKILL.md、scripts/、src/ 和按需文档保持同级。无须先全局 pip 安装。发布包提供以 codex-triad/ 为顶层的 skill ZIP；未来安装时选择整个 skill 根目录，不能只复制 SKILL.md。

正式仓库为 [ruanyueheng/codex-triad](https://github.com/ruanyueheng/codex-triad)，对应提交的 CI 状态以该仓库 Actions 为准。skill ZIP 只保留运行文件和所需参考，不包含研发历史；可解压到目标仓库 `.agents/skills/` 后调用。没有自动安装到全局技能目录。公开源码与创建 Release/PyPI 包是不同操作；后者仍需明确授权。

English: the local CLI App Server supplies observed role, parent/child thread and model activity evidence. The verifier joins startup and completion records instead of trusting assistant claims or empty waits. Model evidence is client runtime selection, not independent backend identity. Runtime collection is opt-in and quota-consuming; offline verification makes no model calls. The standalone skill contains the runtime and required references and can be installed in a target repository without changing global skill/configuration files.
