> 最新更新：独立 CLI 的角色/线程/运行时模型证据现已补齐，见 [CLI 原生验收](../CLI_NATIVE_VERIFICATION.md)。以下保留此前阶段记录。

> 后续真实验证更新：用户已授权独立环境测试；三次目标模型请求返回、私有远端 CI 与草稿附件验证通过。完整原生协作和后端模型身份仍未验收。详见 [隔离验证报告](ISOLATED_VALIDATION_REPORT.md)。下文是此前离线交付记录。

# 当前状态与风险（2026-10-23）

当前交付版本 **0.2.0a1**；原 v0.1.0 的 26 项测试是历史基线。本次以实际执行日志为准，见 [验证报告](VALIDATION_REPORT.md)、[审查清单](AUDIT_FINDINGS.md) 和 [修改清单](CHANGE_SUMMARY.md)。

已实现并本地测试：事务安装/卸载/中断恢复、进程锁、junction/硬链接与所有权保护、TOML 语义校验、结构化 UNKNOWN、CLI 集成、扩展离线评测。Windows 多版本与 WSL Linux 测试详情在验证报告。

真实 Codex worker/advisor 启动、实际模型/推理强度、账户访问、成本节省：**NOT_VERIFIED**。本机 CLI --version 输出 0.163.0；未据此推定支持三模型。未调用模型、未读取凭据或全局配置。未运行远端 GitHub Actions，未发布。

残余风险：本地恶意写者的路径竞态、多文件非同时可见、断电/磁盘故障、网络文件系统、Windows ACL 差异、旧清单无法还原原始空白。恢复备份可能含配置敏感内容；完成即删，未完成时离线保护，禁止上传。当前没有 .git 元数据，交付源码目录与包，不伪造提交记录。

发布前仍需真实模型烟测、远端 CI、名称/商标/包名检查、维护者联系方式和授权发布。下一阶段先验证正式事件和模型/线程归属，再考虑 opt-in 收集与门禁；不要抓取私有日志冒充稳定接口。

English: this is a locally tested 0.2.0a1 source preview. Actual model access/identity, runtime delegation, enforced gates, cost savings and remote CI/publication remain unverified. See the validation and audit reports for evidence and remaining risks.
