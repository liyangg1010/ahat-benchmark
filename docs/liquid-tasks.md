# 液体指令分类：liquid-pruning-v1 历史清单

以下保留去重阶段的分类依据。后续 liquid-v1 已将 32 道迁入液体 domain、隔离 7 道，
正式集合为 289 道。当前任务状态及完整 46 道审查映射见 [液体建模修订](liquid-domain.md)。
本页及 liquid_instruction_current.json 的“current”指去重阶段，不是液体建模后的任务集合。

2026-11-11，liquid-pruning-v1 后 benchmark 为 **296 道（easy 130 / medium 74 / open 92）**。液体相关指令共 **42 道、9 类**。

超过 10 道的四类各保留 6 道现有代表，合计删除 43 道近似变体。其余五类保持不变；不合并为更长的新指令，不更改存活任务的 scene、plan 或 reference_goal。

| 主类 | 精简前 | 当前 |
| --- | ---: | ---: |
| 常温水装填／补水／交付 | 26 | 6 |
| 现成饮料取用／搬运／摆放 | 13 | 6 |
| 热水／烧水／倒水与交付 | 16 | 6 |
| 茶的准备／冲泡 | 5 | 5 |
| 咖啡制作／分配 | 5 | 5 |
| 未指定种类的温热饮品 | 2 | 2 |
| 浇植物／花瓶补水及相关装水 | 12 | 6 |
| 沐浴／清洗用途的水 | 4 | 4 |
| 方便面准备／热水冲泡 | 2 | 2 |

## 对上一轮分类的纠正

此前 85 道清单误把“取蔬菜和肉准备火锅”归入热水类，遗漏真正要求“取电磁炉和锅、装水、开炉”的任务。错误来自按位置取记录时使用了 184 而非 176；本次按稳定 ID 纠正。两条原始 benchmark 记录都保留，分类修正本身不删除任务；纠正后精简前总数仍为 85。

- 移出液体清单：`d4e3362f-60d3-46cd-8638-8954f5a9602b` — Go to the kitchen and pick up the vegetables and meat from the refrigerator and kitchen cabinet to prepare a hot pot.
- 纳入热水设备准备类并保留：`184f5333-3807-406c-bec5-124adc3cd227` — Retrieve the portable induction stove and hot pot saucepan from kitchen_cabinet, place them on kitchen_island, fill the saucepan with water, and power on the stove.

旧 33 道是上轮烹饪审查的筛查子集，不是全部液体任务。完整旧清单保留历史记录，当前以 [当前机器清单](validation/liquid_instruction_current.json) 为准。

## 去重阶段全部原指令

### 常温水装填／补水／交付

| 稳定 ID | 原指令 |
| --- | --- |
| `6e590abe-0592-4a01-8de9-269cdd94fa89` | Could you fill my reusable water bottle and give it to the person on the stairs, please? |
| `c172ca4c-9f21-407c-87e8-350cbebfe340` | Can you fill the kettle with water for me? |
| `6f3adc5c-dc18-480e-852d-dcfca0387ba7` | I'm a bit parched — could you bring me a glass of water, please? |
| `44a3890d-31fb-4a53-b9d2-1d7f2e22f686` | Pick up the reusable water bottle from desk in the bedroom, take it to the sink at sink_cabinet in the laundryroom, fill it with water from the faucet, then return and place it back on desk. |
| `baebc10b-0942-4ab8-a948-b5ce3630af75` | Refill the student's reusable water bottle and place it in her bedroom so it's ready for her study session. |
| `ca93f23c-c8c5-426f-81f5-4f7e51811dfc` | Refill a reusable water bottle and make it available in the kitchen. |

### 现成饮料取用／搬运／摆放

