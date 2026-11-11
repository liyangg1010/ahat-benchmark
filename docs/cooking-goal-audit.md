# Cooking reference goal audit — cooking-goals-v1

当前语义已由 [heated-v2](heated.md) 统一为一个 heated 结果和三个 heat 动作。
本文及 cooking_goal_inventory.json 是先前审查快照；其中 cooked、初始熟食和生鸡蛋
反例的论证属于旧模型，不再用于当前检查。餐食内容和供餐覆盖的审查仍有参考价值。
后续 FIX-011 已为两人热早餐、温热早午餐的鸡蛋节点显式声明 `serves_two=true`，
并补入参考目标；这两道的份量证据缺口已解决。下文两人份未表示的结论属于历史快照，
其他任务未自动补标。见 [当前份量语义](serves-two.md)。

后续 FIX-012 按语义覆盖删除 16 道相似备餐变体：其余 23 道保留 7 道，加上 4 道处理任务，
备餐候选为 11 道，总数为 339。下文 27/25 等数量和删留项为历史快照；当前审计保留历史清单，
只排除明确批准的删除 ID。见 [完整原指令及去重结果](meal-pruning.md)。

日期：2026-11-11。关联 FIX-006；本次只改两条源记录的参考字段。

历史更新（FIX-009，后被 FIX-010/011 取代）：以下是 cooking-goals-v1 审查时点的记录，逐题机器清单和旧验证
文件保留历史语义。当时温热早午餐目标已补 `(cooked breakfast_eggs_1)`，旧生鸡蛋
反例不再满足当前目标；原参考计划已包含 cook，无需改动。“两人份”的表示仍未解决，
所以该目标仍为部分检查，未新增到两道已确认充分目标中。当前证据见
[目标修复检查](validation/warm_brunch_goal_checks.json) 和
[全量参考检查](validation/warm_brunch_reference_checks.json)。

## 调查口径与结论

已审阅当前 355 条指令，并结合候选场景和参考计划逐题筛查：

| 口径 | 数量 | 含义 |
| --- | ---: | --- |
| 上次 cook 修复补标能力的场景 | 294 | 包含无烹饪要求的场景，不能作为烹饪任务数 |
| 明确要求食物烹饪、加热或热食 | 4 | casserole 复热、简单早餐、两人热早餐、两人温热早午餐 |
| 备餐、供餐的宽口径候选（包含上面 4 道） | 27 | 其中部分可能用冷食完成；不自动添加 cooked 要求 |
| 本次可确认充分参考 goal | 2 | 都已有 reference_goal，本次完善目标；新增目标字段为 0 条 |
| 本次不修改的备餐候选 | 25 | 未确认完整餐食、份量、场景含义或历史过程 |
| 单独列出的餐桌／氛围布置 | 17 | 不把布置指令改成烹饪指令 |
| 单独列出的食材／工具／设备准备和收纳 | 17 | 含电磁炉上电、火锅备料、饺子工具、烹饪后收纳等 |
| 单独列出的饮品／液体／沐浴 | 33 | 当前缺少液体温度和成分模型，本次不扩展 |

27 是人工筛查的候选范围，**不是 27 道必须 cook 的任务**。对于只取物、搬运或
以做饭作背景的指令，不从场景有炉灶推断烹饪要求。
逐条稳定 ID、指令、分类和判断理由见
[机器清单](validation/cooking_goal_inventory.json)。未列出的 261 条属于本次审查范围之外的取物、搬运或其他任务。
清单的源索引是当前快照的 0 起始索引；后续以稳定 ID 定位。

## 充分条件的边界

这里只认证当前 domain 和 scene 抽象内的一种充分完成方式，**不声称必要**。
指定餐盘、桌子、关机、空手等可以比指令更强。其他合法完成方式不需要达到这组
参考目标，运行时评分继续依据指令；这些目标只用于离线检查。

先人工检查目标是否覆盖指令，再用 native VAL 检查动作和合取目标，最后用合法的
不完整方案作对照，并逐步比对 scene 回写与 PDDL 执行。VAL 成功只证明可达性，
不能代替自然语言充分性审查。heated 沿用已有的无冷却布尔抽象；本次不添加真实
温度、时间、液体成分、食物份量、进餐或主观风格的判定模型。

## 两道确认任务

### 简单早餐并上桌

