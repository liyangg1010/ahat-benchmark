# 三道两人／家庭备餐参考修复

修订：`group-meal-reference-v1`（2026-11-12）。已采纳为正式参考 plan；open 版本为 1.10.3，正式任务数仍为 287。

沿用上一批晚餐的做法：构造一种可行的成功方案，先验证候选，再替换参考。以下 goal 是这些具体方案的离线结果见证，未写入运行时 `reference_goal`，也不要求其他正确解使用同一菜单、餐具或动作顺序。cozy 采用既有蜡烛／桌面布置的一种解释；不声称由 PDDL 证明主观舒适度。

两人晚餐补充土豆与蔬菜，两者均为真实食物、初始 heated=false、serves_two=true，放入现有 refrigerator_32。家庭早餐补充 bread_115，初始 heated=false、serves_group=true，放入 refrigerator_35。两个场景共新增三个节点及三条 in 边。原鸡蛋的份量标注保留；早午餐场景无需增加食物。

晚餐为加热后的鸡蛋、土豆和蔬菜，早午餐为加热后的两人份鸡蛋与已有苹果，家庭早餐为加热后的家庭份鸡蛋、家庭份面包及已有黄油。均用现有干净碗／盘承装，放在干净餐桌上；共享盛菜器皿允许多人取餐，不把一个器皿解释为一人份。苹果、黄油为配菜，不推断其足量覆盖所有人。

`heated` 仅由加热动作获得，不增加 cooked 或初始生熟分类；面包无需强制加热。serves_group 表示足够该场景所指家庭，不表示任意人数。没有把空杯、牛奶盒或未声明内容物的果盘当作饮品或食物，没有新增液体操作、进食、等待或营养模型。

| 任务 | 原步骤 | 新步骤 | 结果 |
| --- | ---: | ---: | --- |
| Host a cozy dinner for two tonight. | 28 | 42 | 鸡蛋、土豆、蔬菜加热装碗，点亮餐桌蜡烛 |
| Host a cozy brunch for two. | 19 | 34 | 两人份鸡蛋加热装碗，与苹果上桌，点亮蜡烛 |
| Prepare a full family breakfast service | 33 | 36 | 家庭份鸡蛋加热装盘，面包与黄油上桌，配餐巾 |

## 验证与影响范围

每条候选在写入前经过真实 VAL、原生目标判断及每步 scene→PDDL 对照。负向对照包括省略加热／点灯、在装盘前停止，以及分别删除份量事实；对照计划依然合法，但不满足选定结果目标。份量不会自动生成加热或供餐状态。

全量验证：287 条参考合法、18 组既有目标通过，287 个 problem 独立解析通过、初态无事实丢失，4,140 步 scene/PDDL 回放一致；113 项测试、doctor 和发布源检查通过。迁移复跑为 0 条变更。

仅三个源记录的 scene_graph／plan 改动；其余 284 行原字节不变。同步 open 场景副本、manifest 和 hf_sync 指纹。指令、既有 reference_goal、两个 domain 和评分规则不变。使用这两个新增食物场景时，应重新导出输入并重新推理评测；不复用旧场景结果。

第四道客人优雅晚餐不在本次范围。通用关闭祖先容器访问、液体不变量、空间防环三项模型问题继续按之前决定暂缓。历史 cooking 清单中的 deferred 标记是旧审查口径，不应将本次三条仍计为旧参考未修复。

后续更新：第四道客人晚餐已在 [guest-dinner-v1](guest-dinner.md) 中补充食物、替换参考并写入对应 reference_goal。

机器证据：

- [采纳记录及原 plan](validation/group_meal_reference_v1_adoption.json)
- [目标与负向对照](validation/group_meal_reference_v1_goal_checks.json)
- [全部参考验证](validation/group_meal_reference_v1_reference_checks.json)
- [全部场景与逐步回放](validation/group_meal_reference_v1_scene_checks.json)

迁移脚本 `scripts/repair_group_meal_references.py` 默认只验证；`--write` 在所有候选通过后才写入，复跑应显示 0 条变更。CI 同时验证本批和此前晚餐参考；这些离线检查不改变实际算法评测的评分入口。

## Host a cozy dinner for two tonight.

`f3ee3e87-d782-4870-8ed3-2bc92f344010`

参考结果 goal：

