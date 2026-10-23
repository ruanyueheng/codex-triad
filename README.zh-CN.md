> 正式源码仓库：[ruanyueheng/codex-triad](https://github.com/ruanyueheng/codex-triad)（当前为私有）。克隆整个仓库即可获得自包含 skill，勿只复制 SKILL.md。

> 0.2.0a3：三种职责自由分配模型。运行 `python scripts/triad.py init --project PATH --interactive --dry-run`，从客户端实时返回的候选列表逐一选择主协调、工作者、顾问及推理强度；同一模型可以复用。去掉 --dry-run 后写入项目。角色不固定绑定任何模型家族。

> 0.2.0a3：独立 CLI App Server 已取得三个角色的自动加载、线程和运行时模型证据；提供自包含 skill 和离线证据核验。见 [CLI 验收](docs/CLI_NATIVE_VERIFICATION.md)。后端独立身份仍未核验，其他账户/版本须复验。

# Codex Triad · Codex 三级多 Agent 协作工具

[English](README.md) · [架构](docs/ARCHITECTURE.md) · [验证报告](docs/work/VALIDATION_REPORT.md) · [安全边界](SECURITY.md)

**0.2.0a3 本地预览，非 OpenAI 官方项目。** Triad 生成并维护 Codex 原生自定义 Agent 配置。它不代理模型请求，不强制调度，不保证节省额度。

以下仅为兼容旧版的默认预设，用户可以全部替换：

- `gpt-6.1-sol`：主协调与源码实现。
- `gpt-6-luna`：Explorer、Researcher、Triage 的有限范围只读调查。
- `gpt-6-astra`：重大设计、安全、两次同类失败、非琐碎提交前的顾问审查。

这些是目标配置；真实账户可访问性、子线程和模型身份仍为 **NOT_VERIFIED**。只读是角色指令，权限继承父会话。

## Windows 上手

Python 3.11+。解压源码 ZIP，进入含 `pyproject.toml` 的目录；无需先创建 GitHub 仓库。

```powershell
py -3 -m pip install -e .
py -3 -m codex_triad --help
codex-triad init --project "C:\Projects\MyApp" --dry-run
codex-triad init --project "C:\Projects\MyApp"
codex-triad doctor --project "C:\Projects\MyApp" --json
codex-triad smoke --phase workers
codex-triad smoke --phase advisor
```

没有 `codex-triad` 命令时，用 `py -3 -m codex_triad` 替代。macOS/Linux 使用 `python3` 和本机项目路径。已有构建工具且需要完全离线安装时，加 `--no-index --no-deps --no-build-isolation`；常规 pip 安装可能下载构建工具，Triad 五个命令本身不发起网络请求。

`smoke` **只打印提示词**。复制到 Codex 执行才可能消耗模型额度。在可信、可丢弃项目中新建会话，观察主模型、两个 worker 独立线程以及 advisor 线程；记录实际 thread/model/effort，无法确认时保留 `MODEL_NOT_VERIFIED`。详见[最小运行验收](docs/RUNTIME_VERIFICATION.md)。

## 安装、升级和卸载

```powershell
codex-triad init --project "C:\Projects\MyApp" --main-model gpt-6.1-sol --advisor-model gpt-6-astra --worker-model gpt-6-luna --main-effort high --advisor-effort high --worker-effort medium --max-subagents 3
codex-triad uninstall --project "C:\Projects\MyApp" --dry-run
codex-triad uninstall --project "C:\Projects\MyApp"
```

维护范围：`AGENTS.md` 中标记块、`.codex/config.toml` 中精确登记的新增行、四个 `.codex/agents/triad_*.toml` 和 `triad-state.json`。用户原有设置保留并提示冲突；`--force` 仅能覆盖清单已登记的 Agent 文件或策略块，不能认领未知文件，也不能覆盖改过的配置行。

实际操作有进程锁、逐文件原子替换与恢复记录。Windows 已有文件保留 DACL，新文件/临时备份限制为仅所有者访问；不同运行身份需要单独配置访问权限。正常失败会尝试回滚；进程中断后先检查本地备份，再运行：

```powershell
codex-triad init --project "C:\Projects\MyApp" --recover
```

`--recover` 仅恢复，不继续安装；卸载也可使用该参数。后续编辑与恢复内容冲突时拒绝覆盖。`.codex/.triad-transaction.json` 是临时本地备份，可能含原配置敏感值，不是加密文件，不应上传。完成后删除；空目录与 `.triad.lock` 保留。[安全写入设计](docs/ADR-001-SAFE-INSTALL.md)

`init --dry-run` 展示差异且不写文件；`uninstall --dry-run` 列出移除/恢复/保留范围。预览可能包含目标文件中的编辑内容，分享前请脱敏。损坏的 TOML、清单、符号链接、junction、硬链接以及无法证明安全的特殊 TOML 布局会被拒绝。

## 诊断和工作流边界

`doctor --json` 返回检查数组，每项含 `level/code/message`。PASS 只说明该静态项目通过；FAIL 是错误；WARN 是冲突/需检查；UNKNOWN 包括客户端功能、项目信任、有效模型与真实运行。退出码：0 为无 FAIL（仍可能 UNKNOWN），1 为诊断失败，2 为操作错误/参数错误。

主会话负责修改源码。Agent 输入应包含目标、范围、证据、约束和期望输出；各角色输出格式见[架构契约](docs/ARCHITECTURE.md)。Astra 检查点是 **advisory/prompt-based**，不是运行时门禁。当前不安装 hook，不修改全局模型/代理/权限，不读取凭据，不上传日志，不自动发起模型调用。

配置文件中的模型/effort 会覆盖该 Agent 的默认解析值；CLI、信任项目、profile 等层级仍影响父会话。工具不读取全局配置来猜测有效值。[官方配置核对](docs/OFFICIAL_COMPATIBILITY.md)

## 评测与开发

```powershell
py -3 -m unittest discover -s tests -v
codex-triad report --csv path/to/measured-runs.csv --json
py -3 -m compileall -q src tests tools
py -3 tools/build_release.py
py -3 tools/check_wheel.py
```

`report` 只汇总手工提供的观测数据；保留旧 CSV 兼容性，支持上下文量、子线程数、质量评分和实验元数据。缺失指标用 JSON null / 文本 UNKNOWN，不推算成本。模板与五类任务见 [evaluation](evaluation/tasks.json) 和[评测规范](docs/EVALUATION.md)。

[验证结果/未验证项](docs/work/VALIDATION_REPORT.md) · [风险清单](docs/work/AUDIT_FINDINGS.md) · [修改清单](docs/work/CHANGE_SUMMARY.md) · [故障排查](docs/TROUBLESHOOTING.md) · [贡献指南](CONTRIBUTING.md) · [发布检查单](docs/PUBLISHING.md) · [路线图](docs/ROADMAP.md)

许可证：[MIT](LICENSE)。名称/商标冲突、维护者联系方式及远端 CI 仍须发布前确认；此前本地交付之后，已获授权上传正式私有仓库；公开发布另行确认。