- ID：`fd22ff41-4720-497c-bad3-7411b468b6cc`；源索引 302，open。
- 指令：`Cook a simple breakfast and serve it`。
- 场景有真实鸡蛋早餐节点，初始未熟、未加热，锅具、炉灶及干净餐盘／餐桌均明确。
- cooked 只能由 cook 动作建立，因此不能通过只开电源或只 heat 满足目标。
  目标同时要求鸡蛋在干净餐盘上，餐盘在餐厅的干净餐桌上，覆盖烹饪和供餐。
- 指令未指定人数、菜式或处理设备；不把某个特定 cook 动作写成必要条件。
- 完善已有目标，保留已能达到该目标的 16 步参考计划。

参考 goal（全部合取）：
```lisp
(cooked breakfast_eggs_1)
(heated breakfast_eggs_1)
(item_on_surface breakfast_eggs_1 plate_48)
(item_on_surface plate_48 dining_table_3)
(furniture_in_room dining_table_3 dining_room_2)
(is_clean plate_48)
(is_clean dining_table_3)
(not (is_powered_on stove_2))
(handempty agent_0)
```

完整参考 plan：

```lisp
(navigate agent_0 outdoor_12 refrigerator_1)
(open agent_0 refrigerator_1)
(navigate agent_0 refrigerator_1 egg_carton_46)
(open agent_0 egg_carton_46)
(navigate agent_0 egg_carton_46 breakfast_eggs_1)
(pick_from_receptacle agent_0 breakfast_eggs_1 egg_carton_46)
(navigate agent_0 breakfast_eggs_1 pot_2)
(place_on_surface agent_0 breakfast_eggs_1 pot_2)
(navigate agent_0 pot_2 stove_2)
(power_on agent_0 stove_2)
(cook_on_heating_device agent_0 breakfast_eggs_1 pot_2 stove_2)
(power_off agent_0 stove_2)
(navigate agent_0 stove_2 breakfast_eggs_1)
(pick_from_surface agent_0 breakfast_eggs_1 pot_2)
(navigate agent_0 breakfast_eggs_1 plate_48)
(place_on_surface agent_0 breakfast_eggs_1 plate_48)
```

### 烤箱复热 casserole 后返回餐桌

- ID：`02a5f844-c663-4336-b6c9-fad5540b7cd5`；源索引 210，medium。
- 指令：`Before dinner, take the casserole from the dining room and reheat it in the kitchen oven. After heating, power off the oven and return the casserole to the dining room table.`
- casserole 初始位于餐厅 counter_40 内，cooked=true、heated=false，表示已经做好的冷菜。
- 当前 scene 唯一具备微波炉／烤箱／炉灶能力的设备是厨房 oven_30；能力不可由动作增加。
  cooked 永不删除，所以 cook 的 not-cooked 前提永远不成立。建立该菜的 heated
  只能通过 oven_30 上的 heat_with_oven，要求菜在关门且开机的烤箱内。
- 初始没有 can_be_moved，烤箱和桌子的房间位置不变。末态要求加热后的菜在餐厅
  table_29 上且烤箱关闭电源，因此加热之后必有返回和关机；餐厅来源由初态保证。
  参考计划还明确采用“加热 → 关机 → 取出 → 返回”的顺序。
- 完善已有目标，参考计划从 19 步简化为 16 步，去掉先把菜暂放烤箱表面再拾取的绕行。

参考 goal（全部合取）：
```lisp
(cooked casserole_21)
(heated casserole_21)
(item_on_surface casserole_21 table_29)
(furniture_in_room table_29 dining_room_1)
(furniture_in_room oven_30 kitchen_1)
(not (is_powered_on oven_30))
(handempty robot1)
```

完整参考 plan：

```lisp
(open robot1 counter_40)
(navigate robot1 counter_40 oven_30)
(open robot1 oven_30)
(navigate robot1 oven_30 casserole_21)
(pick_from_receptacle robot1 casserole_21 counter_40)
(navigate robot1 casserole_21 oven_30)
(place_in_receptacle robot1 casserole_21 oven_30)
(close robot1 oven_30)
(power_on robot1 oven_30)
(heat_with_oven robot1 casserole_21 oven_30)
(power_off robot1 oven_30)
(open robot1 oven_30)
(navigate robot1 oven_30 casserole_21)
(pick_from_receptacle robot1 casserole_21 oven_30)
(navigate robot1 casserole_21 table_29)
(place_on_surface robot1 casserole_21 table_29)
```

## 不修改的候选

“不确认”不等于已证明任务不可完成。包装、果碗、汤罐、酸奶杯等可能包含食物，
但不能凭容器名称虚构内容、份数或已熟状态。存在生鸡蛋也不意味着指令必须 cook；
缺少份量模型时，两只杯子或两只盘子不能证明已经准备两人份食物。

