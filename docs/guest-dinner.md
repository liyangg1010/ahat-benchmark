# 客人晚餐：场景、参考 plan 与 goal

修订 `guest-dinner-v1`，2026-11-12；open 版本 1.10.4。

任务 `dec162ab-e453-419f-971a-2e32987350f2`：**Prepare an elegant dinner for guests**。原 21 步计划摆放盘子、苹果、奶酪与蜡烛；新版 49 步提供完整的具体晚餐方案。

## 场景补充

| 新食物 | 类型 | 初始位置 | 份量 |
| --- | --- | --- | --- |
| salmon_fillet_107 | seafood | refrigerator_33 内 | serves_group=true |
| potatoes_108 | potato | refrigerator_33 内 | serves_group=true |
| vegetables_109 | vegetables | refrigerator_33 内 | serves_group=true |

三个节点均显式标注 is_food、can_be_heated、is_clean、can_be_moved 为 true，heated=false。serves_group 表示足够该场景中的客人，不推断具体人数或任意人数；原有苹果与奶酪及奶酪份量声明保留。仅新增三个节点和三条 in 边，已有节点状态不改写。

## 参考方案与目标含义

先开柜取干净餐盘上桌，再将三份食物放入已有 stove_oven_27。关炉门、通电后，逐份执行 heat_with_oven；断电、开炉门后取出食物，放到 plate_79 上共享供餐。关闭炉门、冰箱与柜门，点亮已有 candle_70；餐桌上已有干净桌布、花瓶与餐巾作为布置。

采用 domain 已支持的食物直接 in 烤箱模型，无需修改 domain 或为炉灶新增能力。加热只产生 heated，不增加 cooked、进食或等待。

这次将以下目标写入源任务的 reference_goal，作为当前符号模型下一个充分的具体成功方案。三种食物提供主菜、主食和蔬菜且各自足够客人；干净餐具、桌面和已有布置加点亮蜡烛构成 elegant 的具体解释。它不意味着其他菜单、不加热的合适餐食或其他布置必然失败，也不能量化主观审美。目标不增加运行时评分门槛；导出的推理 cases 仍只含指令、场景和 domain 绑定，避免泄露答案。

## 修改范围与验证

仅这一条源任务的 scene_graph、plan、reference_goal 改动，其余 286 条源行原字节不变；同步 open cases、manifest 与 hf_sync 指纹。普通和液体 domain、easy/medium 场景副本均不变。场景已变化，应重新导出该任务输入并重新推理评测。

写入前已验证真实 VAL 合法性、完整 goal 可达及每步 scene/PDDL 回放。负向对照：去掉全部加热动作、去掉点灯、停在装盘之前、分别删除三种食物的 serves_group；六个对照均仍可执行，但无法满足完整 goal。

全量验证通过：287 条参考合法、19 组 reference_goal 可达；两个 domain 和 287 个 problem 独立解析通过，无初态事实丢失，4,168 步回放一致。113 项测试、doctor、发布源检查通过，迁移复跑为 0 条变更。历史 cooking 审查表的 deferred 计数尚未更新，不能据此把本任务继续判为旧参考待修复。

通过 scripts/repair_guest_dinner.py 重现候选验证，--write 在验证成功后采纳；重复运行应为 0 条变更。CI 使用 check_dinner_references.py 校验正式 plan、正式 reference_goal 与采纳记录一致并重跑负向对照。份量回归同时检查这三个新声明可见于实际 D1 请求、不会自动产生 heated。

证据：

- [原计划与采纳记录](validation/guest_dinner_v1_adoption.json)
- [目标与负向对照](validation/guest_dinner_v1_goal_checks.json)
- [全部参考检查](validation/guest_dinner_v1_reference_checks.json)
- [全部场景与逐步回放](validation/guest_dinner_v1_scene_checks.json)

## 正式 reference_goal

