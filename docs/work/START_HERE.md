> 2026-10-23 更新：当前版本 0.2.0a1；请先看 [本次验证报告](VALIDATION_REPORT.md)。以下保留原交接入口，历史测试数字不是当前验收结果。

# Codex Triad — Work 模式交接入口

> 推荐直接将整个 `codex-triad-work-handoff.zip` 上传至 ChatGPT Work，不要只上传 `.whl` 文件。

## 资料优先级

1. `handoff/01-WORK-TASK.md`：完整任务目标、任务分期与交付标准（主任务书）
2. `handoff/02-REQUIREMENTS-AND-DESIGN.md`：架构、功能/非功能要求、技术约束
3. `handoff/03-ACCEPTANCE-CHECKLIST.md`：逐项验收与真实运行证据格式
4. `handoff/04-CURRENT-STATUS-AND-RISKS.md`：已有成果、未验证事项和优先排查方向
5. `handoff/05-COPY-TO-WORK.txt`：适用于 Work 对话的一键粘贴指令
6. `codex-triad/`：当前 v0.1.0 Python 源码、测试和开源文档
7. `MANIFEST.sha256`：打包内容校验摘要

## 交接程序

在 ChatGPT 中切换到 **Work**，新建一个任务，上传 `codex-triad-work-handoff.zip`，粘贴 `05-COPY-TO-WORK.txt` 全部内容，并开始执行。若 Work 可继续使用当前聊天附件，也建议显式附上 ZIP 以保证源文件完整。

请 Work：先解压、审阅、运行原有测试，再编写任务计划并推进。不要把旧 ZIP 直接作为最终发布版本，不要误以为通过离线测试就已验证真实的 Codex 运行。除用户明确批准外，不公开仓库或推送。

## 推荐开工检查

```powershell
cd codex-triad
py -3 -m pip install -e .
py -3 -m unittest discover -s tests -v
py -3 -m codex_triad --help
```

离线跑通后，再使用一个临时 Git 仓库进行 `init --dry-run`、`init`、`doctor`、`smoke`、`uninstall --dry-run`、`uninstall`；不要直接在用户重要项目上做破坏性试验。

## 核心事实

- 项目：Codex Triad，社区开源工具，非 OpenAI 官方产品。
- 模型：主协调 `gpt-6.1-sol`，高级顾问 `gpt-6-astra`，并行工作者 `gpt-6-luna`。
- 技术形态：优先基于 Codex 原生项目级 `.codex/agents/*.toml`，不是绕过认证的中转站。
- v0.1.0 是 **preview**，26 项离线单元测试通过；真实 Windows Codex 多模型调度尚未验证。
- Work 必须在报告中分别标注静态配置、测试执行、真实运行证据和推断。
