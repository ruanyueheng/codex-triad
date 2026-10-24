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
