> 最新更新：独立 CLI 的角色/线程/运行时模型证据现已补齐，见 [CLI 原生验收](../CLI_NATIVE_VERIFICATION.md)。以下保留此前阶段记录。

# 独立环境真实验证（2026-10-23）

本次由用户明确授权真实模型请求、隔离环境内局部配置与私有远端测试。此前 0.2.0a1 离线报告是历史基线，本报告追加实际结果。

## 结果

| 项目 | 结论 |
|---|---|
| 三个目标模型的独立请求 | 三次均成功返回各自校验文本，CLI exit 0，有真实 thread.started/turn.completed 和 usage |
| 后端实际模型身份 | MODEL_NOT_VERIFIED：成功发送所选 model ID 不能证明服务端没有映射；事件未提供可独立核验的后端模型字段 |
| Sol → Luna workers → Astra 原生协作 | 未通过验收：存在协调器自述与 wait 事件，但没有完整的三角色真实子线程/模型对应证据 |
| 本地 hooks 观测实验 | NOT_OBSERVED；没有可用的 SessionStart/SubagentStart/Stop 记录，不当作已验证采集能力 |
| GitHub Actions | Windows/Linux × Python 3.11–3.14 共 8 个 job 全部 success，包含测试、构建与干净 wheel 安装 |
| 私有草稿 Release | isDraft=true、isPrerelease=true；三个附件上传、下载和 SHA256 比对通过 |
| 全局 Codex 配置 | 测试前后 SHA256 完全一致；未修改全局模型、代理或权限配置 |

## 隔离方式

独立目录：`E:/University/Github/我的/codex-triad-validation/20261023-34e47d23/`。

- source/：从已审阅 ZIP 提取的独立 Git 快照，用于私有远端 CI。
- runtime-project/：只有 app.py、README 和局部 .codex/AGENTS.md 的小型测试项目。
- venv/：独立 Python 环境，离线安装 wheel，64/64 单元与集成测试通过；结果在 evidence/venv-tests.txt。
- evidence/：仅本机保存的 JSONL、错误、线程与结果；目录设为仅所有者访问，原始日志没有上传。
- release-download/：从私有草稿下载的附件，逐一检查摘要。

这是工作目录、依赖、配置和会话数据的隔离，不是独立 VM/操作系统用户。复用现有 Codex 登录和机器网络；没有复制或展示凭据。CLI 使用 --ephemeral、read-only sandbox、--ignore-user-config、--ignore-rules，日志及 SQLite 状态指向独立目录。默认关闭 hooks/apps/plugins；一次本地已审阅 hook 实验在子进程中临时启用，结果未验证。

## 模型请求证据

| 请求 ID | 校验回复 | 耗时 | 真实 CLI 线程 |
|---|---|---|---|
| gpt-6-luna | TRIAD_LUNA_34E47D23 | 20.832s | 01a16723-e7b3-7ab2-b4e1-dc7f24dd155d |
| gpt-6.1-sol | TRIAD_SOL_34E47D23 | 8.904s | 01a16729-da79-76a0-8e98-cf3a509bd4a5 |
| gpt-6-astra | TRIAD_ASTRA_34E47D23 | 9.319s | 01a16726-4a4b-77a3-a053-1d6bfb29b2bc |

对应 usage 为 CLI 真实输出，完整字段见同目录脱敏摘要；不估算 USD 成本，也不据此声称三层工作流节省 token。它不是 A/B 实验。两次协调器请求分别只返回确认、或自述子 Agent 完成；自述不作为真实 spawn 证明。

## 实测故障与局部处理

1. 干净 CLI 直连出现 tls handshake eof，并重连；Luna 首次网络探测超时，没有当作模型不可用。
2. 系统代理存在但 HTTP_PROXY/HTTPS_PROXY 环境变量未设置。仅为测试子进程读取并继承系统代理后，三次独立请求成功；没有改变系统或全局代理。
3. 尝试直接加载现有全局配置时，strict 模式报告 preferred_auth_method 未知，普通模式报告 mcp_servers.node_repl 的 invalid transport。没有修改这份配置；最终通过 --ignore-user-config 做隔离测试。它不证明桌面客户端配置无效，只说明该 CLI 的解析不兼容。
4. 探测脚本初始给内置 openai provider 设置重试参数被保留 ID 校验拒绝，已从隔离脚本移除；没有修改 Triad 产品源码。

## 远端证据

- 私有仓库：[隔离验证仓库](https://github.com/ruanyueheng/codex-triad-validation-20261023-34e47d23)。
- [CI 完整运行](https://github.com/ruanyueheng/codex-triad-validation-20261023-34e47d23/actions/runs/39891519133)；commit `5c0de5dc91d10a12f22cf1f57635b2069860dab6`。
- [草稿 Release](https://github.com/ruanyueheng/codex-triad-validation-20261023-34e47d23/releases/tag/untagged-e8113b3e6b48ae7ee6e9)，三个附件下载摘要一致；没有公开发布，也没有发布到 PyPI。

上传内容只有已审阅的 54 文件源码快照和发行附件；没有上传运行日志、全局配置、auth 文件或密钥。保留私有仓库和草稿供用户复核，没有自动删除它们。

## 本机复现

进入上述独立目录。单次调用可能消耗额度：

```powershell
.\venv\Scripts\python.exe .\run_probe.py luna system-proxy
.\venv\Scripts\python.exe .\run_probe.py sol system-proxy
.\venv\Scripts\python.exe .\run_probe.py astra system-proxy
```

原始证据保留在本机 evidence/。脱敏摘要 `sanitized-summary.json` 只包含请求模型、线程、usage、CI 与附件核验状态。公开分享前仍请复核。

下一步应先在目标桌面/CLI 的正式线程事件接口中补齐 custom agent name → thread ID → runtime model 的证据链，并查明局部配置与 hooks 的实际加载；在这之前，原生三层协作与强制门禁均不能标记通过。

English: three independent requested-model CLI calls completed with nonce responses and real usage events, while backend model identity and the complete native custom-agent workflow remain unverified. All eight remote CI jobs passed. The private draft prerelease assets were downloaded and hash-checked. Global Codex configuration hashes are identical before and after testing. No credentials or raw runtime logs were uploaded; no public release was made.
