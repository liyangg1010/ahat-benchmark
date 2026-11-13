# 移动位置与摆放容量修复：location-capacity-v1

2026-11-11。同时修复普通 domain 和由其生成的液体 domain。
沿用未发布快照的 domain ID，以新增 `revision: location-capacity-v1` 和更新后的
SHA-256 标识本轮协议。所有 split manifests 和域注册表同步更新。
模型生成及评测应使用新 domain 指纹和新的输出目录。

## 移动家具／设备后位置唯一

旧 move_furniture_to_room / move_device_to_room 添加 `(agent_at agent target_room)`，
却保留 `(agent_at agent moved_object)`。这让 VAL 和直接 PDDL 回放认为机器人同时
位于目标房间和原动作对象；scene 的单个 location 字段只能保存一个，导致两种回放不一致。

现在移动时同时删除旧对象位置、添加目标房间位置，移动物体的房间关系也同步更新。
从有效的单位置初态出发，移动、后续导航、再次搬运均保持单位置，不修改其他机器人的位置。
旧漏洞允许搬运后直接从过期位置发起 navigate；现在该计划因前置条件不满足而无效。

## 普通与相邻摆放遵守同一容量约束

`can_only_place_one_object` 限制目标上相应摆放空间的直接占用数：

- 表面用 `item_on_surface` 计数；place_on_surface 与 place_next_to_surface 都要求目标为空。
- 容器内部用 `item_in_receptacle` 计数；place_in_receptacle 与 place_next_to_inside 都要求内部为空。
- 因为 next_to 动作需要已有参考物体，单物体容量目标无法再接收第二个相邻物体。
- 不带该标记的目标仍可正常相邻摆放；移走已占用物体后，普通摆放可再次使用空目标。

沿用已有表面容量语义，表面与内部按各自关系计数，不将柜内物体当成柜顶占用，
也不将柜顶物体当成内部占用。本修订不引入总容积或跨空间共享容量模型。

## 数据影响与验证

当前 289 条参考计划均未调用两个移动动作，所有场景也未启用该容量标记。
本次 **不修改指令、scene、参考计划、目标或任务数量**；全量参考末态与修复前一致。
新约束主要阻止算法生成利用漏洞的计划。

验证：91 项单元／集成测试通过；两种 domain 的 12 组原生 VAL 对照验证旧漏洞
确实可利用、修复后被拒绝，并覆盖普通表面摆放原本就受限的对照组。测试还覆盖
多机器人、连续搬运、空容量、解除占用、无容量限制及 scene/PDDL 一致性。
289 条参考计划合法，18 个原目标可达，11 个邻接和 4 个固体处理反例仍通过。

证据：[漏洞对照与末态比较](validation/location_capacity_v1_checks.json)、
[全部参考验证](validation/location_capacity_v1_reference_checks.json)。
之前的 liquid_v1_* 报告保留其当时的 domain 哈希，是历史证据，不代表本轮修复后的指纹。
