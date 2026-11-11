# 液体任务去重审查 — liquid-pruning-v1

范围：审查四个超过 10 道的类别共 67 条记录，保留 24 道，删除 43 道。当前任务数 339→296；easy 149→130、medium 98→74、open 92 不变。所有存活原始 JSONL 行、字段及顺序不变。

按用户要求，以指令目标和必要步骤为主，结合 scene 初始状态、位置关系、取物访问方式和参考计划结构审查。采用现有代表，不拼接指令。相似措辞并不代表 scene 相同；本次接受减少部分对象、房间与布局变体以限制同类数量。

## 保留的不同约束

- 常温水：瓶装交人、只装水壶、柜内取杯的隐含饮水请求、装水后返回原处、在卧室备好、在厨房备好。
- 现成饮料：台面取用交人、冰箱取用交人、明确 next_to 的多物收集、零食加饮料、学习用品加热茶、节庆多目的地组合。
- 热水：装水／开机／分杯／交人、指定炉上加热、柜内取壶及指定中转、移动炉具和锅的准备、只装水开壶、保温瓶及指定存放。
- 植物用水：单株室内、多株与中途补水、仅装满浇水壶交人、花瓶装水返回、室外菜地、柜内取壶浇香草。

## 所有删留与代表映射

索引为精简前 339 条快照从 0 开始的位置。代表映射说明相近能力覆盖，不表示原指令与代表逻辑等价。

### 常温水装填／补水／交付

