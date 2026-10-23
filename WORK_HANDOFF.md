> 本次研发已按此任务书推进至 0.2.0a1 本地交付；状态与未验证项见 [验证报告](docs/work/VALIDATION_REPORT.md)。以下保留原任务书与历史基线。

# Codex Triad — Work 研发总任务书

> 本文件放在 **Codex Triad 项目根目录**，供 ChatGPT Work 或 Codex 开始继续开发时直接阅读。
> 交付基线：v0.1.0 Preview；不代表已经在用户 Windows 客户端验证真实三模型调用。

## 入口与执行顺序

1. 先读本文件与 `README.zh-CN.md`，再阅读 `docs/ARCHITECTURE.md` 和 `docs/work/REQUIREMENTS_AND_DESIGN.md`。
2. 接着读 `docs/work/ACCEPTANCE_CHECKLIST.md`、`docs/work/CURRENT_STATUS_AND_RISKS.md`。
3. 检查 `src/codex_triad/` 和 `tests/` 的真实实现，并运行全部单元测试。
4. 以检查结果为准，修正不准确的旧文档、配置与假设。**不要因为任务书中写了能力就当成已经验证。**
5. 未经用户明确批准，不要创建公开仓库、push、部署或发 Release。

## 当前必须如实标记的边界

- `gpt-6-astra`、`gpt-6.1-sol`、`gpt-6-luna` 是用户指定的目标模型；具体服务商、客户端及账号的可用性应现场检查，不能根据字符串推断已启用。
- `AGENTS.md` 风险升级规则是指令驱动的建议，不是强制执行的运行时 hook。
- `doctor` 只做本地/静态检查，不能证明 API 调用、模型身份或成本节省。
- 下述任务书是**待办与验收要求**，不是已完成工作的承诺。

---

# Codex Triad — Work 模式完整研发任务书

**项目名**：Codex Triad  
**产品定位**：可复现、可诊断、可维护的 Codex 原生三级多 Agent 协作配置工具  
**当前基线**：v0.1.0 preview（位于 `codex-triad/`）  
**目标平台**：Windows Codex 桌面客户端为优先环境，同时兼顾 Codex CLI 与 macOS/Linux。  
**目标用户**：需要多模型协作、控制长上下文噪声并按风险升级审查的软件开发者。  
**输出语言**：文档中英文双语（中文优先），代码中的接口、测试名和变量名用英文。

## 1. 总目标

在现有 v0.1.0 项目基础上，交付一个经安全审查、真实测试与可复现验证、适合发布 GitHub 预览版本的开源项目。不要仅做 README 美化；优先提高安装器的正确性、Codex 子 Agent 的真实可用性和工程可信度。

模型分工：

| 层级 | 模型 ID | 职责 | 工作方式 |
|---|---|---|---|
| 首席顾问 | `gpt-6-astra` | 架构/安全评审、同类故障连续失败、非琐碎提交前审核 | 仅在关键节点升级调用 |
| 主协调器 | `gpt-6.1-sol` | 需求拆解、代码实现、测试和结果集成 | 主会话负责整合 |
| 探索/研究/诊断 | `gpt-6-luna` | 代码检索、文档验证、日志归因 | 并行、任务范围有限、短证据报告 |

**不得承诺**三模型一定同时可用、总成本一定下降、提示词能强制执行审查门禁；上述事实都必须经真实用户客户端和授权环境验证。

## 2. 必须首先完成的审查（P0）

1. 解压完整交接包，阅读现有 README、`docs/ARCHITECTURE.md`、`src/`、测试。
2. 使用当前官方 Codex 文档验证 `.codex/agents/*.toml` 字段、配置优先级、权限继承、线程并发限制、实际模型选择逻辑；指出代码与文档的差异。
3. 在本地运行基线测试并记录 Python 版本、命令、测试结果；确认打包安装是否正常。
4. 安全审计安装器：路径穿越、符号链接、TOML 错误、重复安装、配置合并、修改保护、备份/回滚、卸载范围、并发运行造成的数据竞争、Windows 文件系统差异。
5. 先提交一份分级问题清单（critical/high/medium/low），再修复 P0/P1 问题，并为每个修复补回归测试。

## 3. 产品增强任务（P1）

### 3.1 CLI 与配置管理

- 保留现有 `init`, `doctor`, `smoke`, `uninstall`, `report` 五个命令，保持旧参数兼容；若必须破坏兼容，明确升级方式。
- `init`: 预览差异、不覆盖未知用户配置、幂等、拒绝误删/覆盖用户改过的 Agent 文件、冲突有可理解的错误消息。
- `doctor`: 增加配置路径、字段语义/优先级、Codex 版本的能力检测（检测不到必须写 unknown）；`--json` 适合自动化；不得将静态检查冒充运行成功。
- `smoke`: 提供 worker 与 advisor 真实启动测试说明；尽可能收集可核实的模型/Agent/线程证据，无法通过 SDK/UI 确认则明确 `MODEL_NOT_VERIFIED`。
- `uninstall`: 增加干运行与恢复报告；不删除非 Triad 管理的数据和配置。
- 默认**不发起 API 调用、不读写密钥、不向外上传日志**；运行时检测属于可选、明确告知可能消耗额度的独立步骤。

