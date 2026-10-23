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