| 原索引 | 稳定 ID | 原指令 | 处理与覆盖参照 |
| --- | --- | --- | --- |
| 3 | `6e590abe-0592-4a01-8de9-269cdd94fa89` | Could you fill my reusable water bottle and give it to the person on the stairs, please? | 保留：瓶装补水并交人，跨房间到楼梯 |
| 10 | `c172ca4c-9f21-407c-87e8-350cbebfe340` | Can you fill the kettle with water for me? | 保留：只装水壶，不要求加热；取壶需要开容器 |
| 15 | `2ac616dc-d786-496d-8cef-59fdbd6ea754` | Could you bring a glass of water to my spouse in the bathroom? | 删除；参照 `6f3adc5c-dc18-480e-852d-dcfca0387ba7` |
| 19 | `359c9091-abba-4695-aeb4-6ff68340f9dd` | I'm thirsty — can you grab me a glass of water? | 删除；参照 `6f3adc5c-dc18-480e-852d-dcfca0387ba7` |
| 26 | `57113a26-952d-4dc6-9617-3ca5bea35246` | Provide a filled reusable water bottle to the teenager in her bedroom. | 删除；参照 `6e590abe-0592-4a01-8de9-269cdd94fa89` |
| 49 | `d96cb594-897e-4b47-83f3-e8b16bd34998` | Bring a drink of water to the person in the dining room. | 删除；参照 `6f3adc5c-dc18-480e-852d-dcfca0387ba7` |
| 74 | `fa727bbc-9c09-420b-a616-66e6e4a6246c` | Provide a cup of drinking water to the child in her bedroom. | 删除；参照 `baebc10b-0942-4ab8-a948-b5ce3630af75` |
| 79 | `78caec8e-5332-4cd0-82f1-0550a430df58` | Could you bring me a glass of water, please? | 删除；参照 `6f3adc5c-dc18-480e-852d-dcfca0387ba7` |
| 80 | `645b5311-11d9-4511-bfd5-5b933fe2b482` | Provide a glass of water to the resident in the living room. | 删除；参照 `6f3adc5c-dc18-480e-852d-dcfca0387ba7` |
| 83 | `f3d312f5-1ca9-4745-9c2c-98ed6e10022c` | Provide a filled reusable water bottle to the person in the bathroom. | 删除；参照 `6e590abe-0592-4a01-8de9-269cdd94fa89` |
| 119 | `6a49e355-517f-41cd-a381-99e024419125` | Go to the kitchen, take a drinking glass from kitchen_cabinet, fill it with water from the faucet, and hand the filled glass to person in the entryway. | 删除；参照 `6f3adc5c-dc18-480e-852d-dcfca0387ba7` |
| 123 | `6f3adc5c-dc18-480e-852d-dcfca0387ba7` | I'm a bit parched — could you bring me a glass of water, please? | 保留：隐含需求的玻璃杯饮水；取杯需要开容器 |
| 143 | `864fcabb-2a56-4efb-9f4b-1d7cb84136c1` | Refill the user's reusable water bottle and deliver it to them. | 删除；参照 `6e590abe-0592-4a01-8de9-269cdd94fa89` |
| 146 | `d3e7a640-74c8-4c97-a936-41682c7b59c6` | Go to the kitchen, get the mug from bench, fill it at sink, and bring the filled mug to person in bathroom and hand it over. | 删除；参照 `6f3adc5c-dc18-480e-852d-dcfca0387ba7` |
| 147 | `d0340668-e518-4aa5-b935-b1a877b25952` | Take a glass from the dining table, fill it with water at the kitchen sink, and hand the filled glass to person in empty_room. | 删除；参照 `6f3adc5c-dc18-480e-852d-dcfca0387ba7` |
| 148 | `fccd6938-4f5d-4bfe-a8de-087e895319dd` | Pick up the reusable water bottle from the dining_table, walk to sink in kitchen to fill it with water, then hand the filled water bottle to person at dining_table. | 删除；参照 `6e590abe-0592-4a01-8de9-269cdd94fa89` |
| 149 | `3bc23367-bbd0-479e-be4b-c16413664743` | Go to kitchen, pick up the teapot from sink, fill it from the faucet, and hand the filled teapot to person in bedroom. | 删除；参照 `c172ca4c-9f21-407c-87e8-350cbebfe340` |
| 152 | `08fefdd7-7df6-488d-bafe-c71dea3b4b2e` | Refill a reusable water bottle and deliver it to the resident. | 删除；参照 `6e590abe-0592-4a01-8de9-269cdd94fa89` |
| 154 | `44a3890d-31fb-4a53-b9d2-1d7f2e22f686` | Pick up the reusable water bottle from desk in the bedroom, take it to the sink at sink_cabinet in the laundryroom, fill it with water from the faucet, then return and place it back on desk. | 保留：明确装水后返回原桌面 |
| 158 | `175a4f28-3023-4e88-8af4-d73c19a16be0` | Refill a drinking container with tap water and deliver it to the person in the corridor. | 删除；参照 `6e590abe-0592-4a01-8de9-269cdd94fa89` |
| 166 | `5804e2c6-9308-4d09-92e8-dbefd7553fec` | Ensure the user's reusable water bottle is filled with water and ready for them to take to work. | 删除；参照 `6e590abe-0592-4a01-8de9-269cdd94fa89` |
| 167 | `d167567d-7887-4626-9cd7-33ba43257944` | Could you fill a cup with water and bring it to my room, please? | 删除；参照 `baebc10b-0942-4ab8-a948-b5ce3630af75` |
| 169 | `451288d0-761d-4576-bf3b-556307ddb7ae` | Fill a plastic cup with water at sink in kitchen and bring it to the child in bedroom, handing it to her. | 删除；参照 `6f3adc5c-dc18-480e-852d-dcfca0387ba7` |
| 175 | `baebc10b-0942-4ab8-a948-b5ce3630af75` | Refill the student's reusable water bottle and place it in her bedroom so it's ready for her study session. | 保留：装水并在卧室备好，不要求交到手中 |
| 203 | `2b60f5c9-31ae-435f-85a2-dbd81109a14b` | Pick up the reusable_water_bottle from dining_table, take it to sink in kitchen, fill it with water, and hand it to person. | 删除；参照 `6e590abe-0592-4a01-8de9-269cdd94fa89` |
| 235 | `ca93f23c-c8c5-426f-81f5-4f7e51811dfc` | Refill a reusable water bottle and make it available in the kitchen. | 保留：装水并在厨房备好 |

### 现成饮料取用／搬运／摆放

