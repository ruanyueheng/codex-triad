> 2026-10-23 更新：当前版本 0.2.0a1；请先看 [本次验证报告](docs/work/VALIDATION_REPORT.md)。以下保留原交接入口，历史测试数字不是当前验收结果。

# 交给 ChatGPT Work / Codex 使用

你当前位于 **Codex Triad** 的完整源代码仓库。

## 使用方法

1. 在 Work 中打开本项目文件夹（或上传整个项目 ZIP）。
2. 把项目根目录的 `WORK_PROMPT.txt` 全文复制到 Work 对话框。
3. 任务上下文在根目录 `WORK_HANDOFF.md`；其余详细需求和验收材料在 `docs/work/`。
4. 如果你只想给**已有仓库**增加交接文档，使用“Docs-Only” ZIP，覆盖前请对比同名文件。

## 本地基线测试

Windows PowerShell：

```powershell
py -3 -m pip install -e .
py -3 -m unittest discover -s tests -v
py -3 -m codex_triad --help
```

此仓库为预览基线。离线测试通过≠真实 Codex 三模型调度已经被验证。请根据 Work 环境中的工具和官方文档重新确认运行时行为。
