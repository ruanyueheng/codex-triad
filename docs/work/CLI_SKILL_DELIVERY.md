# 0.2.0a2：CLI 原生证据与 Skill 交付

日期：2026-10-23。独立 `codex app-server --listen stdio://` 真实执行，使用隔离 Codex home 和项目；未用当前聊天子 Agent 的结果替代本次 CLI 证据。

## 已通过

- 原生加载 triad_explorer、triad_researcher、triad_architect；thread/list 返回精确 agentRole、parentThreadId 和不同 UUID。
- subAgentActivity 启动记录给出 gpt-6-luna / gpt-6-luna / gpt-6-astra，root 为 gpt-6.1-sol。模型是客户端运行时选用值，后端身份仍 UNKNOWN。
- 两 worker 运行区间重叠，两个完成后才启动 advisor，父 turn 成功完成。正式记录与脱敏文件见 [原生验收](../CLI_NATIVE_VERIFICATION.md)。
- 可复用 `scripts/collect_runtime.py` 再次实跑通过，父线程 01a16860-ec66-76c3-98ba-62d383636646；不依赖孤立原型脚本。
- Windows Python 3.11.15、3.12.14、3.13.5、3.14.6：各 69 项全部通过。WSL Ubuntu Python 3.12.3：67 项通过、2 个 Windows 专项跳过。
- skill-creator 静态校验：Skill is valid。独立子 Agent 按 SKILL.md 安装演练：保留 personal-model、agents.enabled=false 和原团队规则；重复 dry-run 无新增修改；doctor 正确返回未就绪，不谎称多 Agent 可运行。
- root SKILL.md 与 scripts/src/docs 构成自包含技能，scripts/triad.py 无需全局 pip 安装；提供 source、wheel 与 skill ZIP。源码/skill ZIP 构建、wheel 干净安装、skill 解压后离线核验均已通过，包摘要见 dist/SHA256SUMS.txt。

## 本次关键修正

此前 exec --json 未显示 subAgentActivity，而 wait 的接收线程列表为空；这不能当作没有执行，也不能当作执行成功。改为正式 App Server 协议，并用 thread/list 交叉核对，而不是解析私有 transcript。

随机角色标记实验仅用于检查开发指令加载：Researcher 与 Architect 返回其本地文件中随机标记，Explorer 未返回。保留这个不完美结果；不把行为指令说成必然遵守或安全门禁。之后恢复原有角色文件再运行正式采集脚本，核验通过。

## 配置与隐私核对

所有显式配置写入均限于隔离项目/home，没有执行全局 config/value/write 或 config/batchWrite。收尾时发现全局配置相对最初快照的 SHA256 已变化，18:46:55 有写入；本轮没有完整的进程审计，不能归因，也不回滚并行设置。不能将此前“哈希一致”的阶段记录扩展为整个会话期间都一致。详细比对只保留本机。

独立 home 认证引用已删除；原始认证文件未删除或上传。本次没有安装进全局技能目录，没有公开发布或将新包上传 GitHub。此前私有仓库 0.2.0a1 的远端 CI 成绩不冒充本版远端成绩。

后续公开上传：明确 owner/正式仓库与可见性，确认许可证/名称/维护者渠道，在新版本提交上跑远端 CI，再发布预览。模型权限、不同客户端版本、后端独立身份、成本收益和强制审查仍各有边界，不能凭本机一次通过推广。
