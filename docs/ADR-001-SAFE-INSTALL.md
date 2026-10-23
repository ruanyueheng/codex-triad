# ADR-001：安全的项目级写入 / Safe project-local writes

日期：2026-10-23。状态：已采用；适用版本 0.2.0a1。

## 决策与原因

`installer.py` 负责生成、所有权与改动计划，`storage.py` 集中处理路径校验、进程锁、原子替换、事务和恢复；`checker.py` 复用相同路径与清单校验。没有新增运行依赖或通用框架。

- 每次实际安装/卸载持有 OS 文件锁；异常退出由系统释放。保留 `.codex/.triad.lock`，不能在持锁时删除再重建锁文件。dry-run 不创建目录或锁，只提供当时的预览。
- 拒绝目标及目录链中的 symlink、Windows reparse point/junction，拒绝硬链接和非普通目标文件。项目根以用户选择的规范路径为边界。
- 先在内存规划全部改动并验证 TOML，再记录读入字节快照。写前复查文件未被其他编辑器修改；每个文件通过同目录临时文件、flush/fsync 和 replace 更新。
- 写前保存 `.codex/.triad-transaction.json`，包含受管理路径的 before/after 字节（base64）。这是本地恢复备份，**不是加密**，可能包含目标配置中的敏感值；正常成功或回滚后删除，禁止提交/上传。POSIX 临时文件默认私有；Windows 在写入前将暂存文件 DACL 设为仅所有者访问；替换已有文件使用 ReplaceFileW 保留其 DACL。新生成文件仅所有者可读写，其他运行身份须显式配置访问权限。
- 可捕获的写入错误触发回滚；进程被终止时保留恢复记录并拒绝新变更。`init --recover` 或 `uninstall --recover` 仅恢复，不继续安装/卸载。恢复先验证全部路径与内容；出现后续编辑就拒绝覆盖并保留备份。
- 状态清单保留 schema 1 兼容性，增加空文件存在性、拼接空白、原配置哈希等元数据，不存完整配置副本。旧清单没有字节恢复元数据时保守保留空白。
- `--force` 仅覆盖清单内已有所有权的 Agent 文件/策略块；未知文件始终冲突。改过的配置行仍需人工处理。
- 不引入 TOML 写库。逐项删除受管理行时，验证完整解析结果只少了对应作用域的键；合并后的完整语义必须与预期相同。遇到多行字符串假表头等无法证明安全的布局，拒绝修改。

## 影响、验证和限制

故障注入、多进程锁、真实子进程中断、后续编辑保护、junction、硬链接、UTF-8/CRLF、空文件往返均有测试。恢复报告不显示备份内容。

此事务不提供多文件同时可见性，不声称抵抗本地恶意进程在路径检查和文件打开间的竞态；锁仅协调 Triad。断电、磁盘/ACL 故障可能阻止恢复，临时目录/锁文件可能留下；检查日志并离线保护备份。网络文件系统锁语义、磁盘断电持久性尚未实测。不自动删除用户目录。

## English

Separate generation/ownership planning from a small shared storage module. Hold a process lock, validate ordinary project-local paths, compare snapshots, persist a local before/after journal, and replace files atomically. Roll back caught failures; require explicit recovery after process termination. Refuse recovery over later edits. Preserve schema-1 compatibility and keep unknown files outside `--force` scope. Validate complete TOML semantics around every managed edit rather than trusting matching text. No additional runtime dependency.

The journal is sensitive local backup data, not encrypted telemetry. This is recoverable multi-file writing, not simultaneous multi-file visibility, a hostile-writer sandbox, or a power-loss guarantee.

Windows 权限语义来源：[Microsoft ReplaceFileW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew)。专项测试使用受保护的自定义 DACL，验证替换保留访问控制；暂存备份写入前配置仅所有者访问。删除后再恢复的文件会使用私有新文件权限，不声称复原所有 ACL、ADS 或文件时间。
