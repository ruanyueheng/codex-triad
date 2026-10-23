> 本次上传前复核：77项本地测试、skill校验、干净wheel安装通过。另在隔离项目真实验证三个职责复用gpt-6.1-sol，线程/模型/生命周期/顺序核验PASS。正式仓库当前为私有；新提交远端CI状态见GitHub。

> 新增：三种职责自由分配客户端报告的模型；交互菜单按模型提供推理强度，允许复用，同步自定义组合核验和skill指令。候选可见不等于已实测调用成功。

# Codex Triad 0.2.0a3 · Local preview

本次新增独立 CLI App Server 取证与核验、自包含 SKILL.md 和无需全局安装的脚本入口。真实数据见 [CLI 验收](docs/CLI_NATIVE_VERIFICATION.md) 与 evaluation/cli-runtime-20261023.json。

本机 Windows CLI 0.163.0 已观察到 Sol 父线程、两个 Luna 角色子线程和 Astra 子线程；角色、父子关系、启动模型、生命周期和先后顺序由协议交叉核对。它是客户端运行时模型证据，不是后端独立身份认证，也不保证所有账户和版本可用。

完整命令仍保持五个；新增 `report --runtime-evidence FILE --json` 是离线核验，不调用模型。真实采集脚本需要显式 --run，可能消耗额度。测试与新包验证见本次交付日志；此前私有仓库的八项远端 CI 属于 0.2.0a1 快照，不能冒充本版本远端验证。

源码 ZIP、wheel 与 skill ZIP 可本地使用；未安装到全局技能目录，未公开发布。skill ZIP 必须保留 scripts/src/docs 配套目录，不能只提取 SKILL.md。保持 MIT 协议；公开 GitHub owner/名称/可见性与发布授权仍待明确。
