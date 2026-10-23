# 故障排查 / Troubleshooting

| 现象 | 操作 |
|---|---|
| 导入或命令找不到 | 在含 pyproject.toml 的目录安装；用同一 Python 运行 pip 与 `-m codex_triad` |
| setuptools 缺失 | 离线构建需要已安装的 setuptools>=68；正常 pip 安装可准备构建环境，不要伪称离线构建已成功 |
| Invalid TOML/UTF-8 | 修复指定项目文件编码/语法；工具不猜测编码并覆盖 |
| 无法安全合并 TOML | 内联表、特殊引号或多行字符串可能触发保守拒绝；人工整理 agents 表，先备份再预览 |
| 未知同名 Agent | 先移走/改名或人工对比；`--force` 不认领未登记文件 |
| 已修改的登记文件 | 先对比；需要放弃这些修改时才对已有登记文件使用 --force；配置行始终人工处理 |
| 锁冲突 | 等另一 Triad 进程退出后重试；不要删锁文件绕过仍在运行的操作 |
| 中断恢复记录 | 检查 `.codex/.triad-transaction.json`，运行 `init --recover`；该操作不继续安装 |
| 恢复与后续编辑冲突 | 保留备份和当前文件，离线人工合并；不要上传恢复记录 |
| PARTIAL_UNINSTALL | 修改过的 Agent/策略块被保留；状态清单保留以便再次核对，不代表卸载完整成功 |
| symlink/junction/hardlink | 选择普通本地项目与普通文件；工具不会跟随链接写入其他位置 |
| 权限/杀毒占用 | 关闭占用目标文件的程序，确认项目目录可写；回滚失败时保护恢复记录 |
| doctor exit 0 但不能启动 | 0 只代表无静态 FAIL；UNKNOWN 不表示运行成功。检查信任、客户端、账户与模型访问 |
| 版本探测 UNKNOWN | CLI 可能不在 PATH，桌面仍可能可用；doctor 不由版本号推断功能支持 |
| `--interactive` 的 App Server 启动失败 | 查看原始错误；桌面全局配置可能包含当前 CLI 不支持的字段或 MCP transport。使用单独配置并通过正常客户端登录的 Codex home，再传 `--codex-home PATH`，不要改全局配置来掩盖兼容性错误 |
| skill 未出现在选择器中 | 检查目标仓库 `.agents/skills/codex-triad/SKILL.md` 与配套目录；单纯克隆源码不等于注册。按需重启 Codex，或先显式引用 SKILL.md 的绝对路径 |
| smoke 后没有子线程 | smoke 只打印提示词；在已授权、已信任的目标会话中执行才会启动真实调用 |
| 模型/线程无法确认 | 保留 MODEL_NOT_VERIFIED；不要用模型自述或 TOML 代替可信运行证据 |
| 子 Agent 失败 | 记录原始错误、请求角色、客户端版本；明确说明退回主线程，不模拟子线程成功 |

退出码：doctor 静态错误 1；操作/参数错误 2。卸载部分成功会打印 PARTIAL_UNINSTALL，仍保留旧版退出码 0 兼容性。

权限与 provider 继承父会话；不更改全局权限/代理来掩盖失败。优先最小复现，分享输出前去除密钥、私有路径和日志正文。

English: preserve original errors, never infer runtime success from static checks. Resolve unknown-file collisions manually, wait for active locks, and use explicit recovery after interruption. Recovery refuses later edits. Partial uninstall preserves the manifest and prints PARTIAL_UNINSTALL while retaining the legacy exit status. See the bilingual README and [runtime verification](RUNTIME_VERIFICATION.md).
