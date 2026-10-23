# 源码审查分级清单 / Audit findings

日期：2026-10-23。先审查原始 0.1.0 源码并记录在根目录 findings.md，随后实施修复。等级使用 critical/high/medium/low；没有把假设当已证实问题。

| ID | 严重度/优先级 | 代码证据与影响 | 处理与回归 |
|---|---|---|---|
| A01 | high/P0 | installer.install/uninstall 逐文件 write_text/unlink，无事务；中途异常留下不一致状态 | storage.apply_changes 原子替换、恢复记录、回滚；安装/升级/卸载故障注入及真实进程中断测试 |
| A02 | high/P0 | _assert_safe_paths 仅 is_symlink，不覆盖 Windows junction，也不排除硬链接/目录目标 | 统一 lstat/reparse/普通文件检查；真实 Windows junction、hardlink、目录替代文件、symlink 测试 |
| A03 | high/P0 | install(force=True) 可覆盖无清单记录的同名 Agent | 未登记文件永远拒绝；仅清单已登记文件允许强制更新；未知碰撞测试 |
| A04 | high/P0 | _strip_our_config_lines 按行删除；merge_config 按假表头插入，只验证最终 TOML 可解析 | 每次改动比较完整 TOML 语义与期望路径；多行假表头/受管理假行回归，不能证明安全就拒绝 |
| A05 | high/P0 | 没有进程互斥或规划前后文件对比 | OS 锁与字节快照；跨进程持锁拒绝/退出释放和后续编辑测试 |
| A06 | medium/P1 | _read_state 仅粗查 schema；doctor 对 [] 等状态调用 get 可崩溃 | 校验 generator/settings/hash/元数据类型；共享清单校验；畸形 JSON/UTF-8 多例回归 |
| A07 | medium/P1 | merge_agents_md/uninstall 使用 rstrip/strip 改写用户空白，空文件可能删除 | 无损读入字节、记录拼接/存在性/原哈希；CRLF/空白/无末尾换行往返回归；旧清单保守保留多余空白 |
| A08 | medium/P1 | pyproject license 字符串不兼容声明允许的 setuptools 68–76；本机 72.1 实际构建失败 | 改为 license file 表；editable、wheel、干净环境安装验证 |
| A09 | medium/P1 | doctor 版本号/静态字段不足以表示运行能力，字段类型和 features.multi_agent 未覆盖 | 明确 UNKNOWN 和优先级；bool/limit/effort/role 检查，模型/线程仍未验证 |
| A10 | medium/P1 | 原评测无元数据/质量/上下文/线程字段；CSV 重复列/Unicode 数字与汇总溢出缺口 | 可选字段保持旧格式兼容；空值 UNKNOWN/null，拒绝歧义输入和非有限汇总，补回归 |
| A11 | medium/P1 | 仅单元测试，无真实 CLI/故障路径/干净 wheel 安装测试 | 新增 CLI、checker、storage 测试；跨版本/WSL 测试，CI 打包验证 |
| A12 | low/P1 | 旧文档数字和未发布占位 URL 容易误导 | 中英 README、当前状态/ADR/验收/路线图同步；历史材料明确标记 |
| A13 | medium/剩余 | 仅路径预检+OS 锁，不能覆盖恶意外部写者竞态或多文件同时可见 | 明确限制；不扩展为安全沙箱，不声称断电/网络文件系统已验证 |
| A14 | medium/剩余 | 恢复备份包含原配置字节；默认目录继承权限不足以保护私有备份 | 写入前仅所有者访问；已有 Windows 文件保留 DACL，专项测试通过；不上传、不提交，成功即删；跨身份权限需现场验证 |
| A15 | low/发布前 | 名称/商标/包名、维护者联系方式与远端 CI 未完成 | 保留发布阻塞，不创建远端、不假造截图或 Git 历史 |

critical：未确认。P0/P1 已落地修复如上，真实模型验证与远端发布不计入离线完成。接口调查与剩余验证见 [官方配置/P2](../OFFICIAL_COMPATIBILITY.md) 和 [验证报告](VALIDATION_REPORT.md)。

English: reviewed the original implementation before edits. High-priority fixes cover transaction failures, Windows path aliases, forced ownership, TOML scope and concurrent writes. Medium fixes cover manifest/type errors, byte preservation, packaging compatibility, diagnostic honesty and malformed evaluation input. Remaining limitations are explicitly documented; no runtime model or publication success is inferred.