| 源索引 | 稳定 ID | 指令 | 暂不修改的理由 |
| --- | --- | --- | --- |
| 238 | `7b007eb0-dfe0-4bcd-8697-8926d4572585` | Prepare a cozy dinner tonight | 原计划只准备饮品；可识别的直接食物仅黄油，包装和 fruit_bowl 未明确内容，不能确认完整晚餐。 |
| 240 | `cb22d87c-0879-4709-9985-4f367772bf44` | Host an elegant dinner this evening | 原计划只布置餐桌；包装、蔬菜篮和果碗内容未明确，无法保证已供餐及 elegant 的完整语义。 |
| 243 | `a55dd1af-59ee-4e0c-8139-208e2134ed49` | Plan and serve a complete evening meal | 苹果和葡萄可以供食，但不能据此保证 complete evening meal；不自行把水果摆放定义为完整晚餐。 |
| 246 | `3cf1736a-3b96-4913-b9c5-df4688ee9053` | Prepare an elegant dinner and ambiance | 原计划只有餐具和氛围布置；胡萝卜和黄瓜可食，但缺少完整晚餐与 elegant 的可验证完成标准。 |
| 249 | `5e8f884f-03be-4d9d-aa32-14003a8aaf52` | Prepare a comforting breakfast and serve it | 原计划摆放牛奶包装、鸡蛋包装和黄油；没有明确可烹饪鸡蛋或准备好的主食，不能确认早餐已完成。 |
| 254 | `590bda12-228f-4784-9caa-404aa7340332` | Prepare an inviting meal for family tonight. | 原计划把锅和餐具移到桌上；锅内没有明确熟食，family 的供餐人数和份量也未表示。 |
| 255 | `861111df-3fbf-4569-9df9-2d3a9da81415` | Host an elegant evening meal | 原计划只有餐具和氛围布置；未确认可供食用的晚餐内容，不能以摆桌替代供餐。 |
| 260 | `7853d8d5-fccc-42e1-8540-cfe67325b42d` | Prepare a complete breakfast for two. | 有直接鸡蛋和两只盘子，但没有食物分份或份量模型，无法证明 complete breakfast for two；不为同一份鸡蛋虚构两份状态。 |
| 261 | `f3ee3e87-d782-4870-8ed3-2bc92f344010` | Host a cozy dinner for two tonight. | 有鸡蛋和牛奶，但 two 的份量/份数和完整晚餐未表示；原计划仅作氛围布置。 |
| 268 | `21d63cf0-3045-4d01-a88a-fe6f7d3e3499` | Prepare a cozy family dinner tonight | 原计划仅布置桌面和灯；果碗内容、family 的份量和晚餐内容未明确。 |
| 269 | `ff25ff1c-035a-474b-a42a-e16c6ea1965f` | Make tonight's dinner special for everyone | 原计划摆放桌布、锅具和调料；无明确已准备的晚餐，也无法表达 everyone 的供餐份量。 |
| 270 | `b2ac8958-c1dc-42d9-a41a-b6e0d8b8dd39` | Prepare a relaxed family breakfast | 原计划摆放牛奶包装和果碗；不能从包装/果碗节点推断早餐内容和 family 的供餐份量。 |
| 273 | `bc56e4a3-3772-456f-9ae6-8c3396f52880` | Prepare breakfast for two | 鸡蛋仍为包装；直接食物仅酥油，无法确认完整早餐及两份供餐。 |
| 279 | `f623e258-d97b-4a07-9121-0337a5fd3277` | Prepare a hearty breakfast for two guests | 只有牛奶包装和鸡蛋包装，缺少明确鸡蛋/主食；两位客人的份量和 hearty 均不能保证。 |
| 284 | `7bc96205-5b58-4310-b056-8768d2c9ca7a` | Host a cozy dinner for guests | 原计划只布置氛围和餐位；未明确食物，guests 的供餐人数和份量也未表示。 |
| 292 | `e2d7a48c-0bc8-4a23-a932-83b4cbee492a` | Make breakfast for two and serve | 鸡蛋仍为包装；原计划的杯子未获得饮品，早餐内容和两人份不能保证。 |
| 293 | `9027ed1b-fcf9-4f17-8b39-c397d4db7563` | Prepare a warm brunch for two. | 旧 goal 可由 heat 替换 cook 达成，留下未熟鸡蛋；另缺两人份表达。保留数据，不将旧标注认证为充分条件。 |
| 300 | `43f14fb2-001a-495e-b9f6-ae11b67c964b` | Prepare an elaborate breakfast and serve it | 原计划摆放包装和空碗；现有酸奶杯未明确内容，不能据此保证 elaborate breakfast。 |
| 301 | `dec162ab-e453-419f-971a-2e32987350f2` | Prepare an elegant dinner for guests | 苹果和奶酪可食，但不能确认满足 elegant dinner for guests 的完整供餐和人数要求。 |
| 303 | `0cf41a97-9f6a-4e13-8542-1def6889483d` | Host a cozy brunch for two. | 有鸡蛋、牛奶和苹果，但 two 的份量未表示；原计划仅摆杯、装饰和苹果，不能据此保证两人早午餐。 |
| 308 | `4a3dc074-3cd6-4241-a4a5-2c37f31c99a1` | Host a formal dinner and cleanup | 要求先晚餐后清理；既没有明确已供餐食物，也没有 served/cleaned-after-serving 等历史状态，末态干净不能证明举办过晚餐。 |
| 319 | `4bddb476-f1ae-44e1-9558-add1571dd936` | Make a hot breakfast for two. | 旧 goal 可确认熟热鸡蛋和伴餐，但没有两份/两人供餐的表示；VAL 可达不足以认证整条指令完成。 |
| 327 | `2608e618-305d-46d2-b563-2ca9bc351c7b` | Prepare a full weekend brunch. | 原计划只摆餐具和果碗；果碗/汤罐内容及 full brunch 的完成标准未明确。 |
| 330 | `198fd035-6f65-4740-8b01-0643a215ccb4` | Prepare a full family breakfast service | 有鸡蛋、黄油和餐具，但 family 的供餐份量未表示，不能保证 full family breakfast service。 |
| 338 | `e8f12ff2-1929-497a-9d87-103ff77d2110` | Prepare a comforting weekend breakfast for two | 有鸡蛋、牛奶、黄瓜和两只杯子，但没有两份食物的表达；两杯不等于两人早餐。 |