| 原索引 | 稳定 ID | 原指令 | 处理与覆盖参照 |
| --- | --- | --- | --- |
| 8 | `e9fed962-33e0-43ce-a5f0-ed603c0fe7d6` | Pick up the milk_tea_cup from sink in kitchen and deliver it to person at dining_table in dining_room. | 保留：台面现成饮料交人 |
| 24 | `adb0fda4-53b4-418f-9154-39dd81aeaf78` | Go to the kitchen, open the refrigerator, pick up the bottle of bubble tea from inside the refrigerator, and bring it to the person in bedroom.001 and hand it over to them. | 保留：开冰箱取瓶装饮料交人 |
| 42 | `0aa92a27-e544-4cf1-bd80-9db63bdbb474` | Deliver a requested beverage from the kitchen area to the person in the bathroom. | 删除；参照 `e9fed962-33e0-43ce-a5f0-ed603c0fe7d6` |
| 52 | `d6e3d05d-410c-4c8e-87a9-27be573b76f7` | Deliver a drink to the person in the bedroom to quench their thirst. | 删除；参照 `e9fed962-33e0-43ce-a5f0-ed603c0fe7d6` |
| 66 | `49d3a7f5-d089-4f5b-a8be-c34a70aecc35` | Go to the kitchen, open refrigerator, take the bottle_of_milk_tea from refrigerator and bring it to person in the hallway, handing it to them. | 删除；参照 `adb0fda4-53b4-418f-9154-39dd81aeaf78` |
| 72 | `010b3761-72e6-444f-bbc8-0bf4c55c077c` | Hey, I'm thirsty—can you grab me a water from the fridge? | 删除；参照 `adb0fda4-53b4-418f-9154-39dd81aeaf78` |
| 84 | `6cd2dba6-1f1e-4003-b231-13001bc37ec1` | Retrieve a recently-delivered drink and bring it to the user. | 删除；参照 `e9fed962-33e0-43ce-a5f0-ed603c0fe7d6` |
| 94 | `facf09d9-cf5d-459f-8344-4d0f6a07adf7` | Hey, can you grab me a milk tea from the kitchen and bring it to my room? | 删除；参照 `e9fed962-33e0-43ce-a5f0-ed603c0fe7d6` |
| 98 | `a502dd4d-6f7e-43a9-8eb6-1157d760a621` | Go to the kitchen, open refrigerator, pick up a bottle of mango juice from inside, and bring it to the person in the bedroom, handing it to her. | 删除；参照 `adb0fda4-53b4-418f-9154-39dd81aeaf78` |
| 139 | `ab270610-f68d-4ccf-8ced-455a237f8dc5` | Gather a glass from the kitchen, get ice from the garage fridge (represent as bottle for ice container), and take a juice bottle from the dining room, and set them up next to your laptop in the office. | 保留：多房间收集饮品／冰／杯，明确 next_to |
| 171 | `cd03b958-c5dc-40fe-9cc4-6d1b78e53241` | Fetch a small snack and a drink for the child. | 保留：零食与饮料两项交付 |
| 172 | `1cdf223d-1597-4e0e-ab9f-c601b577dfab` | Bring your laptop and a notebook from your bedroom to the office for studying, grab a cup of hot tea from the kitchen, and also bring your watch from the office to keep track of your study breaks. | 保留：学习用品与现成热茶组合 |
| 221 | `079da0e5-422a-4fe4-afc5-e885f4e98453` | Set a candle holder and mooncakes on the dining room table, bring your favorite indie music album (CD) from the bedroom to the living room, and take a bottle of tea from the kitchen to enjoy. | 保留：多目的地节庆布置与瓶装茶组合 |

### 热水／烧水／倒水与交付