```lisp
(and
  (is_food salmon_fillet_107)
  (serves_group salmon_fillet_107)
  (heated salmon_fillet_107)
  (item_on_surface salmon_fillet_107 plate_79)
  (is_food potatoes_108)
  (serves_group potatoes_108)
  (heated potatoes_108)
  (item_on_surface potatoes_108 plate_79)
  (is_food vegetables_109)
  (serves_group vegetables_109)
  (heated vegetables_109)
  (item_on_surface vegetables_109 plate_79)
  (item_on_surface plate_79 dining_table_14)
  (is_clean plate_79)
  (is_clean dining_table_14)
  (furniture_in_room dining_table_14 dining_room_7)
  (not (is_powered_on stove_oven_27))
  (not (is_open stove_oven_27))
  (not (is_open refrigerator_33))
  (not (is_open kitchen_cabinet_set_30))
  (handempty agent_0)
  (item_on_surface tablecloth_67 dining_table_14)
  (is_clean tablecloth_67)
  (item_on_surface centerpiece_vase_32 dining_table_14)
  (is_clean centerpiece_vase_32)
  (item_on_surface napkin_34 dining_table_14)
  (is_clean napkin_34)
  (item_on_surface napkin_36 dining_table_14)
  (is_clean napkin_36)
  (item_on_surface napkin_69 dining_table_14)
  (is_clean napkin_69)
  (is_light_on candle_70)
  (item_on_surface candle_70 dining_table_14)
)
```

## 正式 plan

```lisp
(navigate agent_0 bedroom_6 kitchen_cabinet_set_30)
(open agent_0 kitchen_cabinet_set_30)
(navigate agent_0 kitchen_cabinet_set_30 plate_79)
(pick_from_receptacle agent_0 plate_79 kitchen_cabinet_set_30)
(navigate agent_0 plate_79 dining_table_14)
(place_on_surface agent_0 plate_79 dining_table_14)
(navigate agent_0 dining_table_14 stove_oven_27)
(open agent_0 stove_oven_27)
(navigate agent_0 stove_oven_27 refrigerator_33)
(open agent_0 refrigerator_33)
(navigate agent_0 refrigerator_33 salmon_fillet_107)
(pick_from_receptacle agent_0 salmon_fillet_107 refrigerator_33)
(navigate agent_0 salmon_fillet_107 stove_oven_27)
(place_in_receptacle agent_0 salmon_fillet_107 stove_oven_27)
(navigate agent_0 stove_oven_27 potatoes_108)
(pick_from_receptacle agent_0 potatoes_108 refrigerator_33)
(navigate agent_0 potatoes_108 stove_oven_27)
(place_in_receptacle agent_0 potatoes_108 stove_oven_27)
(navigate agent_0 stove_oven_27 vegetables_109)
(pick_from_receptacle agent_0 vegetables_109 refrigerator_33)
(navigate agent_0 vegetables_109 stove_oven_27)
(place_in_receptacle agent_0 vegetables_109 stove_oven_27)
(close agent_0 stove_oven_27)
(power_on agent_0 stove_oven_27)
(heat_with_oven agent_0 salmon_fillet_107 stove_oven_27)
(heat_with_oven agent_0 potatoes_108 stove_oven_27)
(heat_with_oven agent_0 vegetables_109 stove_oven_27)
(power_off agent_0 stove_oven_27)
(open agent_0 stove_oven_27)
(navigate agent_0 stove_oven_27 salmon_fillet_107)
(pick_from_receptacle agent_0 salmon_fillet_107 stove_oven_27)
(navigate agent_0 salmon_fillet_107 plate_79)
(place_on_surface agent_0 salmon_fillet_107 plate_79)
(navigate agent_0 plate_79 potatoes_108)
(pick_from_receptacle agent_0 potatoes_108 stove_oven_27)
(navigate agent_0 potatoes_108 plate_79)
(place_on_surface agent_0 potatoes_108 plate_79)
(navigate agent_0 plate_79 vegetables_109)
(pick_from_receptacle agent_0 vegetables_109 stove_oven_27)
(navigate agent_0 vegetables_109 plate_79)
(place_on_surface agent_0 vegetables_109 plate_79)
(navigate agent_0 plate_79 stove_oven_27)
(close agent_0 stove_oven_27)
(navigate agent_0 stove_oven_27 refrigerator_33)
(close agent_0 refrigerator_33)
(navigate agent_0 refrigerator_33 kitchen_cabinet_set_30)
(close agent_0 kitchen_cabinet_set_30)
(navigate agent_0 kitchen_cabinet_set_30 candle_70)
(light_on agent_0 candle_70)
```
