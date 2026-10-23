# 修改清单 / Change summary

版本：0.1.0 → **0.2.0a1**。保留源码目录结构与 init/doctor/smoke/uninstall/report 五个命令。

| 范围 | 改动 |
|---|---|
| 新增 storage.py | 集中路径保护、锁、原子替换、快照、事务/回滚/恢复、Windows DACL 保留与私有暂存；没有新增运行依赖 |
| installer.py | 生成与所有权规划复用存储层；语义验证合并；--force 不认领未知文件；精确保留用户字节和空文件 |
| checker.py | 共享路径/清单验证，字段类型与禁用检查，未知运行事实明确 UNKNOWN |
| cli.py/templates.py | 恢复参数、ultra 可选强度、干运行差异、quota/evidence 提示、正式角色输入输出契约 |
| benchmark.py/evaluation | 旧 CSV 兼容；质量/线程/上下文与实验元数据可选列，安全数值验证，五类任务和证据模板 |
| tests | 保留原 26 项并增加故障注入、进程锁/中断、Windows 路径、CLI、JSON 与评测回归 |
| pyproject/__init__/MANIFEST | 0.2.0a1、本机可用的兼容许可证元数据、完整源码分发清单 |
| tools | 本地无网络 wheel/源码 ZIP 构建、摘要校验、干净 venv 安装和命令验证 |
| .github | Windows/Linux、Python 3.11–3.14，语法/包构建/干净安装；模板已审阅，无额外发布权限 |
| 文档 | 中英 README、安全 ADR、官方核对/P2、风险、验证、运行验收、路线图和发布清单 |

兼容性：所有旧命令/参数保留；schema-1 清单可升级。新增 --recover 是独立恢复操作，不能和 --dry-run 同用。doctor JSON 仍是 level/code/message 数组，但增加 UNKNOWN 等检查；report JSON 保留旧字段并增加可选指标。PARTIAL_UNINSTALL 继续保留旧退出码 0，并打印未完整卸载提示。未知同名文件的 --force 行为有意收紧，需先人工移走或合并。

当前目录没有 .git；本报告与基线快照差异供审阅，不声称存在真实 Git commit/diff 历史。不初始化仓库，不做远端操作。

English: retain five commands and legacy flags/schema, add isolated recovery and optional metrics, tighten force ownership, and keep runtime uncertainty explicit. New shared storage code solves file safety once; no framework or runtime dependencies were added. This source directory contains no Git metadata or invented commits.