| 原索引 | 稳定 ID | 原指令 | 处理与覆盖参照 |
| --- | --- | --- | --- |
| 144 | `b5839f9a-eb34-4d4d-ad2b-5665e8b9c5ef` | Prepare a cup of boiled water and deliver it to the user. | 删除；参照 `d3512291-7f63-46ff-8377-3bc926e7fc98` |
| 150 | `d3512291-7f63-46ff-8377-3bc926e7fc98` | Fill the electric_kettle on sink with water, power it on to heat, pour the hot water into the mug on dining_table, then hand the mug to person in bathroom. | 保留：装水→开机→倒入杯→交人完整流程 |
| 160 | `63771138-ea77-46d7-98ef-730f7fc06a7d` | Could you make me a cup of hot water and bring it down here? | 删除；参照 `d3512291-7f63-46ff-8377-3bc926e7fc98` |
| 161 | `c4eaedfe-58a6-4535-8817-5e6c30ef5ba0` | Fill the kettle with water from the sink and place it on the stove to heat. | 保留：水壶放到炉上加热的指定方法 |
| 162 | `75fa2d06-2278-45fa-a9d1-fa3cdb6e3da8` | Prepare a cup of hot water and bring it to the person. | 删除；参照 `d3512291-7f63-46ff-8377-3bc926e7fc98` |
| 163 | `0127af55-e737-4be4-8fda-ea2efaf69461` | Prepare a cup of hot water for the user. | 删除；参照 `d3512291-7f63-46ff-8377-3bc926e7fc98` |
| 164 | `bd6d5204-77c2-4be5-bd70-9f60a25d6a9d` | Take the electric_kettle from the kitchen_cabinet to the kitchen_island, fill it with water at sink_cabinet, power it on to heat, then pour hot water into a mug on table. | 保留：从柜内取电水壶、指定中转位置并倒入桌上杯 |
| 170 | `e066d3a7-c73c-464d-b0a5-a28ce4b7939d` | Fill the electric kettle at sink (kitchen) with water, power it on to boil, pour the boiled water into a cup on dining_table, and deliver the cup to person in bedroom. | 删除；参照 `d3512291-7f63-46ff-8377-3bc926e7fc98` |
| 177 | `3add086d-6d85-470a-a351-bdab3456e295` | I need my hot water — please make me a cup and bring it here. | 删除；参照 `d3512291-7f63-46ff-8377-3bc926e7fc98` |
| 176 | `184f5333-3807-406c-bec5-124adc3cd227` | Retrieve the portable induction stove and hot pot saucepan from kitchen_cabinet, place them on kitchen_island, fill the saucepan with water, and power on the stove. | 保留：取移动电磁炉和锅、装水开炉的准备任务 |
| 190 | `cea31743-32c3-4f59-b07e-b12a71e840de` | Fill the kettle with water from the faucet and power it on to heat the water. | 保留：只装水并给水壶通电，不要求分杯交付 |
| 196 | `f2c44280-76ff-449b-895e-2d78cdfc6b28` | Go to the kitchen, fill and switch on the electric kettle, pour hot water into the ceramic mug on the kitchen island, and hand the mug to the person in the kitchen. | 删除；参照 `d3512291-7f63-46ff-8377-3bc926e7fc98` |
| 220 | `bd621dea-7022-4f49-ae0f-3018da6b2f12` | Fill the kettle with water from the faucet and then power it on to heat the water. | 删除；参照 `cea31743-32c3-4f59-b07e-b12a71e840de` |
| 223 | `7728b3b9-4cd2-4586-8dd0-6f70bdea8e22` | Pick up the electric kettle and a mug from the dining table, fill the kettle at the kitchen sink, power it on to heat the water, pour hot water into the mug, and bring the mug to the person in bathroom. | 删除；参照 `d3512291-7f63-46ff-8377-3bc926e7fc98` |
| 225 | `9c120c15-b00a-4544-bafa-ffeece47d701` | On a cold winter day, pour hot water into a thermos bottle and place it on the bedroom chest of drawers so I can have warm water during the night. | 保留：热水装保温瓶、指定存放位置及保温用途 |
| 229 | `4a58251b-b8bf-4f05-ad45-7947bf665031` | Could you please make me a warm cup of boiled water and bring it here? | 删除；参照 `d3512291-7f63-46ff-8377-3bc926e7fc98` |

### 浇植物／花瓶补水及相关装水

