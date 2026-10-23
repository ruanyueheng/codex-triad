# Codex Triad

[![CI](https://github.com/ruanyueheng/codex-triad/actions/workflows/ci.yml/badge.svg)](https://github.com/ruanyueheng/codex-triad/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**在 Codex 中，为协调、探索和审查分别选择模型。**

[English](README.md) · [上手指南](docs/GETTING_STARTED.md) · [验证结果](docs/VALIDATION.md) · [故障排查](docs/TROUBLESHOOTING.md)

Codex Triad 是面向 Codex 原生子 Agent 的项目级 CLI 和 Agent Skill。你可以为三种职责分别选择模型与推理强度，预览配置变化，并保留已有设置。同一个模型可以承担多个职责。

**Alpha 预览版 · 社区项目，非 OpenAI 官方项目。** 审查检查点是指令约定，不是强制 hook。模型可用性取决于你的客户端和账户。

## 工作方式

| 职责 | 工作 | 原生角色 |
|---|---|---|
| 主协调 | 负责实现、测试和最终结果 | 主会话 |
| 工作者 | 调查有边界、彼此独立的问题 | `triad_explorer`、`triad_researcher`、`triad_triage` |
| 顾问 | 审查重大决策、重复失败和非琐碎提交 | `triad_architect` |

```text
任务 → 主协调 → 有限范围的工作者 → 实现与测试
             → 在相关检查点调用顾问 → 结果与证据
```

Sol/Luna/Astra 只是兼容旧版的预设。所有职责都能重新分配；工具不代理模型请求，也不静默替换不可用模型。

## 快速上手

需要 Python 3.11+。交互选择还需要已安装、已登录且支持 App Server `model/list` 的 Codex CLI。已实测客户端为 Windows CLI 0.163.0；其他环境见[兼容性与证据](docs/VALIDATION.md)。

克隆仓库，直接运行内置 CLI，无需安装 Python 包：

```bash
git clone https://github.com/ruanyueheng/codex-triad.git
cd codex-triad
python scripts/triad.py --help
```

在此目录创建一个可丢弃的目标项目，先选模型并预览，再安装：

```bash
mkdir ../triad-demo
python scripts/triad.py init --project ../triad-demo --interactive --dry-run
python scripts/triad.py init --project ../triad-demo --interactive
python scripts/triad.py doctor --project ../triad-demo --json
```

Windows 可将 `python` 换成 `py -3`；macOS/Linux 按需使用 `python3`。预览不保存选择，第二条命令会重新询问。目录查询可能访问配置的服务，但不会发起生成 turn；出现在列表中不等于该账户已实测调用成功。

然后检查生成文件，在 Codex 中打开**目标项目**，审阅后再信任并新建会话。给协调器一项确实需要探索和审查的任务，观察实际子 Agent 活动；安装完成不代表已经启动 Agent。

暂时没有 CLI 或网络？先走[离线演练](docs/GETTING_STARTED.md#offline-walkthrough)。也可以选择[虚拟环境安装](docs/GETTING_STARTED.md#optional-python-package-installation)，使用 `python -m codex_triad` 的五个命令。本项目尚未发布到 PyPI。

## 作为 skill 使用

仓库根目录包含 `SKILL.md` 和配套运行文件。仅克隆到任意目录，不等于已经注册到 Codex 技能列表。

把构建得到的 `codex-triad-<version>-skill.zip` 解压到目标仓库的 `.agents/skills/`，保留 `.agents/skills/codex-triad/SKILL.md`、`scripts/`、`src/`、`docs/` 和 `evaluation/`。然后调用：

```text
$codex-triad
检查本项目的模型分配，然后修复失败测试。
在有帮助时使用有限范围的工作者，保留单一代码实现负责人，
并让已配置的顾问审查真实差异和测试结果。
```

也可直接要求 Codex 读取克隆仓库中 `SKILL.md` 的绝对路径。参见[技能安装、案例与移除](docs/GETTING_STARTED.md#use-the-skill)。本地技能发现机制依据 [Codex 官方文档](https://learn.chatgpt.com/docs/build-skills)。

## 会修改什么

Triad 维护 `AGENTS.md` 标记块、`.codex/config.toml` 中登记的新增内容、四份角色 TOML 和所有权清单。已有设置会保留；未知同名文件会触发拒绝。用 `doctor` 检查冲突，`--force` 不能覆盖无关配置。

```bash
python scripts/triad.py uninstall --project ../triad-demo --dry-run
python scripts/triad.py uninstall --project ../triad-demo
```

卸载保留用户修改过的文件，并报告部分卸载；可能留下空目录和锁文件。中断写入需显式恢复，详见[安全存储设计](docs/ADR-001-SAFE-INSTALL.md)。

## 已验证的能力

- 单元和集成测试覆盖配置合并、原文保留、回滚、并发、模型选择及运行证据的反例。
- CI 覆盖 Windows/Linux、Python 3.11–3.14，构建发行包，并验证干净 wheel 和独立 skill。
- 独立 CLI App Server 实测取得角色、父子线程、模型活动与执行顺序证据。另一次修复案例通过 20 项项目测试和 7 项独立检查。
- 这些结果不能证明后端独立模型身份、所有账户权限、强制审查或费用下降。[验证报告](docs/VALIDATION.md) 保留了尚未定位来源的桌面配置持久化现象。

对仓库内的真实脱敏证据进行离线核验：

```bash
python scripts/triad.py report --runtime-evidence evaluation/cli-runtime-20261023.json --json
```

`doctor` 检查静态配置，`smoke` 打印提示词，两者都不证明模型调用成功。真实采集需要主动启用，会消耗额度；要求隔离时使用单独配置的 `CODEX_HOME`。参见[原生运行验收](docs/CLI_NATIVE_VERIFICATION.md)。

## 文档与贡献

[模型分配](docs/MODEL_ASSIGNMENT.md) · [架构](docs/ARCHITECTURE.md) · [评测](docs/EVALUATION.md) · [路线图](docs/ROADMAP.md) · [变更记录](CHANGELOG.md)

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python tools/build_release.py
python tools/check_wheel.py
```

运行时只依赖 Python 标准库，构建需要 setuptools 和 wheel。环境与产物检查见[贡献指南](CONTRIBUTING.md)。本机构建文件位于 `dist/`，成功的 CI 运行也会保留预览产物。

通过 [Issues](https://github.com/ruanyueheng/codex-triad/issues/new/choose) 报告问题；涉及敏感信息时按[安全策略](SECURITY.md) 私下报告，不要上传完整日志。欢迎改进可复现性与兼容性。

[MIT 许可证](LICENSE)。文档组织参考 [uv](https://github.com/astral-sh/uv)、[ripgrep](https://github.com/BurntSushi/ripgrep) 和 [Anthropic Skills](https://github.com/anthropics/skills)，不代表获得这些项目的认可或背书。
