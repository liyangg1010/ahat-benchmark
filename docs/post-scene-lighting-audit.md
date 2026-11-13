# scene-lighting-v1 后续调查

后续状态：第 1 项水瓶问题已按 [bottle-refill-v1](bottle-refill.md) 修复并去重，
四道保留两道，当前正式任务数为 287。第 2 项咖啡任务已按用户选择将盒子改为直接可用的
胶囊原料，删除开盒及多余导航，保留先开柜再取料；见 [FIX-019](repair-log.md#fix-019咖啡胶囊原料与参考计划简化)。
第 4 项人物位置转换已按 [FIX-020](repair-log.md#fix-020人物位置从-scene-到-pddl-的转换)
修复，61 道场景的位置边现在生成 person_at，任务数据和 domain 未变。
第 5 项已按 [FIX-021](repair-log.md#fix-021普通-domain-移除液体制作与转移动作)
从普通 domain 删除五个液体动作，液体 domain 保持原字节。
第 3 项已按 [type-hierarchy-v1](domain-types.md) 修复：两个 domain 和全部 287 个
problem 均经 pddl 0.4.6 独立解析通过，参考与全量回放通过。
通用外层容器可访问性、液体不变量一致性及空间防环三项模型问题，
已于 2026-11-12 按用户决定统一记录为暂缓处理，不列入当前修复范围。
当前 287 道正式任务及参考计划未发现触发这三项问题；下文保留调查时证据。

## 当前决定：三项模型问题暂缓

用户判断这三项不会影响当前任务，要求保留记录、暂不修复。依据当前验证结果，
287 条参考合法、3,985 步 scene/PDDL 回放一致；此决定限定于当前任务范围，
不表示已消除 domain 中的构造反例，也不保证任意生成计划都不触发。

| 问题 | 保留的问题记录 | 当前任务依据 | 状态 |
| --- | --- | --- | --- |
| 外层关闭容器访问约束不完整 | 可能隔着关闭柜门操作内部物体；需要按动作区分直接接触与设备内部处理 | 已发现的咖啡实例均已修正，当前参考未发现继续触发 | 暂缓，不修改 domain |
| 液体动作与 scene 不变量不完全一致 | 同容器先泡面再泡茶可被 VAL 接受，但 scene 校验拒绝末态 | 当前同时声明茶原料与方便面的正式场景为 0，参考未触发 | 暂缓，不修改液体动作或校验 |
| 空间关系可能形成环 | 容器可被放进自己的后代，缺少任意层级的 on/in 防环约束 | 已有构造反例，未发现正式参考产生环 | 继续暂缓，不实施派生谓词方案 |

保留既有反例与设计建议。以后新增相关场景、扩展任务范围或实际观察到生成计划触发时，
再复查是否需要恢复修复；本决定不改变任务数据、参考计划、评测口径或已隔离任务状态。

## 历史调查记录

2026-11-12。仅调查，未修改 domain、评测代码、任务或参考计划。
调查对象为当前 289 道正式任务及两个 `scene-lighting-v1` domain。
[机器证据](validation/post_scene_lighting_audit.json)记录当前数据／domain 指纹、
受影响任务 ID、独立解析器结果及原生 VAL 反例。

最近修复的通过基线仍是 102 项测试、289 条合法参考、18 个既有目标及
3,997 步参考回放一致。本轮没有重复整套测试，而是检查基线未覆盖的动作组合、
实际前序约束及独立 PDDL 解析兼容性。参考可执行和结果可达并不证明动作模型完整。

## 1. 四道参考计划向关闭的水瓶注水

以下任务的 reusable_water_bottle 均声明 `can_be_opened=true`，没有 `is_open=true`。
参考计划没有打开瓶子就调用 fill_from_faucet；真实 VAL 判合法，并能同时满足
`contains_water(bottle)` 与 `not is_open(bottle)`。

| 任务 ID | 指令 |
| --- | --- |
| `6e590abe-0592-4a01-8de9-269cdd94fa89` | Could you fill my reusable water bottle and give it to the person on the stairs, please? |
| `44a3890d-31fb-4a53-b9d2-1d7f2e22f686` | Pick up the reusable water bottle from desk in the bedroom, take it to the sink at sink_cabinet in the laundryroom, fill it with water from the faucet, then return and place it back on desk. |
| `baebc10b-0942-4ab8-a948-b5ce3630af75` | Refill the student's reusable water bottle and place it in her bedroom so it's ready for her study session. |
| `ca93f23c-c8c5-426f-81f5-4f7e51811dfc` | Refill a reusable water bottle and make it available in the kitchen. |

这与外层柜门访问是两种约束：即使瓶子已拿到水槽，瓶子自身的开闭状态仍被忽略。
当前没有另行声明可在瓶盖关闭时注水的独立开口。
建议明确带盖容器的注水／倒出规则，对需要打开的容器检查 is_open；
按现有 open 的 handempty 要求，在拿起瓶子之前打开，随后验证参考计划及结果。
是否要求最终盖好应依据指令或明确的容器操作策略，不自动增加新任务目标。

## 2. 另一道咖啡参考先开柜内盒子，再开柜门

任务 `05f9fb16-de68-4fb8-8cc7-4ad1714f7f72`：
“Prepare a hot cup of coffee in the kitchen and deliver it to the bedroom nightstand.”

coffee_pod_box_44 在关闭的 kitchen_cabinet_84 内。参考第 9 步先
`open coffee_pod_box_44`，第 11 步才 `open kitchen_cabinet_84`。
原计划经 VAL 判 valid；前九步确实达到“盒子已打开、柜门未打开”的状态。
本轮将检查范围从 pick/pour 扩大到 open、power、light、装料、制作等目标操作，
在所有参考中检出这一处关闭外层容器的访问问题。

它不属于上一轮两台咖啡机的位置错误，也不是新修复引入；原始检查范围没有覆盖 open。
建议参考先开柜门，再接近并打开胶囊盒；通用目标可访问性约束仍需独立设计。
不应把微波炉内部加热之类有意要求关闭设备的过程直接套成“所有物体都必须开放”。

## 3. PDDL 类型声明不兼容标准解析器

两个 domain 都重新声明了 `object - physobj`，将 PDDL 内置根类型名 object 当成
小物品类型使用。环境中独立解析器 **pddl 0.4.6** 的 `pddl.parse_domain(...)`
均在该处抛出 UnexpectedToken（OBJECT）。这已证明至少一种外部解析器不兼容，
不是证明所有规划器失败；当前自带 VAL 仍接受现有参考计划。

同时，开头 `item agent - item` 按 typed-list 语法会把 item 和 agent 都声明为
item 的子类型，即出现 `item -> item` 的自身继承。本项目解析器实际输出也如此。
这与暂缓的 on/in 空间包含环不同，是类型声明问题。

建议保留内置 object 根类型，给现有小物品类型换一个独立名称，并显式声明
`item - object`；同步 scene 分类→PDDL 类型映射、动作／谓词签名及容器父类型。
需要验证 VAL、Python 和外部规划器的类型一致性，并更新两个 domain 的指纹。

后续具体方案（已按 type-hierarchy-v1 实施，以下保留设计与验证要求）：

```lisp
(:types
  item - object
  agent location - item
  person physobj - location
  room furniture device small_object - physobj
  container - small_object)
```

保留 PDDL 内置根类型 object，将现有小物品类型改为 small_object；同步所有
动作／谓词中原本表示小物品的类型签名，以及 SceneGraphManager 和其他导出入口的
objects→small_object 映射。scene JSON 的 objects 分类和节点业务 type、对象名称、
指令及计划动作参数不必改名。必须审查根类型默认值与子类型判断，不能全局替换 object 字符串。
重新生成液体 domain，并核验两种 domain 的类型图无环、独立解析器接受、非法参数仍被拒绝、
287 条参考及目标可达、scene/PDDL 回放一致；现有反例仅证明类型节兼容问题，
不能保证修完类型后外部解析器不会暴露其他语法兼容点。

## 4. 61 个场景的人物位置没有进入 PDDL

279 个场景含人物；其中 61 个只有 links 中的 `person in room`，没有
`person.location`。SceneGraphManager 在提取 in links 时跳过 person，随后只从
location 字段生成 person_at，因此这 61 个场景的 PDDL 没有对应人物位置。
D2 与机器人房间推导可以读取 links，D1 初态／末态则缺少该信息。

这 61 条参考计划均未调用 hand_over_to_person，不能据此声称存在 61 条交付失败
或评分错误。它是当前正式数据中的信息损失，优先级低于上面的实际操作流程问题。
建议统一人的位置来源：location 缺省时从唯一合法位置边补充；两者同时存在时核对
一致性，同时保留精确位置与房间归属的区别。

## 5. 普通 domain 仍允许非容器装水

普通 domain 的 fill_from_faucet 不检查盛液能力。真实 VAL 接受：

```lisp
; 手持 laptop_1，位于有水龙头的 sink_1。
(fill_from_faucet agent_0 laptop_1 sink_1)
; 结果：(is_filled laptop_1)
```

普通 domain 的 pour_into 等仍保留类似宽松规则；液体 domain 已有
is_liquid_container 检查。当前 **257 条普通参考计划中没有使用这五个液体动作**
（fill_from_faucet、fill_device_with_water、dispense_from_device、pour_into、pour）。
这是算法生成候选计划时仍能利用的旧 domain 漏洞，不是已发现的参考计划失败。
可考虑从普通 domain 移除未使用的制作／转移液体动作，或保留动作并补能力检查；
需要明确自定义任务的兼容策略，不能直接把它当作本轮已批准修改。

## 6. 液体动作尚未保持全部 scene 不变量

用合法初态构造：面杯含热水和方便面、机器人持有可用茶原料。
先 load_tea、放下原料，prepare_instant_noodles，再 brew_tea。
VAL 接受整条计划，末态同时存在 noodles_prepared 和 contains_tea，contains_water 被删除。
scene 回放却因 `Prepared noodles lack hot water` 抛错。

原因是 brew_tea 改变液体种类但没有清除／限制依赖水状态的 noodles_prepared，
与 validate_liquid_scene 的不变量冲突。建议统一语义：限制这类制作组合，
或在内容变化时同步清理失效的制作标记；不要单纯删除 scene 校验来隐藏不一致。

当前没有正式场景同时声明 tea_supply 与 contains_noodles，此反例未在现有参考
中出现。它证明的是对合法扩展场景的模型闭合性问题，不能扩写成当前全部液体任务失败。

## 历史建议顺序及当前暂缓状态

原调查建议优先处理闭瓶注水、咖啡盒顺序、类型声明、人物位置及普通液体动作；
这些项目现已修复。剩余三项模型问题按上方决定统一暂缓，不再沿用旧修复优先级。
尚未测试真实 LLM 对这些反例的评分，未测量算法排名影响。

PDDL 防环仍按用户要求暂缓，既有问题和派生谓词方案保留于
[上一轮修复文档](scene-lighting.md)。容量、连续温度、冷却、混合及主观任务质量等
已声明的抽象边界，也未因为本轮调查而自动升级为实现缺陷。