| 原索引 | 稳定 ID | 原指令 | 处理与覆盖参照 |
| --- | --- | --- | --- |
| 71 | `da7b09cd-9be9-443b-9d30-5818df18a3ed` | Water an indoor plant in the apartment. | 删除；参照 `8b696fe2-79cb-412f-94a1-0c7cb5a5da84` |
| 88 | `45c7ef7c-cbbe-46a5-b464-d161cb6da953` | Maintain the indoor plant by watering it. | 删除；参照 `8b696fe2-79cb-412f-94a1-0c7cb5a5da84` |
| 106 | `177ac7f6-d696-4581-9f68-9d075052f1cf` | Hey, could you water the plant on the table in the living room? It's getting thirsty. | 删除；参照 `8b696fe2-79cb-412f-94a1-0c7cb5a5da84` |
| 117 | `8b696fe2-79cb-412f-94a1-0c7cb5a5da84` | Hey, could you water the living room plant for me? | 保留：单株室内植物浇水 |
| 156 | `679dc145-55cf-4f32-9000-dad6d9a16d60` | Fetch the watering_can from the utility area, fill the watering_can at sink, and hand the filled watering_can to the person in utility_room. | 保留：仅装满浇水壶交人 |
| 157 | `5ae5b97c-620f-400b-b14a-3ad0fa6fcae9` | Pick up the watering_can from bench, fill it at sink in the kitchen, then pour water into vase and vase in living_room. | 删除；参照 `8a288187-e7a6-47a9-bfad-2543976de82e` |
| 165 | `7ca9b7af-487b-4dde-8c11-3dbc7c7af671` | Fill a watering can at the kitchen sink and use it to water the potted plant located on the vase in the playroom (vase in playroom). | 删除；参照 `8b696fe2-79cb-412f-94a1-0c7cb5a5da84` |
| 180 | `8a288187-e7a6-47a9-bfad-2543976de82e` | Go to the kitchen and fill the watering can with water from the sink, then water the plants in the living room. | 保留：多株植物，需中途重新装水 |
| 194 | `3bc29099-3549-4cbe-8009-9a21718bf60e` | Fill the watering_can at sink and pour water into vase in bathroom to water the plant. | 删除；参照 `8b696fe2-79cb-412f-94a1-0c7cb5a5da84` |
| 206 | `41eef001-7744-4656-bb14-84c8920b2fde` | At dusk, bring a vase and freshen it by filling it with water from the kitchen faucet, then place it back on the bedroom stool. | 保留：花瓶装水后放回指定位置 |
| 209 | `e78432e1-25fd-4476-8711-7da0d50bc88c` | The plants need a drink — can you fill the watering can and water my vegetable patch outside? | 保留：室外菜地用水 |
| 216 | `4377c209-f70e-4cc9-a0d9-c09e1ffef3b9` | Could you fill the watering can and water my herbs on the coffee table, please? | 保留：香草定向浇水，取壶需开容器 |

## 相似度依据与取舍

以“Fill the kettle ... and [then] power it on ...”两道为例，规范为小写后的字符序列相似度为 96.9%，动作名序列完全相同，但完整 scene 节点重合率仅约 0.34%。它们是语义／流程近似，不是同一 scene 的复制。

机器清单对每个删除项记录与保留代表的字符序列比率、完整节点 Jaccard、规范化关系边 Jaccard 及动作名序列是否相同。这些指标用于描述证据，不作为自动阈值，也不是语义嵌入分数。节点比较保留名称、类别与全部属性，因此不同命名场景可能数值很低。

在 6 道限制下，部分原指令细节只得到近似覆盖：饮料品种、指定房间、杯／瓶／茶壶变体、热水 versus boiled water 等并非全都等价。保留多目标、返回原处、容器访问、设备方法和明确 next_to 等结构差异；原始删项完整记录仍在此前快照／溯源中可追查。

保留参考并不认证自然语言完成：例如指定炉上加热的旧计划仍开水壶而非满足指定炉上方法，部分指定取水位置或温度要求也未被旧计划证明。当前液体成分和热传递建模缺口不因精简消失，本次不改写这些参考。

## 同步与验证

- easy 1.6.0→1.7.0，medium 1.5.0→1.6.0，open 保持 1.7.0；domain/rubric 不变。
- 全部 18 组参考目标保留，包括 11 道显式邻接和全部处理参考；两人／群体份量数据保留。
- `scripts/prune_liquid_cases.py` 按稳定 ID 和记录哈希执行；写入前检查来源哈希、代表存在、无部分删除、受保护目标和数量，重复执行不改数据。
- 历史修订和旧分类清单保留；烹饪审计只额外排除明确记录的液体删项，其他任务缺失仍报错。
- 采用新任务 ID 集和新评测输出目录；以前的 339/355/348 题成绩不直接与 296 题均分比较。

证据：[完整审查清单](validation/liquid_pruning_inventory.json)、[当前分类](validation/liquid_instruction_current.json)、[迁移检查](validation/liquid_pruning_migration_checks.json)、[参考检查](validation/liquid_pruning_reference_checks.json)、[目标审计](validation/liquid_pruning_goal_checks.json)。未运行真实裁判或对外发布。