```lisp
(and
  (heated eggs_116)
  (heated potatoes_122)
  (heated vegetables_123)
  (is_food eggs_116)
  (item_on_surface eggs_116 fruit_bowl_74)
  (is_food potatoes_122)
  (item_on_surface potatoes_122 fruit_bowl_74)
  (is_food vegetables_123)
  (item_on_surface vegetables_123 fruit_bowl_74)
  (serves_two eggs_116)
  (serves_two potatoes_122)
  (serves_two vegetables_123)
  (item_on_surface fruit_bowl_74 dining_table_19)
  (is_clean fruit_bowl_74)
  (is_clean dining_table_19)
  (not (is_powered_on stove_26))
  (handempty agent_0)
  (not (is_open refrigerator_32))
  (item_on_surface centerpiece_27 dining_table_19)
  (is_light_on candle_29)
  (item_on_surface candle_29 dining_table_19)
)
```

已采纳 plan：

```lisp
(navigate agent_0 empty_room_10 refrigerator_32)
(open agent_0 refrigerator_32)
(navigate agent_0 refrigerator_32 eggs_116)
(pick_from_receptacle agent_0 eggs_116 refrigerator_32)
(navigate agent_0 eggs_116 pot_37)
(place_on_surface agent_0 eggs_116 pot_37)
(navigate agent_0 pot_37 stove_26)
(power_on agent_0 stove_26)
(heat_on_heating_device agent_0 eggs_116 pot_37 stove_26)
(power_off agent_0 stove_26)
(navigate agent_0 stove_26 eggs_116)
(pick_from_surface agent_0 eggs_116 pot_37)
(navigate agent_0 eggs_116 fruit_bowl_74)
(place_on_surface agent_0 eggs_116 fruit_bowl_74)
(navigate agent_0 fruit_bowl_74 potatoes_122)
(pick_from_receptacle agent_0 potatoes_122 refrigerator_32)
(navigate agent_0 potatoes_122 pot_37)
(place_on_surface agent_0 potatoes_122 pot_37)
(navigate agent_0 pot_37 stove_26)
(power_on agent_0 stove_26)
(heat_on_heating_device agent_0 potatoes_122 pot_37 stove_26)
(power_off agent_0 stove_26)
(navigate agent_0 stove_26 potatoes_122)
(pick_from_surface agent_0 potatoes_122 pot_37)
(navigate agent_0 potatoes_122 fruit_bowl_74)
(place_on_surface agent_0 potatoes_122 fruit_bowl_74)
(navigate agent_0 fruit_bowl_74 vegetables_123)
(pick_from_receptacle agent_0 vegetables_123 refrigerator_32)
(navigate agent_0 vegetables_123 pot_37)
(place_on_surface agent_0 vegetables_123 pot_37)
(navigate agent_0 pot_37 stove_26)
(power_on agent_0 stove_26)
(heat_on_heating_device agent_0 vegetables_123 pot_37 stove_26)
(power_off agent_0 stove_26)
(navigate agent_0 stove_26 vegetables_123)
(pick_from_surface agent_0 vegetables_123 pot_37)
(navigate agent_0 vegetables_123 fruit_bowl_74)
(place_on_surface agent_0 vegetables_123 fruit_bowl_74)
(navigate agent_0 fruit_bowl_74 candle_29)
(light_on agent_0 candle_29)
(navigate agent_0 candle_29 refrigerator_32)
(close agent_0 refrigerator_32)
```

## Host a cozy brunch for two.

`0cf41a97-9f6a-4e13-8542-1def6889483d`

参考结果 goal：

```lisp
(and
  (heated eggs_66)
  (is_food eggs_66)
  (item_on_surface eggs_66 fruit_bowl_30)
  (is_food apple_180)
  (item_on_surface apple_180 fruit_bowl_30)
  (serves_two eggs_66)
  (item_on_surface fruit_bowl_30 dining_table_52)
  (is_clean fruit_bowl_30)
  (is_clean dining_table_52)
  (not (is_powered_on stove_26))
  (handempty agent_0)
  (not (is_open cabinets_49))
  (not (is_open refrigerator_25))
  (not (is_open refrigerator_46))
  (is_light_on candle_set_28)
  (item_on_surface candle_set_28 dining_table_52)
)
```

已采纳 plan：

