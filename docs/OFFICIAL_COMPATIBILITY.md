# 官方配置核对与 P2 可行性 / Official compatibility and P2 assessment

核对日期：2026-10-23。本机版本输出：`codex-cli 0.163.0`。以下是官方文档核对，不代表此客户端、账户或中转服务已经成功执行。

## 配置核对

| 项目 | 核对与本项目处理 |
|---|---|
| 自定义文件 | `.codex/agents/*.toml`；必填 name、description、developer_instructions；继续使用独立文件 |
| 模型/推理强度 | 文件可配置 model 与 model_reasoning_effort；保留用户指定模型与旧默认值；ultra 仅通过参数选用，支持情况仍待账号实测 |
| 并发 | max_concurrent_threads_per_session 不含主线程；max_threads 为旧别名，保留已有值，不同时自动写新别名 |
| 默认 Agent 设置 | enabled、default_subagent_model、default_subagent_reasoning_effort 仍有文档支持，无需误迁移为其他 API 的同名概念 |
| 权限 | provider、MCP、沙箱/审批继承父会话；只读角色指令不创建独立沙箱 |

来源：[Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)。

配置优先级由高到低：CLI 覆盖 → 信任项目配置（更近目录优先）→ 选定 profile → 用户 → 云默认 → 系统 → 内置。强制 requirements 是额外约束。`doctor` 仅读取目标项目，不读取全局配置、信任库或凭据，因此有效值与信任状态记 UNKNOWN。[Config basics](https://learn.chatgpt.com/docs/config-file/config-basic)

模型解析先取显式 spawn 参数，再取 agents 默认值，再继承父会话；自定义 Agent 文件显式设置的 model/effort 随后优先。新选模型但未指定 effort 时还涉及该模型默认 effort。Triad 文件同时写明两者以减少歧义；这仍是配置意图。[Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)

## P2：存在正式接口，但尚未集成

| 接口 | 文档支持 | 结论 |
|---|---|---|
| Hooks | PreToolUse 可拒绝支持的工具调用；有 SubagentStart/Stop 事件和 model 字段 | 可做 opt-in 原型；hook 需要信任，部分路径不覆盖，不能保证拦截所有 Git/外部操作 |
| Codex SDK | 可编排 Codex 流程 | 不由 SDK 名称推断能取得桌面所有子线程身份或费用 |
| Agents API | 有子 Agent 事件及 usage/可观察接口 | 是独立 API 执行面，不能当作已存在桌面会话的完整遥测或订阅账单 |

来源：[Hooks](https://learn.chatgpt.com/docs/hooks)、[Codex SDK](https://learn.chatgpt.com/docs/codex-sdk)、[Agents multi-agent](https://developers.openai.com/api/docs/guides/agents-api/multi-agent)、[Observability and usage](https://developers.openai.com/api/docs/guides/agents-api/observability)。

不安装 hook、不读取 transcript、不抓取私有日志、不调用 API。下一步应先在隔离环境验证：事件顺序、真实 model/thread 绑定、失败行为、覆盖路径、费用来源与最小数据字段。届时再设计按 diff 哈希绑定的审查结果；失败计数需可信测试结果，不能仅靠 Agent 文本。日志抓取不作为正式接口的替代。

## English

Current official documentation supports the existing standalone agent schema and project-level agent settings. Preserve requested model IDs and legacy concurrency aliases; do not infer account access from documentation. Agent-file model/effort values take precedence after spawn/default/parent resolution. Parent permissions still apply.

Hooks, the Codex SDK and Agents API provide possible integration surfaces, but this release installs none of them. Hook coverage is incomplete and the APIs do not automatically expose existing desktop sessions or subscription charges. Effective model identity, thread attribution, hook behavior and usage remain NOT_VERIFIED until an explicit runtime experiment.