### 3.2 可靠三层工作流

- 正式明确 Explorer、Researcher、Triage、Architect 的输入输出格式，减少主上下文噪音。
- 在文档和规则中规定风险触发：架构/安全/数据迁移决策前；相同失败签名两次无改进；非琐碎 Git commit 前。
- 明确每一步是 **advisory/prompt-based** 还是 **enforced/runtime-based**。
- 默认只让 Sol 修改源码；Luna/Astra 执行只读角色任务（注意这只是行为指令，不等于独立沙箱）。
- 如果模型不可访问、子 Agent 启动失败、CLI 版本不兼容，要报原始错误并清晰回退，不得伪装执行。

### 3.3 评估体系

- 增强 `evaluation`：同一任务单模型对照 VS 三层协作，记成功率、修复质量、耗时、主线程上下文占用、子线程数量、实际 token / cost（仅在数据源真实支持时）。
- 评测至少覆盖：仓库入口追踪、依赖版本兼容性、重复故障诊断、跨模块修复、提交前风险审查。
- 每次实验记录 Codex 客户端版本、模型实际 ID、任务快照、提示词版本、样本量与失败原因。
- 不用离线汇总冒充真实的 Codex telemetry；缺失数据记 `UNKNOWN`，不能估算后声称实测。

## 4. 可选高级功能（P2，需要先评估可行性）

- 确认可用的正式事件 hook / Agents API / Codex SDK 能力后，才设计确定性 Astra 审查门禁、重复失败签名计数器、Git 提交保护；没有官方支持不要做脆弱的日志抓取冒充可靠拦截。
- 在不上传敏感内容的前提下设计 opt-in trace/metrics collector，并向用户展示会收集哪些信息。
- 支持用户可配置模型组合、Agent 模板和回退规则，但第一版不实现跨 provider 自由混用的虚假能力。
- 当真实工程需求充分时考虑图形界面，不以仪表盘优先于核心运行可靠性。

## 5. 开源工程化与 GitHub 发布准备（P1）

- 中英文 README：项目定位、真实能力、限制、Windows 一键上手、示例、截图、常见错误、FAQ。
- MIT LICENSE、SECURITY.md、CONTRIBUTING.md、CODE_OF_CONDUCT.md、CHANGELOG.md、Issue/PR 模板。
- GitHub Actions 至少测试 Windows 与 Linux、Python 3.11+；增加包安装测试、lint/type check（只有当维护成本合理时）。
- 发布版本/仓库名/Logo 需确认与开源项目不冲突；检查敏感信息和第三方版权。
- 准备 `v0.1.0-alpha` 或更高预览版 release notes，说明哪些能力 **NOT VERIFIED**。
- 未经用户明确确认，**不要创建公开仓库、push、发布 GitHub Release 或暴露私有文件**。

## 6. 交付产物

至少交付：

1. 修复和增强后的完整、可安装的 Git 仓库文件（原始目录结构保留）。
2. 全部单元测试与集成测试结果；如有真实 Codex 运行，附脱敏后的版本/运行证据。
3. 设计决策记录（ADR）、风险清单、修改日志、剩余问题清单。
4. 完整中英文开发者/用户文档、GitHub 发布检查单。
5. 可用于下载或推送的源代码 ZIP、可安装 wheel（如果仍使用 Python 包装）。
6. 清晰的状态报告：已实现、已通过本地测试、真实运行验证、未完成，各自分开。

## 7. 实施顺序与工作方式

- **阶段 A：审查基线** → 列出问题、重跑 26 项测试、检查官方文档。
- **阶段 B：修复与增强** → 优先安全和兼容性，再改善命令行与配置。
- **阶段 C：验证与量化** → 新增回归测试、在可用环境做真实 Codex smoke test。
- **阶段 D：开源交付** → README/CI/发布包/Release notes 完善，等待用户确认发布。

除存在必须获取的 API 权限或仓库所有权外，按合理默认决策执行，不要因为细枝末节反复提问。若缺少真实 Windows/Codex 客户端访问，尽可能完成离线工作，并列出用户只需执行的最小验证步骤。

## 8. 基础引用（实施时重新核对最新版本）

- Codex subagents: https://learn.chatgpt.com/docs/agent-configuration/subagents
- Codex 配置: https://learn.chatgpt.com/docs/config-file/config-reference
- Codex 基础配置: https://learn.chatgpt.com/docs/config-file/config-basic
- 模型目录: https://developers.openai.com/api/docs/models
- Python Packaging: https://packaging.python.org/