```lisp
(navigate agent_0 rec_game_18 cabinets_49)
(open agent_0 cabinets_49)
(navigate agent_0 cabinets_49 fruit_bowl_30)
(pick_from_receptacle agent_0 fruit_bowl_30 cabinets_49)
(navigate agent_0 fruit_bowl_30 dining_table_52)
(place_on_surface agent_0 fruit_bowl_30 dining_table_52)
(navigate agent_0 dining_table_52 refrigerator_46)
(open agent_0 refrigerator_46)
(navigate agent_0 refrigerator_46 eggs_66)
(pick_from_receptacle agent_0 eggs_66 refrigerator_46)
(navigate agent_0 eggs_66 pot_132)
(place_on_surface agent_0 eggs_66 pot_132)
(navigate agent_0 pot_132 stove_26)
(power_on agent_0 stove_26)
(heat_on_heating_device agent_0 eggs_66 pot_132 stove_26)
(power_off agent_0 stove_26)
(navigate agent_0 stove_26 eggs_66)
(pick_from_surface agent_0 eggs_66 pot_132)
(navigate agent_0 eggs_66 fruit_bowl_30)
(place_on_surface agent_0 eggs_66 fruit_bowl_30)
(navigate agent_0 fruit_bowl_30 refrigerator_25)
(open agent_0 refrigerator_25)
(navigate agent_0 refrigerator_25 apple_180)
(pick_from_receptacle agent_0 apple_180 refrigerator_25)
(navigate agent_0 apple_180 fruit_bowl_30)
(place_on_surface agent_0 apple_180 fruit_bowl_30)
(navigate agent_0 fruit_bowl_30 candle_set_28)
(light_on agent_0 candle_set_28)
(navigate agent_0 candle_set_28 cabinets_49)
(close agent_0 cabinets_49)
(navigate agent_0 cabinets_49 refrigerator_25)
(close agent_0 refrigerator_25)
(navigate agent_0 refrigerator_25 refrigerator_46)
(close agent_0 refrigerator_46)
```

## Prepare a full family breakfast service

`198fd035-6f65-4740-8b01-0643a215ccb4`

参考结果 goal：

```lisp
(and
  (heated eggs_90)
  (is_food eggs_90)
  (item_on_surface eggs_90 plate_86)
  (is_food bread_115)
  (item_on_surface bread_115 plate_86)
  (is_food butter_92)
  (item_on_surface butter_92 plate_86)
  (serves_group eggs_90)
  (serves_group bread_115)
  (item_on_surface plate_86 dining_table_19)
  (is_clean plate_86)
  (is_clean dining_table_19)
  (not (is_powered_on stove_22))
  (handempty agent_0)
  (not (is_open refrigerator_23))
  (not (is_open refrigerator_35))
  (item_on_surface napkin_87 dining_table_19)
)
```

已采纳 plan：

```lisp
(navigate agent_0 corridor_11 plate_86)
(pick_from_surface agent_0 plate_86 dining_table_38)
(navigate agent_0 plate_86 dining_table_19)
(place_on_surface agent_0 plate_86 dining_table_19)
(navigate agent_0 dining_table_19 refrigerator_35)
(open agent_0 refrigerator_35)
(navigate agent_0 refrigerator_35 eggs_90)
(pick_from_receptacle agent_0 eggs_90 refrigerator_35)
(navigate agent_0 eggs_90 pot_30)
(place_on_surface agent_0 eggs_90 pot_30)
(navigate agent_0 pot_30 stove_22)
(power_on agent_0 stove_22)
(heat_on_heating_device agent_0 eggs_90 pot_30 stove_22)
(power_off agent_0 stove_22)
(navigate agent_0 stove_22 eggs_90)
(pick_from_surface agent_0 eggs_90 pot_30)
(navigate agent_0 eggs_90 plate_86)
(place_on_surface agent_0 eggs_90 plate_86)
(navigate agent_0 plate_86 bread_115)
(pick_from_receptacle agent_0 bread_115 refrigerator_35)
(navigate agent_0 bread_115 plate_86)
(place_on_surface agent_0 bread_115 plate_86)
(navigate agent_0 plate_86 refrigerator_23)
(open agent_0 refrigerator_23)
(navigate agent_0 refrigerator_23 butter_92)
(pick_from_receptacle agent_0 butter_92 refrigerator_23)
(navigate agent_0 butter_92 plate_86)
(place_on_surface agent_0 butter_92 plate_86)
(navigate agent_0 plate_86 napkin_87)
(pick_from_surface agent_0 napkin_87 dining_table_38)
(navigate agent_0 napkin_87 dining_table_19)
(place_on_surface agent_0 napkin_87 dining_table_19)
(navigate agent_0 dining_table_19 refrigerator_23)
(close agent_0 refrigerator_23)
(navigate agent_0 refrigerator_23 refrigerator_35)
(close agent_0 refrigerator_35)
```
