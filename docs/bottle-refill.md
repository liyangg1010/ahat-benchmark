# 水瓶任务去重与开瓶注水：bottle-refill-v1

四道 reusable water bottle 任务保留两道代表，另外两道完整归档并退出正式评分集合。
总数 **289→287**：easy 130、medium 65、open 92；普通 domain 257 道，液体 domain 30 道。
此前隔离的 7 道任务不变，重复任务归档与不支持任务隔离分别记录。

| 决定 | 任务 ID | 语义 |
| --- | --- | --- |
| 保留 | `6e590abe-0592-4a01-8de9-269cdd94fa89` | 水瓶装水后交给楼梯上的人 |
| 保留 | `44a3890d-31fb-4a53-b9d2-1d7f2e22f686` | 从卧室书桌取瓶，到指定洗衣房水槽注水后归位 |
| 归档 | `baebc10b-0942-4ab8-a948-b5ce3630af75` | 补水后放回学生卧室，重复注水后摆放能力 |
| 归档 | `ca93f23c-c8c5-426f-81f5-4f7e51811dfc` | 补水后放在厨房，主要是目的地变化 |

两道保留任务原本已显式使用 `ahat-liquid-v1`，本次确认并保留该绑定，
没有让它们经过普通 domain 的宽松注水动作。
原指令、scene、ID、难度及 liquid_reference 结果断言均不变；
参考计划在拿起水瓶前加入 `open`，因为当前 open 要求空手。
顺序步骤见证也加入开瓶。两条计划各从 6 步增加到 7 步。

仅修改液体 domain 的 fill_from_faucet 前置条件，增加：

```lisp
(imply (can_be_opened ?c) (is_open ?c))
```

可打开容器必须已经打开；普通无盖杯子无需新增动作。注水效果保持原样，
不会自动打开瓶子。未增加最终必须盖好瓶子的任务要求，未修改其他注液动作、
普通 domain 或 PDDL 空间防环规则。其他液体动作的开口约束仍需另行审查。

修改入口为 `scripts/build_liquid_domain.py`，生成后的 liquid domain revision
更新为 `bottle-refill-v1`；普通 domain 保持 `scene-lighting-v1` 且字节不变。
easy/medium/open split 版本分别更新为 **1.9.1 / 1.9.0 / 1.9.1**，
域注册表、任务数及数据哈希同步。液体推理结果必须带新 domain SHA-256，
旧液体结果和旧评分分母不能直接复用。

## 验证与数据追溯

- 104 项测试通过；287 条参考计划合法，18 个既有 reference_goal 全部可达。
- 液体／器具 32 组结果断言通过，485 步 scene/PDDL 回放一致，74 个遗漏动作对照通过。
- 两道旧参考计划在旧液体 domain 下合法，在新 domain 下因未开瓶而非法；
  补充 open 后合法，并达到原有结果。末态仅多出相应 `is_open` 事实。
- 新增反例验证关闭瓶子（显式 false 或缺省）不能注水，打开瓶子可注水，普通杯子仍可注水。
- 其余 **285 条记录及 JSONL 源行原字节不变**；归档的两条记录与修复前完整记录一致。
  迁移脚本重复运行无数据变化。未运行真实 LLM 裁判。

[重复任务原始记录](../benchmarks/bottle-refill-v1/pruned.json)保留删除原因和代表映射。
[修改清单](validation/bottle_refill_v1_inventory.json)记录修复前的源／split 索引及前后计划。
验证见[范围与原生 VAL 对照](validation/bottle_refill_v1_checks.json)、
[全部参考及目标](validation/bottle_refill_v1_reference_checks.json)、
[液体审计](validation/bottle_refill_v1_liquid_checks.json)。
`scripts/repair_bottle_refill.py` 默认仅报告变化，`--write` 执行迁移并同步 manifests。
