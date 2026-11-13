# 液体专用 domain：liquid-v1

液体任务已按 [bottle-refill-v1](bottle-refill.md) 修订：水瓶任务四留二，
可打开容器注水前须打开。正式任务 274 道，其中 30 道使用液体 domain。
下文任务数及 liquid-v1 证据保留初次迁移时点。
普通 domain 后续更新为 ordinary-core-v1，移除了五个液体动作；生成器独立加入
这些动作，液体 domain 字节与 bottle-refill-v1 完全一致。见
[FIX-021](repair-log.md#fix-021普通-domain-移除液体制作与转移动作)。
最新两个 domain 均为 [type-hierarchy-v1](domain-types.md)，修正内置根类型与
small_object 映射，更新两个 domain 哈希；保持液体动作语义、任务数据及目标不变。

后续 `location-capacity-v1` 已修复两个 domain 的移动位置和摆放容量约束，更新协议哈希；
任务数据和液体制作规则不变。当前共享动作与验证见 [动作不变量修复](action-invariants.md)。
下文关于“普通 domain 字节保持不变”的描述及 liquid_v1_* 证据属于液体初次迁移时点。

2026-11-11。前序修复及去重已提交为 `c14898f`。本修订保留普通
`ahat-v8-group-portions` 的 PDDL 字节和四份裁判提示词，新增完整的
`ahat-liquid-v1` 及独立裁判规则。基础包仍为未发布的 2.3.0。

正式集合 **296→289**：easy 130、medium 67、open 92，split 版本为
1.8.0 / 1.7.0 / 1.8.0。257 道使用普通 domain，32 道使用液体 domain。
7 道隔离任务不进入正式 splits、默认推理集合或评分分母。

## 审查范围与数据变化

审查了去重阶段 42 道液体指令，以及清单外三道实际使用液体动作的任务，以及一条复查发现的水壶检查任务，共 46 道：
32 道迁移，2 道只需准备器具的任务修正参考计划后保留普通 domain，5 道现成饮料搬运
记录完全不变，7 道隔离。其余 250 道未变，合计 **255 道记录及参考末态不变**。
所有保留指令、ID、难度划分保持不变；已有 18 个 reference_goal 全部保留。

初态补充有明确依据的能力：三个已有 sink_cabinet 的水龙头属性、茶盒／咖啡原料、
水壶和咖啡机能力，以及指令明确要求取用的现成热茶。新增状态是本地场景修订，
不是从旧 plan 的成功反推初态。没有新增炉子、菜地或热水管网来掩盖场景缺失。

旧计划的典型修复：

- 指定 laundryroom sink_cabinet 装水的任务使用该柜体的水槽，不再去浴缸。
- 茶任务真实装入茶原料并冲泡；咖啡任务真实装水、装料、出杯。
- 杯中热水沿倒水动作传递；浇植物产生 watered，而不是把植物标成“装满”。
- 方便面杯从柜中取出，再加热水并完成冲泡；不把水壶放在面杯上。
- 要求从水壶倒热水到浴室碗的任务使用水壶，并清洗明确要求干净的漱口杯。
- “取现成热茶”声明初态已有热茶，执行搬运，不强迫重新泡茶。
- 只开水壶、准备杯子或给别人备好器具的任务，不升级为制作饮品的要求。

## 模型边界

液体没有独立对象节点；内容存于容器 `states`。主要字段：

| 状态 | 含义 |
| --- | --- |
| is_liquid_container | 明确允许盛装液体的对象 |
| is_filled | 存在一份液体；保留满／空的二值抽象 |
| contains_water / contains_tea / contains_coffee / contains_other_drink | 互斥内容种类；other_drink 不自动满足指定茶或咖啡 |
| contents_heated | 当前内容完成过加热；不是容器自身的 heated |
| tea_loaded / coffee_loaded | 原料确实装入目标；摆放原料包装不产生该结果 |
| ingredient_available | 原料包足够一次制作，装料后消耗该可用标记 |
| water_checked | 实际检查当前装有水的容器；清空／换水后失效 |
| watered | 声明的植物接收了水 |
| contains_noodles / noodles_prepared | 面杯有方便面内容，且已用热水完成抽象冲泡步骤 |

同一容器最多一种液体。空容器不能携带内容或内容加热标记，错误初态会被拒绝。
新液体属性传给普通 domain 也会报错，不会静默丢弃。

`heated` 仍表示食物／物品加热处理，不增加 cooked、生熟等级。contents_heated
针对当前内容：倒出、倒掉后清除，普通水补入后为 false。固体容器原有 heated
不会被补水清除，也不能代替 contents_heated。

每次倒水整份转移，目标必须为空且有盛液能力。模型不表示毫升、容积比、部分倒出、
液体混合、连续温度、冷却或夜间保温。冷热仅是已完成加热的抽象，不用于证明
具体温度、沸点或饮用安全温度。植物一次浇水消耗一份水，多目标可重新装水。
茶／咖啡原料是一次制作的抽象供给，不表示包装全部原料的真实体积。

## 动作与共享代码

`build_liquid_domain.py` 从普通 domain 生成可独立使用的完整 PDDL。
独立加入 fill_from_faucet、fill_device_with_water、pour_into、pour、
dispense_from_device；不再依赖普通 domain 中的同名占位动作。
通用导航、拿取、开关、邻接、固体加热等动作保持一致。
新增 heat_liquid_in_kettle、heat_liquid_on_stove、load_tea、load_coffee、
brew_tea、water_plant、prepare_instant_noodles、inspect_water_container。

power_on 保持“设备开启”的含义。电水壶加热动作检查壶内水和开机；炉上液体加热
检查容器实际在开启的烹饪表面。咖啡分配动作检查水、已装原料、开启的咖啡机和
设备上的空杯，得到咖啡及内容加热结果。可打开的原料包装必须先打开。

条件效果读取动作执行前的状态，全部删除／添加同时生效。因此倒水不会因先清空
源容器而漏传内容属性。共享回放器扩展了 when，仍拒绝数值效果和不支持的条件。
VAL 与 SceneGraphManager 的逐步回放需保持一致。

## 推理、评测与缓存

任务的 domain_id 由数据固定。普通任务可以省略该字段并使用 split manifest 的
默认 domain；已注册任务不能被全局配置切换到其他 domain。自定义旧数据集仍支持
显式配置 domain 路径。算法提交的动作不能改变任务所属 domain。

导出不含参考计划、参考目标和审查答案的推理输入：

```sh
ahat-benchmark export-inputs --dataset ahat-medium --output outputs/medium-inputs.json
```

导出文件包含每道任务的指令、scene、初始 problem、domain_id、domain_sha256，
以及按 ID 去重的完整 domain 文本。problem 使用空目标，不泄露参考目标。
外部算法应按任务选取 `domains[case.domain_id].pddl`，不能继续给全部任务传一个
固定 domain。Python 接口同样可用：

```python
from ahat_benchmark.domains import resolve_domain, domain_binding
path = resolve_domain(case.domain_id)
result = {"id": case.id, "plan": generated_plan, **domain_binding(case.domain_id)}
```

液体推理结果必须带正确的 domain ID/hash，否则评测拒绝并要求重新生成。
旧普通任务结果允许缺省绑定字段，但仍受数据、代码和协议指纹约束。VAL、回放、
裁判和汇总按同一任务映射选择 domain。汇总同时提供各 domain 的样本数和均分。

普通裁判提示词保持原字节；液体裁判使用独立四份提示词。D1 检查内容种类和
contents_heated；D2 看原料与场景声明；D3/D4 检查指令要求的制作阶段、方法与顺序。
评分权重不变。domain 映射、哈希和裁判规则均进入缓存签名。

现有外部实验的固定 domain 入口需接入上述导出/API；本修订不改写历史实验配置、
训练集或结果，也未重新运行各算法或真实 LLM 裁判。新液体输入必须重新推理。

## 参考结果与充分性

新 `liquid_reference` 明确区分结果断言和顺序阶段见证，不冒充仅靠末态即可证明
所有历史步骤的充分 goal，也不要求所有正确方案复制参考动作序列。
这些断言只用于离线参考检查，未送入模型或增加运行时硬评分门槛。
其中两道抽象 refreshment 题只验证饮品和摆放结果；不宣称证明 calming 的主观质量
或未声明的 fruit_bowl 内容。D3/D4 仍按原指令判断合理完成程度。

保留原有 18 个 reference_goal；没有把新的局部结果冒充完整充分目标写入该字段。
省略关键动作的反例分别记录“非法／结果不达标”与“遗漏指定阶段”，不混为一种证明。

## 隔离与恢复

[隔离文件](../benchmarks/liquid-v1/quarantined.json) 保留完整原始记录与原因。
[原始记录归档](../benchmarks/liquid-v1/originals.jsonl) 保留全部 41 道受影响原始记录，
包括隔离项。隔离不是删除，恢复需补齐场景或明确建模边界，并重新验证计划和裁判输入。

- 炉上烧水：缺炉具。
- 厨房烧水备茶：缺厨房水源，旧计划到浴缸取水；待明确场景修订后恢复。
- 室外菜地浇水：缺菜地，旧计划对 outdoor 房间倒水。
- 热水澡：缺热水供应／加热能力。
- 温水淋浴准备：缺温水来源及明确淋浴准备结果。
- 夜间保温：超出时间／冷却模型，旧计划也没有热水倒入过程。
- gourmet coffee：缺明确品质标准。

## 验证命令与证据

```sh
python scripts/build_liquid_domain.py --check
python scripts/repair_liquid.py
python -m unittest discover -s tests -v
python scripts/check_reference_plans.py --output docs/validation/liquid_v1_reference_checks.json
python scripts/audit_liquid.py
ahat-benchmark doctor
python examples/offline_demo.py
python scripts/check_release.py
```

安装包复核：289 条参考计划合法，52 组原目标／新增结果断言达成，483 步液体回放一致；
混合 domain 评测和无参考答案导出通过。完整完成记录见
[构建与安装验证](validation/liquid_v1_completion_checks.json)。

机器记录：[迁移清单](validation/liquid_v1_inventory.json)、
[液体参考／反例／回放](validation/liquid_v1_checks.json)、
[全部参考计划与既有目标](validation/liquid_v1_reference_checks.json)。
安装后的包可用 `python -I examples/check_installed_liquid.py` 验证全部参考计划、
液体回放和混合 domain 流程（本地模拟裁判）；CI 在独立安装环境执行此检查。

测试包含温热与成分传递、冷水反例、补水清除、原料消耗、错误接收对象、
炉上放置、条件效果读取前态、错配 domain、混合 domain 评测与参考信息不泄露。

## 完整 46 道审查映射

以下指令保持原文。`migrate` 表示液体 domain，`repair_equipment` 表示普通 domain
下的器具准备参考修复，`retain_base` 表示记录未变，`quarantine` 表示隔离。

| 稳定 ID | 原指令 | 处理 | 理由 |
| --- | --- | --- | --- |
| `6e590abe-0592-4a01-8de9-269cdd94fa89` | Could you fill my reusable water bottle and give it to the person on the stairs, please? | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `e9fed962-33e0-43ce-a5f0-ed603c0fe7d6` | Pick up the milk_tea_cup from sink in kitchen and deliver it to person at dining_table in dining_room. | retain_base | Ready-drink transport; existing object identity and spatial semantics suffice. |
| `c172ca4c-9f21-407c-87e8-350cbebfe340` | Can you fill the kettle with water for me? | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `3b49cc0c-0f25-45b2-8c9a-dbc4f957f693` | Can you fill the tub for my bath? | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `adb0fda4-53b4-418f-9154-39dd81aeaf78` | Go to the kitchen, open the refrigerator, pick up the bottle of bubble tea from inside the refrigerator, and bring it to the person in bedroom.001 and hand it over to them. | retain_base | Ready-drink transport; existing object identity and spatial semantics suffice. |
| `8b696fe2-79cb-412f-94a1-0c7cb5a5da84` | Hey, could you water the living room plant for me? | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `6f3adc5c-dc18-480e-852d-dcfca0387ba7` | I'm a bit parched — could you bring me a glass of water, please? | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `a9f01a35-f905-499e-ac54-007822d408c3` | On this chilly Inner Mongolian morning, please bring my teapot and an electric kettle to the bathroom so I can carefully pour and prepare hot water for myself and my spouse. | repair_equipment | Equipment preparation only; no automatic tea/hot-water completion requirement. |
| `ab270610-f68d-4ccf-8ced-455a237f8dc5` | Gather a glass from the kitchen, get ice from the garage fridge (represent as bottle for ice container), and take a juice bottle from the dining room, and set them up next to your laptop in the office. | retain_base | Ready-drink transport; existing object identity and spatial semantics suffice. |
| `8708a9fe-8ed0-49a8-9339-36f8d2a11611` | On a chilly winter morning, prepare the bathroom by pouring hot water from the kettle into a bowl placed on the bathroom counter, then bring a clean cup for rinsing. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `d3512291-7f63-46ff-8377-3bc926e7fc98` | Fill the electric_kettle on sink with water, power it on to heat, pour the hot water into the mug on dining_table, then hand the mug to person in bathroom. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `44a3890d-31fb-4a53-b9d2-1d7f2e22f686` | Pick up the reusable water bottle from desk in the bedroom, take it to the sink at sink_cabinet in the laundryroom, fill it with water from the faucet, then return and place it back on desk. | migrate | Declare faucet capability on the existing instruction-named sink cabinet. |
| `679dc145-55cf-4f32-9000-dad6d9a16d60` | Fetch the watering_can from the utility area, fill the watering_can at sink, and hand the filled watering_can to the person in utility_room. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `f8e914bb-3f3a-43de-8b8f-c86cbaf6894f` | Could you make a coffee and bring it to my friend in the game room? | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `c4eaedfe-58a6-4535-8817-5e6c30ef5ba0` | Fill the kettle with water from the sink and place it on the stove to heat. | quarantine | Instruction requires a stove; scene has no stove/cooking surface. Old plan used a powered kettle on an island. |
| `bd6d5204-77c2-4be5-bd70-9f60a25d6a9d` | Take the electric_kettle from the kitchen_cabinet to the kitchen_island, fill it with water at sink_cabinet, power it on to heat, then pour hot water into a mug on table. | migrate | Declare faucet capability on the existing instruction-named sink cabinet. |
| `83e9c29c-054d-4269-8bf4-d5ac26b8ccfd` | Go to the kitchen, fill the kettle with water from the faucet, and boil it to prepare tea. | quarantine | Kitchen boiling preparation has no kitchen water source in the scene; old reference filled from a bathroom bathtub. Restore after a documented scene repair. |
| `cd03b958-c5dc-40fe-9cc4-6d1b78e53241` | Fetch a small snack and a drink for the child. | retain_base | Ready-drink transport; existing object identity and spatial semantics suffice. |
| `1cdf223d-1597-4e0e-ab9f-c601b577dfab` | Bring your laptop and a notebook from your bedroom to the office for studying, grab a cup of hot tea from the kitchen, and also bring your watch from the office to keep track of your study breaks. | migrate | Instruction explicitly fetches ready hot tea: declare initial tea/heated contents instead of fabricating a brewing requirement. |
| `baebc10b-0942-4ab8-a948-b5ce3630af75` | Refill the student's reusable water bottle and place it in her bedroom so it's ready for her study session. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `184f5333-3807-406c-bec5-124adc3cd227` | Retrieve the portable induction stove and hot pot saucepan from kitchen_cabinet, place them on kitchen_island, fill the saucepan with water, and power on the stove. | migrate | Equipment preparation only: no request to put the saucepan on the stove or finish heating. |
| `8eaf1794-e3f0-4f38-aa7e-d6b77872d7a8` | On a chilly morning, power on the electric kettle in the kitchen and prepare a cup for green tea before your video calls. | repair_equipment | Equipment preparation only; no automatic tea/hot-water completion requirement. |
| `99c7a3e4-033a-4142-8cb9-9d2bd63c5748` | I'm cold and tired — can you make me a cup of tea and bring it out to the garage? | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `8a288187-e7a6-47a9-bfad-2543976de82e` | Go to the kitchen and fill the watering can with water from the sink, then water the plants in the living room. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `acba2bf0-ad1e-452e-b3f7-43af06ebfc81` | I'm filthy from work — can you run me a hot bath and bring my towel? | quarantine | Hot bath requires a declared hot-water source or bath-heating capability; neither is provided. |
| `cea31743-32c3-4f59-b07e-b12a71e840de` | Fill the kettle with water from the faucet and power it on to heat the water. | migrate | Instruction specifies filling and switching on to heat; do not require completed heating as an extra goal. |
| `23178c37-3b65-4dff-9eb5-3c5d1e985232` | Go to the kitchen, take the electric_kettle from the sink area, fill and power it to heat water, then pour the hot water into the instant_noodle_cup on the dining_table and bring a spoon. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `2cd06e0a-88a9-45a6-a5e3-a378199d6414` | Go to the kitchen, use the coffee machine to brew a cup of coffee into a mug, and place the mug on the kitchen island. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `6d1fc47f-358b-4bf5-b8ce-eb61f66d8fa0` | Prepare and deliver a warm drink to a person in another room. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `a6858c23-0cee-461d-bbf3-c9951bfbbda3` | Could you make me a cup of tea and bring it to my home office, please? | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `7f0a1344-6ce2-4860-8b0d-1d6de7219fdd` | Before a family dinner, arrange plates, spoons, and a casserole on the dining table and check if there is a pitcher of water (jug) present. | migrate | Instruction identifies a pitcher of water: declare its initial water contents and explicitly inspect it after setting the table. |
| `41eef001-7744-4656-bb14-84c8920b2fde` | At dusk, bring a vase and freshen it by filling it with water from the kitchen faucet, then place it back on the bedroom stool. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `12b30bd2-1470-4249-9b4c-080acc03c4eb` | Go to the kitchen, fill the coffee machine with water, load coffee grounds, brew a cup into the ceramic mug, and hand the mug to the person in the kitchen. | migrate | Declare faucet capability on the existing instruction-named sink cabinet. |
| `e78432e1-25fd-4476-8711-7da0d50bc88c` | The plants need a drink — can you fill the watering can and water my vegetable patch outside? | quarantine | Vegetable patch is absent; old reference poured into the outdoor room itself. A room cannot stand for an unspecified planting target. |
| `e2589b66-026b-4075-9525-3acdbf38e1f0` | Prepare bathing supplies and warm water in the bathroom for a post-work shower. | quarantine | Warm shower preparation lacks a declared warm-water supply and a clear shower-ready outcome; a filled wash basin is insufficient. |
| `4377c209-f70e-4cc9-a0d9-c09e1ffef3b9` | Could you fill the watering can and water my herbs on the coffee table, please? | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `c77c47ae-9d7a-4369-abbd-c305498e2aad` | Prepare a hot morning beverage and deliver it to the resident's bedroom. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `3a12822b-f774-4834-b9af-b741f2592c5e` | Could you make some hot tea and bring a cup to the person at the dining table? | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `079da0e5-422a-4fe4-afc5-e885f4e98453` | Set a candle holder and mooncakes on the dining room table, bring your favorite indie music album (CD) from the bedroom to the living room, and take a bottle of tea from the kitchen to enjoy. | retain_base | Ready-drink transport; existing object identity and spatial semantics suffice. |
| `9c120c15-b00a-4544-bafa-ffeece47d701` | On a cold winter day, pour hot water into a thermos bottle and place it on the bedroom chest of drawers so I can have warm water during the night. | quarantine | Night-time warmth/retention is outside the no-time/no-cooling model; old plan also lacks a hot-water pour. |
| `72d3763d-58b9-4f1f-befe-eed2fba16f6b` | Prepare a quick cup of instant noodles. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `f740c053-35da-470a-8628-e9291a9738cb` | Prepare a gourmet coffee and deliver it to the person in the bedroom. | quarantine | Gourmet quality has no operational criterion; ordinary coffee production cannot certify it. |
| `05f9fb16-de68-4fb8-8cc7-4ad1714f7f72` | Prepare a hot cup of coffee in the kitchen and deliver it to the bedroom nightstand. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `ca93f23c-c8c5-426f-81f5-4f7e51811dfc` | Refill a reusable water bottle and make it available in the kitchen. | migrate | Explicit container contents, legal processing and instruction-matched reference. |
| `ed9e36b8-03bb-43bb-a260-37bcc20d9f53` | Set up a calming morning refreshment | migrate | Minimal refreshment witness: clean drinking water served on the table; remove unrelated bath products. Subjective calming quality is not certified. |
| `3a5724ed-a1f5-4869-86ae-b1a21c969c6f` | Prepare and serve a light evening refreshment. | migrate | Final assertions cover the drink/service; do not certify the contents of an unannotated fruit bowl. |
