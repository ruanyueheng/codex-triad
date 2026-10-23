# Codex Triad

[![CI](https://github.com/ruanyueheng/codex-triad/actions/workflows/ci.yml/badge.svg)](https://github.com/ruanyueheng/codex-triad/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**三权分工，模型自选，在 Codex 中完成协作开发。**

[English](README.md) · [安装](#安装) · [使用](#使用) · [完整指南](docs/GETTING_STARTED.md)

Codex Triad 将实现、探索和审查分成三种职责。你来选择模型，让工作者并行调查，由主协调器实现和测试，在关键节点请顾问审查。

## 安装

在你的项目目录运行：

```bash
npx skills add ruanyueheng/codex-triad --agent codex
```

通过 [skills CLI](https://github.com/vercel-labs/skills) 安装到 `.agents/skills/codex-triad/`。需要 Node.js 22.20+；内置配置工具使用 Python 3.11+ 和你的 Codex CLI。

## 使用

在项目中打开 Codex，先配置三权：

```text
$codex-triad
为当前项目配置 Triad，让我从客户端的模型列表中
分别选择主协调、工作者和顾问使用的模型。
```

每种职责都可以选择模型和推理强度，也可以让同一个模型承担多个职责。

配置后直接交给它任务：

```text
$codex-triad
修复 CSV 导入问题。让工作者分别检查导入逻辑和测试，
由主协调器修改代码、运行测试，再请顾问审查实际差异。
```

## 三权分工

| 职责 | 负责什么 | Codex 角色 |
|---|---|---|
| 主协调 | 规划、实现、测试与整合 | 主会话 |
| 工作者 | 代码探索、依赖研究与故障诊断 | `triad_explorer`、`triad_researcher`、`triad_triage` |
| 顾问 | 设计评审、重复失败诊断与重要改动审查 | `triad_architect` |

三种职责均可自由分配模型。Sol/Luna/Astra 是最初的预设组合。

## CLI

需要手动配置或检查时，可以直接使用安装后的工具：

```bash
python .agents/skills/codex-triad/scripts/triad.py init --project . --interactive
python .agents/skills/codex-triad/scripts/triad.py doctor --project . --json
```

提供 `init`、`doctor`、`smoke`、`uninstall`、`report` 五个命令。安装和卸载加 `--dry-run` 可先预览。源码安装、离线演练和更多示例见[完整指南](docs/GETTING_STARTED.md)。

## 测试

77 项单元/集成测试，Windows/Linux 与 Python 3.11–3.14 的 CI，独立 wheel/skill 安装检查，以及真实三模型 CLI 协作验证。复现命令和详细结果见[验证记录](docs/VALIDATION.md)。

## 文档

[模型选择](docs/MODEL_ASSIGNMENT.md) · [架构](docs/ARCHITECTURE.md) · [故障排查](docs/TROUBLESHOOTING.md) · [更新记录](CHANGELOG.md)

[参与贡献](CONTRIBUTING.md) · [反馈问题](https://github.com/ruanyueheng/codex-triad/issues/new/choose) · [安全报告](SECURITY.md)

MIT · Alpha 预览版 · 面向 Codex 的社区项目。
