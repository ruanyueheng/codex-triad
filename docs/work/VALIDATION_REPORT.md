> 最新更新：独立 CLI 的角色/线程/运行时模型证据现已补齐，见 [CLI 原生验收](../CLI_NATIVE_VERIFICATION.md)。以下保留此前阶段记录。

> 后续真实验证更新：用户已授权独立环境测试；三次目标模型请求返回、私有远端 CI 与草稿附件验证通过。完整原生协作和后端模型身份仍未验收。详见 [隔离验证报告](ISOLATED_VALIDATION_REPORT.md)。下文是此前离线交付记录。

# Codex Triad 0.2.0a1 验证与交付报告

日期：2026-10-23（Asia/Shanghai）。交付是本地源码目录及安装包，不是远端 Release；目录原本没有 .git，未创建或伪造提交历史。

## 已实现

- 保留五个命令/旧参数；所有权保护、无副作用的差异预览、可恢复安装与卸载、OS 互斥、Windows junction/硬链接/普通文件检查。
- TOML 全语义校验；未知文件不能由 --force 认领；旧 schema-1 清单兼容；CRLF、UTF-8、空文件和原有配置保留。
- Windows 现有文件 DACL 保留，暂存/新文件写入前设置仅所有者访问；其他运行身份需要明确配置权限。
- doctor 的结构化 UNKNOWN、字段/功能开关检查；smoke 的额度提示和手工证据方案。
- 扩展离线评测、五类任务、正式角色契约、中英文档、ADR、风险与路线图。

## 本地测试通过

原始基线：Python 3.13.5，`PYTHONPATH=src python -m unittest discover -s tests -v`：26/26 通过。首次未安装包时导入失败；随后发现原许可证元数据不兼容 setuptools 72.1，修复后 editable 安装成功。

最终命令：`python -m unittest discover -s tests -q`。使用不同解释器时设置 PYTHONPATH=src；详细摘要在 [TEST_RESULTS.md](TEST_RESULTS.md)。

| 环境 | 结果 |
|---|---|
| Windows，CPython 3.11.15 | 64/64 通过，无跳过 |
| Windows，CPython 3.12.14 | 64/64 通过，无跳过 |
| Windows，CPython 3.13.5 | 64/64 通过，无跳过 |
| Windows，CPython 3.14.6 | 64/64 通过，无跳过 |
| WSL Ubuntu，CPython 3.12.3 | 62 通过，2 个 Windows 专项按平台跳过；共发现 64 项 |

覆盖实际子进程中断、故障注入、锁竞争、恢复时后续编辑保护、junction、symlink、hardlink、Windows DACL、长路径/中文/空格路径、错误 JSON/TOML/UTF-8、所有五个 CLI 命令，以及非有限/歧义 CSV 输入。它们是安装工具本地验证，不是模型运行验证。

构建检查：本机 setuptools 72.1.0；兼容许可证格式；无新增运行依赖。

```powershell
python -m pip install --no-index --no-deps --no-build-isolation -e .
python -m compileall -q src tests tools
python tools/build_release.py
python tools/check_wheel.py
```

已执行 editable 安装、wheel 构建和隔离 venv 安装：从源码目录之外验证包版本、模块/console 入口以及 init → doctor → uninstall。源码 ZIP 包含源码、测试、文档和 CI，排除缓存、.git、项目 .codex、恢复记录与环境文件；摘要见 dist/SHA256SUMS.txt。最终包核验结果追加在本报告末尾。

未额外引入 lint/type-check 工具；compileall 仅为语法检查，不能替代类型检查。CI 已配置 Windows/Linux × Python 3.11–3.14 和包安装检查；**远端 GitHub Actions 尚未执行**。

## 实际运行验证

本机命令 `codex --version` 输出 **codex-cli 0.163.0**。该信息不是桌面应用版本，也不证明加载项目配置、模型访问或多 Agent 成功。

以下均为 **NOT_VERIFIED / NOT_RUN**：主会话有效模型、Luna worker/Astra advisor 真实启动、模型与线程/推理强度绑定、账户/提供方权限、准确 token/cost、上下文收益及成功率改进。没有发起模型请求，也没有模拟子 Agent 成功。手工最小步骤见 [RUNTIME_VERIFICATION.md](../RUNTIME_VERIFICATION.md)，证据模板在 evaluation/runtime-evidence.template.json。

官方文档核对及 P2 结论见 [OFFICIAL_COMPATIBILITY.md](../OFFICIAL_COMPATIBILITY.md)：正式 hooks/SDK/API 已有可调查接口，但本版没有安装任何运行时门禁或日志采集器。

## 未完成与风险

1. 真正三模型烟测、脱敏截图和可核实的运行/费用数据，需要用户在真实客户端明确执行。
2. macOS、远端 CI、网络文件系统、断电/磁盘损坏、跨身份 ACL 尚未验证；WSL Linux 不等价于全部 Linux 部署环境。
3. 文件事务不是多文件同时可见，也不阻止同权限恶意进程竞争路径；恢复可能受磁盘/ACL 故障阻止。删除后恢复会使用私有新文件权限，不保证恢复完整元数据。
4. 恢复记录含配置字节，虽然本地文件权限受限，仍不是加密；正常完成删除，异常时离线保护。dry-run 可能显示目标文件中的编辑，分享前脱敏。
5. 发布名称/商标/包名、维护者联系方式、截图、远端 CI 仍须确认。未创建公开仓库、push、部署、提交或发布 Release。

下一阶段：先做真实客户端验收 → 冻结版本兼容矩阵 → 采集有来源的 A/B 样本 → 在隔离环境验证 hooks 的事件与模型/线程字段 → 才设计 opt-in、按实际 diff 绑定的审查门禁。详细 [ROADMAP](../ROADMAP.md)。

English: 0.2.0a1 is a locally tested source preview. The 64-test suite passed on four Windows Python versions; WSL Ubuntu passed 62 tests with two Windows-only skips. Source/wheel and clean-environment CLI checks are separate from model verification. Actual delegation/model identity/usage, remote CI and publication remain unverified. No credential reads, global Codex changes, paid model tests or remote publication were performed.

## 最终包核验

- `python tools/check_wheel.py`：退出码 0，输出 `Clean wheel installation and CLI lifecycle passed: 0.2.0a1`。
- 源码 ZIP：54 个文件，存储层源码和测试日志与工作目录逐字节一致；未包含缓存、私有 .codex、恢复记录或环境文件。
- 本地 Markdown 链接检查：无断链。常见凭据/私钥/带密码 URL 模式扫描：无命中；模式扫描不等于证明任何形式的敏感信息都不存在。
- `dist/LOCAL_CHANGES.patch`：基于修改前本地快照的文本差异，不是 Git 历史；报告记录 47 个新增/修改文件。
- 交付：`dist/codex-triad-0.2.0a1-source.zip`、`dist/codex_triad-0.2.0a1-py3-none-any.whl`；SHA256 在同目录 SHA256SUMS.txt。
