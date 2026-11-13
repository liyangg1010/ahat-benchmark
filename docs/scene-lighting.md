# 场景、照明与缓存修复：scene-lighting-v1

2026-11-12。按已确认方案完成多物交付回放、两道咖啡机位置、非法名称、
机器人位置关系、照明及评测缓存修复。正式任务仍为 **289 道**，ID、顺序、
指令、难度和已有参考目标均保持不变。PDDL 防环只记录方案，本轮未实施。

两个 domain ID 沿用原值，revision 更新为 `scene-lighting-v1`，哈希已更新。
easy/medium/open split 版本为 **1.9.0 / 1.8.0 / 1.9.0**。
普通裁判版本为 `ahat-rubric-scene-lighting-v7`，液体裁判为
`ahat-rubric-liquid-lighting-v2`。生成输入和评测须使用当前数据、domain 和新输出目录。

## 修改及范围

### 多物交付

scene 中 `person.p_holding` 使用去重的对象列表，不设数量上限；兼容旧字符串、
null 和缺省字段。交付追加对象，删除持有关系时只删除指定对象。机器人仍保持单物持有。
初态提取、邻接验证、回放及 D2 摘要均支持完整列表；D1 仍使用直接 PDDL 末态。
旧回放在 14 道参考任务中丢失的 22 条持有关系已恢复，无需修改这些任务的交付计划。

### 两道咖啡任务与非法名称

咖啡机沿用已有厨岛，将 `in` 改为 `on`，厨岛顶面不受柜门关闭影响：

| 任务 ID | 咖啡机 | 厨岛 |
| --- | --- | --- |
| `f8e914bb-3f3a-43de-8b8f-c86cbaf6894f` | coffee_machine_16 | kitchen_island_6 |
| `2cd06e0a-88a9-45a6-a5e3-a378199d6414` | coffee_machine_39 | kitchen_island_84 |

两条参考计划不变，液体结果断言和制作步骤见证均通过。

五道场景中的非法名称及全部显式引用同步替换：
`children's_toys_63` → `childrens_toys_63`、`stuffed toy_22` → `stuffed_toy_22`（两道）、
`under‑stair_storage_unit_22` → `under_stair_storage_unit_22`、`t‑shirt_57` → `t_shirt_57`。
当前正式场景转换不再排除任何初态事实；未改写历史隔离数据和原始归档。

### 机器人位置

最初调查的 59 条“物品／家具 on agent”全部删除。执行时全量扫描补发现两条
“room on agent”，同属反向位置编码残留，也一并删除，合计 **61 条／61 道任务**。
其中 **58 道**机器人原有房间边与 `agent.location` 冲突，已修正。
保留所有物品的合法物理支撑关系，两个房间节点仍作为空间根节点，不人为另找放置处。

`agent.location` 为精确位置，`agent in room` 为推导的冗余关系，不产生额外
`agent_at`。完整动作回放后同步房间边，包括导航、拿起后仍以手持对象为位置锚点、
向人交付，以及其他机器人所在家具被移动的情况。D2 摘要使用同步后的房间关系，
并展示精确位置及人的完整持有列表。

### 照明

`light_on` 与 `is_light_on` 的对象类型改为 `physobj`，仍要求 `can_be_lighted`。
增加 `light_off`。纯照明节点只用 `is_light_on` 表示开启状态，不再携带通电状态；
咖啡机、水壶等设备继续使用原有 `power_on/off`。

审查后的照明对象清单位于迁移脚本中，不依据 furniture 分类批量推断能力。
**184 道场景的 1,629 个照明节点**清除冗余通电字段，其中一盏初始已开启的灯迁移为
`is_light_on=true`。**11 条参考计划**将开灯 power_on 改为 light_on。
八份裁判提示词同步说明单一照明状态与多物交付语义，评分权重不变。

### 缓存绑定

VAL resume、judge（含 resume）和 summarize 都逐条比较缓存计划与 inference 的
规范化动作，接受大小写、空白及受支持调用格式的差异。对 valid case，另核对
缓存初态与当前场景生成的初态。检查在复用结果、覆盖输出及裁判调用之前执行。

阶段结果保存 cases 内容 hash；judge 的上游绑定包含 VAL 的输入／协议签名及
实际 cases hash。改变上游结果会使旧 judge 缓存失效，即使原输入文件没有改变。
内容 hash 用于发现结果损坏／错配，不是针对可任意重写文件者的真实性签名。
这些检查未增加任务成功的硬目标门槛。

## 验证

- 102 项单元／集成测试通过，包含原生 VAL 的多物交付、三种灯具类型、关灯、
  非照明设备通电、位置同步，以及缓存错配、内容损坏、规范化等价和恢复执行检查。
- 289 条参考计划经 VAL 判合法；18 个既有 reference_goal 全部可达；
  11 个邻接对照与 4 个固体热处理对照通过。
- 34 组液体／器具参考结果断言、76 个遗漏步骤对照通过。
- 全部 289 条参考计划共 **3,997 步**的 scene→PDDL 回放与直接 PDDL 回放一致。
- 全量基线末态比较只出现已批准的照明、对象重命名及咖啡机放置变化；
  104 道末态完全相同。所有非照明动作定义与修复前完全相同。
- 289 道数据迁移均幂等；数据投影、域生成、doctor、release source check 通过。

多项数据修改有重叠，合计 **235 条任务记录改变**，其余 54 条源数据行保持原样。
未重新运行外部算法或真实 LLM 裁判。

证据：[修改明细及源／split 索引](validation/scene_lighting_v1_inventory.json)、
[全量逐步回放及基线对比](validation/scene_lighting_v1_checks.json)、
[参考计划与目标](validation/scene_lighting_v1_reference_checks.json)、
[液体结果及遗漏对照](validation/scene_lighting_v1_liquid_checks.json)。

迁移脚本 `scripts/repair_scene_lighting.py` 默认只报告变化，`--write` 才写入；
重复运行不再改变任务。`scripts/check_scene_lighting.py --baseline <旧快照目录>`
执行全量逐步回放和限定范围的前后比较；旧目录需包含 JSONL 及两个 domain 文件。

## 暂不实施：PDDL 防环

问题：大盒子内已有小盒子，拿起大盒子后仍能放进小盒子，产生包含环。
普通 on/in 与相邻放置也需要覆盖任意层级、混合路径。

拟增加派生谓词，示意如下（**未加入当前 domain**）：

```lisp
(:derived (spatial_under ?x - physobj ?y - physobj)
  (or
    (item_on_surface ?x ?y)
    (item_in_receptacle ?x ?y)
    (exists (?z - physobj)
      (and
        (or (item_on_surface ?x ?z) (item_in_receptacle ?x ?z))
        (spatial_under ?z ?y)))))
```

四个放置动作拟检查 `(not (= ?obj ?target))` 与
`(not (spatial_under ?target ?obj))`，并补齐声明和 requirements。
派生关系由当前 on/in 推导，不写进 scene/init，不手工维护效果。
Python 验证初态，PDDL 限制动作，回放／导出执行同语义检查。
实施前须核验递归派生谓词的 VAL／规划器兼容性、房间根节点及家具／设备移动关系。
本轮没有添加该谓词、前置条件或空间无环校验。

关闭外层容器的通用可访问性约束也尚未扩展；本轮修正两道咖啡场景，
不宣称 domain 已禁止所有隔着关闭容器操作的计划。该模型缺口与防环是不同问题。