| 稳定 ID | 原指令 |
| --- | --- |
| `e9fed962-33e0-43ce-a5f0-ed603c0fe7d6` | Pick up the milk_tea_cup from sink in kitchen and deliver it to person at dining_table in dining_room. |
| `adb0fda4-53b4-418f-9154-39dd81aeaf78` | Go to the kitchen, open the refrigerator, pick up the bottle of bubble tea from inside the refrigerator, and bring it to the person in bedroom.001 and hand it over to them. |
| `ab270610-f68d-4ccf-8ced-455a237f8dc5` | Gather a glass from the kitchen, get ice from the garage fridge (represent as bottle for ice container), and take a juice bottle from the dining room, and set them up next to your laptop in the office. |
| `cd03b958-c5dc-40fe-9cc4-6d1b78e53241` | Fetch a small snack and a drink for the child. |
| `1cdf223d-1597-4e0e-ab9f-c601b577dfab` | Bring your laptop and a notebook from your bedroom to the office for studying, grab a cup of hot tea from the kitchen, and also bring your watch from the office to keep track of your study breaks. |
| `079da0e5-422a-4fe4-afc5-e885f4e98453` | Set a candle holder and mooncakes on the dining room table, bring your favorite indie music album (CD) from the bedroom to the living room, and take a bottle of tea from the kitchen to enjoy. |

### 热水／烧水／倒水与交付

| 稳定 ID | 原指令 |
| --- | --- |
| `d3512291-7f63-46ff-8377-3bc926e7fc98` | Fill the electric_kettle on sink with water, power it on to heat, pour the hot water into the mug on dining_table, then hand the mug to person in bathroom. |
| `c4eaedfe-58a6-4535-8817-5e6c30ef5ba0` | Fill the kettle with water from the sink and place it on the stove to heat. |
| `bd6d5204-77c2-4be5-bd70-9f60a25d6a9d` | Take the electric_kettle from the kitchen_cabinet to the kitchen_island, fill it with water at sink_cabinet, power it on to heat, then pour hot water into a mug on table. |
| `184f5333-3807-406c-bec5-124adc3cd227` | Retrieve the portable induction stove and hot pot saucepan from kitchen_cabinet, place them on kitchen_island, fill the saucepan with water, and power on the stove. |
| `cea31743-32c3-4f59-b07e-b12a71e840de` | Fill the kettle with water from the faucet and power it on to heat the water. |
| `9c120c15-b00a-4544-bafa-ffeece47d701` | On a cold winter day, pour hot water into a thermos bottle and place it on the bedroom chest of drawers so I can have warm water during the night. |

### 茶的准备／冲泡

| 稳定 ID | 原指令 |
| --- | --- |
| `83e9c29c-054d-4269-8bf4-d5ac26b8ccfd` | Go to the kitchen, fill the kettle with water from the faucet, and boil it to prepare tea. |
| `8eaf1794-e3f0-4f38-aa7e-d6b77872d7a8` | On a chilly morning, power on the electric kettle in the kitchen and prepare a cup for green tea before your video calls. |
| `99c7a3e4-033a-4142-8cb9-9d2bd63c5748` | I'm cold and tired — can you make me a cup of tea and bring it out to the garage? |
| `a6858c23-0cee-461d-bbf3-c9951bfbbda3` | Could you make me a cup of tea and bring it to my home office, please? |
| `3a12822b-f774-4834-b9af-b741f2592c5e` | Could you make some hot tea and bring a cup to the person at the dining table? |

### 咖啡制作／分配

| 稳定 ID | 原指令 |
| --- | --- |
| `f8e914bb-3f3a-43de-8b8f-c86cbaf6894f` | Could you make a coffee and bring it to my friend in the game room? |
| `2cd06e0a-88a9-45a6-a5e3-a378199d6414` | Go to the kitchen, use the coffee machine to brew a cup of coffee into a mug, and place the mug on the kitchen island. |
| `12b30bd2-1470-4249-9b4c-080acc03c4eb` | Go to the kitchen, fill the coffee machine with water, load coffee grounds, brew a cup into the ceramic mug, and hand the mug to the person in the kitchen. |
| `f740c053-35da-470a-8628-e9291a9738cb` | Prepare a gourmet coffee and deliver it to the person in the bedroom. |
| `05f9fb16-de68-4fb8-8cc7-4ad1714f7f72` | Prepare a hot cup of coffee in the kitchen and deliver it to the bedroom nightstand. |

### 未指定种类的温热饮品

| 稳定 ID | 原指令 |
| --- | --- |
| `6d1fc47f-358b-4bf5-b8ce-eb61f66d8fa0` | Prepare and deliver a warm drink to a person in another room. |
| `c77c47ae-9d7a-4369-abbd-c305498e2aad` | Prepare a hot morning beverage and deliver it to the resident's bedroom. |

