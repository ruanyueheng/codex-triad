# 最小运行验收 / Minimal runtime verification

以下命令前三类只做本地配置/诊断或打印提示词。**把提示词交给 Codex 执行才会调用模型并可能消耗额度。** 本次研发未执行该步骤。

```powershell
$triadProject = Join-Path $env:TEMP ("triad-smoke-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $triadProject | Out-Null
py -3 -m codex_triad init --project $triadProject --dry-run
py -3 -m codex_triad init --project $triadProject
py -3 -m codex_triad doctor --project $triadProject --json
codex --version
py -3 -m codex_triad smoke --phase workers
py -3 -m codex_triad smoke --phase advisor
```

1. 在 Codex 中打开 `$triadProject`，审阅并信任项目，新建会话。主模型应由 UI/可信运行信息确认，不能据项目文件推定。
2. 手工执行 workers 提示词，观察 triad_explorer 与 triad_researcher 两个实际线程；记录名称、线程 ID、开始/完成/失败。并发上限 3 不含主线程。
3. 手工执行 advisor 提示词，观察 triad_architect；只读策略仍继承父会话权限。
4. 复制 `evaluation/runtime-evidence.template.json` 到私有目录填写。model/effort 无可信来源则写 MODEL_NOT_VERIFIED/UNKNOWN。Agent 自述不是来源；线程成功和模型确认是两个事实。
5. 若失败，保留原始错误并记录 outcome=FAILED；回退为主线程处理要明确说明。不要替换 provider 或放宽权限来制造通过结果。
6. 脱敏后才分享客户端版本、必要 thread/model 字段或截图；不提交原始日志、备份和登录信息。当前没有自动证据采集器。

```powershell
py -3 -m codex_triad uninstall --project $triadProject --dry-run
py -3 -m codex_triad uninstall --project $triadProject
```

English: create a disposable project, preview/install/diagnose, then explicitly run the printed prompts in a trusted new Codex session. Observe two workers and one advisor, separately record thread outcomes and effective models, preserve UNKNOWN when identity is unavailable, and keep evidence private/redacted. No automatic paid test is included.
