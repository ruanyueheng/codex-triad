> 2026-10-23 更新。当前证据见 [验证报告](VALIDATION_REPORT.md)；保留未做的真实调用/发布验证为空。

# Work 任务验收清单

## A. 离线可交付

- [x] 源码包解压后没有构建缓存、密钥文件、私有数据和错误的打包路径
- [x] Python 3.11 / 3.12 / 3.13（可获得时）跨平台单元测试通过，输出实际命令和结果
- [x] `pip install -e .` / `pip wheel .` / `python -m codex_triad --help` 运行成功
- [x] `init --dry-run` 不修改目标目录
- [x] 首次安装、重复安装、升级不同模型、用户自定义冲突、受保护编辑、卸载均有测试
- [x] 符号链接、路径遍历、文件权限、无效 TOML、Windows 长路径/编码/原子更新风险已测试或明确记录限制
- [x] `doctor --json` 在未知状态正确输出 UNKNOWN/WARN，而不是错误标记真实模型可用
- [x] 默认无第三方出站请求、不访问令牌/登录凭据
- [x] 文档、例子、CI 配置与代码一致；README 中文/英文并存

## B. Codex 实际运行证据（若环境允许）

- [ ] 记录 Codex CLI/桌面版本、运行系统、日期、登录方式类型（不记录凭据）
- [ ] 记录主模型有效选择方式（不是根据配置文件猜测）
- [ ] 能观察真实 `triad_explorer`、`triad_researcher` 子线程或给出原始失败信息
- [ ] 能观察真实 `triad_architect` 线程或给出原始失败信息
- [ ] 记录真实的模型 ID/推理强度（若运行时未暴露则 `MODEL_NOT_VERIFIED`）
- [ ] 不触发 Git push、部署或未经批准的费用性操作
- [ ] 在版本/账户不支持时能不误导地解释原因和回退路径

## C. 能力边界和对比实验

- [x] Prompt-only Advisor 调度明确标注“非强制”
- [x] 不把子 Agent 的提示词只读承诺冒充沙箱保护
- [x] 统计模型调用只能基于真实记录；无来源的不估算成本收益
- [ ] 单 Agent baseline 与 Triad 实验采用相同任务/环境，原始记录与汇总一致
- [ ] 报告成功率、耗时、质量、成本可用字段和样本数，不做无样本量结论

## D. GitHub 发布前检查

- [ ] GitHub Actions Windows/Linux 成功（如果实际连接 GitHub）
- [x] MIT License、SECURITY、CONTRIBUTING、CODE_OF_CONDUCT、CHANGELOG、release notes 齐全
- [x] 脱敏检查包含 `.env`、凭据、token、代理 URL 中敏感参数、隐私日志
- [ ] 仓库名和项目名称的第三方冲突已检查
- [x] v0.x 发布文案只写经过证实的能力
- [x] 公开仓库、push、release 均在用户**明确批准后**进行

## 运行验证记录格式（每个场景一份）

```yaml
case_id: WORKERS-001
platform: Windows 11
codex_client: desktop | cli
codex_version: UNKNOWN
account_provider: masked
main_model_effective: MODEL_NOT_VERIFIED
subagents_requested: [triad_explorer, triad_researcher]
subagents_observed: []
models_effective: MODEL_NOT_VERIFIED
outcome: NOT_RUN
observed_error: NONE
raw_evidence_location: NONE
secrets_removed: true
notes: ""
```

验证证据不足时保留 `NOT_RUN` / `MODEL_NOT_VERIFIED`，不要为了填满表格编造结果。