### 浇植物／花瓶补水及相关装水

| 稳定 ID | 原指令 |
| --- | --- |
| `8b696fe2-79cb-412f-94a1-0c7cb5a5da84` | Hey, could you water the living room plant for me? |
| `679dc145-55cf-4f32-9000-dad6d9a16d60` | Fetch the watering_can from the utility area, fill the watering_can at sink, and hand the filled watering_can to the person in utility_room. |
| `8a288187-e7a6-47a9-bfad-2543976de82e` | Go to the kitchen and fill the watering can with water from the sink, then water the plants in the living room. |
| `41eef001-7744-4656-bb14-84c8920b2fde` | At dusk, bring a vase and freshen it by filling it with water from the kitchen faucet, then place it back on the bedroom stool. |
| `e78432e1-25fd-4476-8711-7da0d50bc88c` | The plants need a drink — can you fill the watering can and water my vegetable patch outside? |
| `4377c209-f70e-4cc9-a0d9-c09e1ffef3b9` | Could you fill the watering can and water my herbs on the coffee table, please? |

### 沐浴／清洗用途的水

| 稳定 ID | 原指令 |
| --- | --- |
| `3b49cc0c-0f25-45b2-8c9a-dbc4f957f693` | Can you fill the tub for my bath? |
| `8708a9fe-8ed0-49a8-9339-36f8d2a11611` | On a chilly winter morning, prepare the bathroom by pouring hot water from the kettle into a bowl placed on the bathroom counter, then bring a clean cup for rinsing. |
| `acba2bf0-ad1e-452e-b3f7-43af06ebfc81` | I'm filthy from work — can you run me a hot bath and bring my towel? |
| `e2589b66-026b-4075-9525-3acdbf38e1f0` | Prepare bathing supplies and warm water in the bathroom for a post-work shower. |

### 方便面准备／热水冲泡

| 稳定 ID | 原指令 |
| --- | --- |
| `23178c37-3b65-4dff-9eb5-3c5d1e985232` | Go to the kitchen, take the electric_kettle from the sink area, fill and power it to heat water, then pour the hot water into the instant_noodle_cup on the dining_table and bring a spoon. |
| `72d3763d-58b9-4f1f-befe-eed2fba16f6b` | Prepare a quick cup of instant noodles. |

## 解释范围

- 类别是互斥主意图；加热、递送、位置、顺序、多目标、开容器等约束需额外逐题保留。
- 取现成饮料不自动要求制作；只准备器具、装水或开机不自动要求终态已经烧开。
- 单纯提到 coffee table、bath towel、reading glasses，搬空杯或取干方便面包装，不属于液体处理任务。
- 当前 is_filled 不区分水、茶、咖啡；fill/pour 不追踪液体温度或成分。保留原参考计划不等于证明这些语义已解决。
- 本次只精简任务集和纠正分类。完整删留映射、相似度依据及保留约束见 [液体去重审查](liquid-pruning.md)。

## 提交 c14898f 时的建模范围审计（历史）

上述 42 道是指令分类，不是液体动作迁移的完整范围。在 296 道参考计划中，
`fill_from_faucet` 被 33 道使用（清单内 30、清单外 3），`pour_into` 被 15 道使用
（清单内 14、清单外 1），`fill_device_with_water` 和 `dispense_from_device`
各被清单内 3 道使用。清单外需要一并审查的任务为：

- `a9f01a35-f905-499e-ac54-007822d408c3`：将茶壶、电水壶带到浴室，为自己和配偶准备热水。
- `ed9e36b8-03bb-43bb-a260-37bcc20d9f53`：Set up a calming morning refreshment。
- `3a5724ed-a1f5-4869-86ae-b1a21c969c6f`：Prepare and serve a light evening refreshment。

当时缺口包括液体种类、加热完成、倒出时属性传递、原料装载与制作，以及部分
参考计划未遵循指定设备或位置。计划合法性不能证明这些自然语言要求已满足。
当时拟新增液体专用 domain 和任务级固定映射，保留普通 domain，并隔离无法
可靠支持的任务；此处记录范围和限制，不表示该扩展已经完成。
