> 最新更新：独立 CLI 的角色/线程/运行时模型证据现已补齐，见 [CLI 原生验收](../CLI_NATIVE_VERIFICATION.md)。以下保留此前阶段记录。

# 完整协作开发案例验收（2026-10-23）

## 实际完成的链条：PASS

当前客户端真实 collaboration 接口执行，非独立模型调用的串行模拟。主协调器由真实 spawn_agent 请求 gpt-6.1-sol；它实际并行启动两个请求 gpt-6-luna 的子 Agent，等两者完成后改动隔离案例，再调用请求 gpt-6-astra 的审查 Agent。父协调器在运行过程中独立观察到了真实 agent tree 与阶段变化。

| 阶段 | 真实任务标识 | 结果 |
|---|---|---|
| Sol 协调 | /root/triad_sol_e2e | 分解、调度、集成、改源码、运行测试 |
| Luna 探索 | /root/triad_sol_e2e/triad_explorer | 定位折扣公式错误，给出 1-discount |
| Luna 测试检查 | /root/triad_sol_e2e/triad_researcher | 只读检查正常/零/全额/空列表四项契约 |
| Sol 实施 | pricing.py | 仅修改一行，不改测试；4/4 测试通过 |
| Astra 审查 | /root/triad_sol_e2e/triad_architect | 读取真实修改后的源码和测试，VERDICT: PASS；没有阻塞问题 |
| 父协调器复核 | 独立 unittest 进程与哈希 | 4/4 通过，测试文件哈希未变，全局配置哈希未变 |

## 真实案例

目录：`<private-validation-root>/endtoend-project/`，实际本机位置不作为公开使用路径。

原程序将“优惠比例”误当“支付比例”。[100,150] 等数组的折后总价应乘 (1-discount)；实际测试使用 [100,50]、20% 折扣，应为 120，修复前得到 30。

```diff
-    return sum(prices) * discount
+    return sum(prices) * (1 - discount)
```

修复前真实运行 4 项测试、3 项失败；修复后 Sol 和父协调器分别执行，均为 4 项通过。原测试内容没有改动。结构化结果在案例目录 E2E_RESULT.json，父进程原始测试输出在 evidence/e2e-independent-tests.txt。

```powershell
python -m unittest discover -s "<private-validation-root>/endtoend-project" -v
```

## 独立 CLI 路径：仍不能宣布通过

这次没有把客户端流程成功偷换成 CLI 配置集成成功。CLI 尝试使用临时会话时，输出过 no rollout found 的错误；取消 --ephemeral 并使用独立 CODEX_HOME 后继续测试。又修正 Windows .cmd 对多行参数的风险，改用原生 codex.exe 和 stdin 传递完整提示词。最后返回了三个角色的报告，但 CLI JSONL 仍只有 receiver_thread_ids=[] 的等待事件，没有足够的三个子线程/角色/模型映射证据，hooks 也未产生观测记录。

因此：客户端内的“Sol→两个Luna→Sol修复与测试→Astra审查→父进程复核”已实际完成；独立 CLI 自动发现/装载 .codex/agents 与完整事件证据仍为 NOT_VERIFIED。显式模型参数记录了请求选择，未声称服务端实际模型身份已独立核验。没有修改全局 Codex 配置，也没有进一步发布或 push。

独立 native-home 曾以私有符号链接复用缓存认证；测试结束已删除本次创建的认证入口，没有删除原认证文件，也没有将其上传。保留的案例与报告不包含凭据。

未检查范围外的非法输入/货币舍入规则；Astra 读取了实际文件，但测试结果依据 Sol 记录，父协调器另外独立验证通过。
