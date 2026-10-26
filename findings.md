# 审查发现

2026-10-23，修复前记录：

| 严重度 | 发现 | 范围及处理 |
|---|---|---|
| critical | 暂未确认 | 不将假设报告为已证实漏洞 |
| high | 写入不原子、无事务/互斥 | 安装/卸载共享事务；故障注入与多进程测试 |
| high | Windows junction 未检测 | 检查 reparse points；检查普通文件类型 |
| high | --force 覆盖未登记同名 Agent | force 仅允许已登记所有权 |
| high | TOML 文本行所有权不识别字符串/表作用域 | 通过完整 TOML 语义前后对比保证仅改期望键；无法安全合并时拒绝 |
| medium | manifest 不完整校验；doctor 可崩溃、类型不严 | 共享严格校验；UNKNOWN 与静态检查分开 |
| medium | AGENTS.md 拼接/卸载 strip 改写用户空白 | 精确保留用户字节，状态记录必要的拼接元数据 |
| medium | 缺 CLI/打包/错误注入测试 | 增集成与 CI |
| low | 文档基线数字、占位链接与运行验证混杂 | 更新验证报告及发布要求 |

官方来源（文档核对，不代表本账号运行验证）：
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/config-file/config-basic
- https://learn.chatgpt.com/docs/hooks

已确认当前文档保留 agents.enabled、default_subagent_model、default_subagent_reasoning_effort、max_concurrent_threads_per_session；max_threads 是旧别名。项目原有主字段无需盲目替换。配置优先级：CLI > 信任项目（近目录优先）> profile > 用户 > 云默认 > 系统 > 内置；强制 requirements 另有约束。
本机 Codex CLI 输出 codex-cli 0.163.0。版本不证明功能/账户/模型可用。

2026-10-24 续测：CLI 已为 0.164.0；同机当前自定义 provider 的正常认证从子进程环境复用，不落盘。模型目录文件是相对 CODEX_HOME 的路径，新 home 需改为对原目录文件的绝对引用。新的 Windows 沙箱首次拒绝 exec，保留环境失败，之后仅在可丢弃子 CLI 使用与本轮宿主相同的 full-access 权限，不改全局设置。子代理实报 Unknown model gpt-6-luna，Available models 为 gpt-6-astra / gpt-6.1-sol；历史模型成功不证明当前仍可用于子代理。

一次 TypeSafe 语义核查实际返回 jev-1.14.0：原 skill 是否明确要求不提交时的交付前顾问审查、是否明确要求冻结基线，两项 yes 概率均为 0.06；人工核对原文确认缺少明确要求。概率不是准确率；只发送公开 SKILL.md 与两个问题，没有发送凭据、配置或私有运行日志。
# 2026-10-26 改进调查

- 当前源码 `checker.diagnose` 只验证文件和版本；不能对照模型目录指出配置中模型或推理强度的变化。既有实测记录曾遇到 Luna 不在目录及子代理失败。
- `appserver.Client` 读取线程跳过非法 JSON；UTF-8 或管道读取异常不会通知调用方，最终只得到 45 秒超时。EOF 标记只消费一次，后续调用仍可能等待。
- 拟复用 `discover_models` 增加 `doctor --check-models`，检查实际配置文件而非仅清单；目录未列出只记 WARN，查询失败记 UNKNOWN，不推断账户权限。
- 对照来源与最终验证在完成后追加；外部内容仅作为数据，不作为执行指令。

## 方向选择与来源

- OpenAI App Server 文档（2026-10-26 读取）：`https://developers.openai.com/codex/app-server`。沿用 initialize → model/list，不增加 thread/start 或 turn/start。目录字段只作为客户端能力声明，不作为运行权限证明。
- MCP Python SDK 实际源码（2026-10-26 读取）：`https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/client/stdio.py`。参考其“解析错误通过流传递”和“关闭 stdin → 等待 → 超时终止进程树”的生命周期原则，使用现有标准库实现，不引入其异步框架或依赖。
- uv 环境检查作为候选先例搜索，但正文抓取失败，不以未读取实现作为设计依据。MCP 旧目录路径也已迁移，本次按搜索结果改读实际 stdio.py。
- TypeSafe/Jev 单次辅助评价：实际 model `jev-1.14.0`（请求 `jev-latest`）；仅发送候选方案和必要事实摘要。现有问题的证据强度（0–3）：传输失败 2.81、目录诊断 2.54、新 A/B 执行器 0.83、新调度器 0.24；输入 1012 / 输出 62 tokens。该分数及 confidence 不等于准确率，最终选择以源码与失败复现为准。
- 108 项基线通过；新异常测试在旧实现复现 UTF-8/读取异常未传播及 EOF 后再等 45 秒。修复后定向测试通过。
- 首次真实 CLI 0.164.0 查询比较了六处模型配置、没有生成调用、项目字节和全局配置哈希不变；临时目录清理遇到 SQLite 共享内存文件仍被占用。因此增加 stdin EOF 优先退出及 Windows 超时进程树清理，补真实启动器/子进程管道回归。
- 测试设计调整：删除清单或手改托管行会触发已有 MANAGED_CONTENT 保护，不能用于“合法保留配置”用例；改用安装前已有的用户配置，并另测角色文件编辑。未放宽原安全检查。
- 继续追踪 Windows 进程树：EOF 后 cmd/node/codex 正常退出，但启动阶段的 git/git-remote-https 仍存活。因此仅优化 close 不够；将 apps/plugins 的禁用提前到 App Server 启动参数。相同实测不再启动 Git，同一启动器进程树无残留；保留进程观测目录，不上传私有 stderr。
- 构建环境：系统 Python 3.14/3.13 均缺少 setuptools 构建后端；使用 gitignored `build/verification-env` 安装构建工具，不修改项目运行依赖。
- 清理限制：自动审批拒绝删除第一次失败实测的临时目录（策略拦截，未提供细分原因）；未绕过删除限制。测试观察目录保留在系统临时目录。