## 旧标注的具体反例

`9027ed1b-fcf9-4f17-8b39-c397d4db7563` 的旧目标只要求鸡蛋 heated，未要求 cooked。
将参考计划中的 cook_on_heating_device 换成 heat_on_heating_device：

- native VAL 判为合法；
- 完全达到旧 reference_goal；
- 最终 cooked breakfast_eggs_1 为 false。

因此旧标注不能被认定为整条早午餐指令完成的充分条件。仅补 cooked 仍没有解决
“for two”的份量问题；遵照本次要求，保留这条任务数据，记录为待后续建模。
`4bddb476-f1ae-44e1-9558-add1571dd936` 的旧目标已要求 cooked+heated，但同样缺少
两人份供餐表达。这两条旧目标仍可检查部分结果，不应被误称为完整充分目标。

## 验证与溯源

写入前，先把候选记录放在本地审计目录，检查两条候选的目标、计划、6 个合法反例
和 32 步 scene/PDDL 重放；确认未认证的其他 353 条记录完全不变后才写入源数据。
本次共修改 2 组 goal、1 条 plan；全部 ID、指令、scene、split、domain 和 rubric 不变。
参考标注仍为 18 组。运行时 split 文件内容及版本不变；只更新源 artifact 哈希和
hf_sync.json 的 local_cooking_goals 溯源。修订脚本保持幂等。

复查：

```sh
PYTHONPATH=src python scripts/audit_cooking_goals.py
PYTHONPATH=src python scripts/check_reference_plans.py
PYTHONPATH=src python scripts/repair_cooking.py
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/check_release.py
```

[语义前提、计划及反例检查](validation/cooking_goal_checks.json) 和
[全量参考验证](validation/cooking_goal_reference_checks.json) 记录当前源和实现哈希。
机器检查保护人工审查使用的前提，不能作为对任意自然语言任务的自动充分性证明。
FIX-006 的 cooking_v1_checks.json 保留为历史证据。本次未调用 LLM 评分或对外发布。

本次实际结果：66 项测试通过；355/355 参考计划合法、18/18 已标注目标达成；
11 个邻接控制、4 个处理省略控制通过；四道处理参考共 80 步 scene/PDDL 重放一致。
本审计额外检查的 6 个合法不完整方案均不能满足两条新目标，旧早午餐反例则能满足
旧目标并保留生鸡蛋。修订脚本复跑为 0 条待修改，发布源检查和差异空白检查通过。
