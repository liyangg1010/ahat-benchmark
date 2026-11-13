# 三道晚餐任务补充食物：dinner-food-v1

后续状态：用户已采纳三组成功方案，正式参考已按 dinner-reference-v1 替换为
44／62／76 步；详见 [当前参考及验证目标](dinner-reference-candidates.md)。
下文关于“原参考未修改”的说明及验证计数保留本次场景补充时点，不代表最新参考状态。

2026-11-12。按用户要求为三道开放式晚餐任务补充可操作的食物。
第一道原有苹果和葡萄，第二道原有胡萝卜和黄瓜，第三道只有未明确建模内容的
鸡蛋盒、牛奶盒；包装名称不作为内部存在食物的证明。

| 任务 ID／原指令 | 新增实际食物节点 | 初始位置 |
| --- | --- | --- |
| `a55dd1af-59ee-4e0c-8139-208e2134ed49` — Plan and serve a complete evening meal | `chicken_breast_162`（鸡胸肉）、`potatoes_163`（土豆）、`broccoli_164`（西兰花） | `in refrigerator_19` |
| `3cf1736a-3b96-4913-b9c5-df4688ee9053` — Prepare an elegant dinner and ambiance | `salmon_fillet_220`（三文鱼）、`potatoes_221`（土豆），搭配原有胡萝卜和黄瓜 | `in refrigerator_32` |
| `4a3dc074-3cd6-4241-a4a5-2c37f31c99a1` — Host a formal dinner and cleanup | `beef_steak_99`（牛排）、`potatoes_100`（土豆）、`green_beans_101`（四季豆） | `in refrigerator_14` |

新增共 8 个独立食物节点及 8 条位置边。业务 type 使用现有 meat、seafood、potato、
vegetables 分类；PDDL 类型均为 small_object。每个节点声明：

```json
{
  "is_food": true,
  "can_be_heated": true,
  "heated": false,
  "is_clean": true,
  "can_be_moved": true
}
```

沿用统一 heated 模型，不区分初始生熟，不增加 cooked 状态。
三条原指令均未指定人数，本次不人为指定 serves_two 或 serves_group。
原有水果、蔬菜和包装节点均保留；没有把盒子改成食物，也没有增加设备或修改 domain。

验证使用现有设施：第一道的 cooking_pot_72／stove_49 与 plate_set_37，第二道的
pot_63／stove_33 与 plate_143，第三道的 cooking_pot_13／stove_15 与 plate_set_15。
每道独立见证先将餐具摆到餐桌，再开冰箱、逐一取食物、加热、关炉并放到餐具上。
三条见证均经真实 VAL 判合法，所有新增食物的 heated、在餐具上及餐具在餐桌上
目标均可达；与原参考合计 177 步 scene/PDDL 回放一致。

这些见证只证明新增食物可实际使用，不替代正式参考，不认证完整晚餐、优雅氛围或
餐后清理已完成。正式指令、参考计划、reference_goal 和 domain 分配均不变。
当前原参考仍只使用已有水果或布置餐桌，新加食物在原参考末态仍留在冰箱里；
参考计划的供餐／清理语义仍需后续单独审查。
后续已采纳 [三道任务的参考 plan 与验证目标](dinner-reference-candidates.md)，
分别为 44、62、76 步，均验证合法且目标可达；第三道包含先供餐再撤餐的阶段目标。

只修改 3 条源 scene 及 open split 的对应副本；其他 284 条 JSONL 行原字节不变。
任务数仍为 287（130/65/92），两个 domain 字节不变；open 版本从 1.10.0 更新为
1.10.1，easy/medium 均保持 1.10.0。hf_sync 保存前后数据哈希与验证记录。
重新推理这三道任务时应使用更新后的 scene 和新评测输出。

幂等修订脚本：

```sh
python scripts/repair_dinner_food.py          # 只报告计划修改
python scripts/repair_dinner_food.py --write  # 先验证候选，再写数据；已修订时不再写入
```

详见 [新增节点与可用性见证](validation/dinner_food_v1_checks.json)、
[全量参考检查](validation/dinner_food_v1_reference_checks.json)、
[全量场景与回放检查](validation/dinner_food_v1_scene_checks.json)。
全量回归：287 条参考合法，18 组既有目标、11 个邻接及 4 个热处理对照通过；
287 个 problem 独立解析通过，初态无事实丢失，3,985 步 scene/PDDL 回放一致。
移除本次新增的 8 个节点与位置边，可精确复原修订前源文件的 SHA-256。
doctor、发布源文件检查及 git diff --check 通过。
本修订未调用真实 LLM 裁判，未发布；三项已决定暂缓的模型问题保持暂缓。
