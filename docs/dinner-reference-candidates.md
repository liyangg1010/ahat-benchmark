# 三道晚餐任务：已采纳的参考 plan 与验证目标

三组方案已按用户确认作为当前模型下的一种成功实例，替换正式任务的 plan（dinner-reference-v1）。本文件保留候选时的文件名；以下 plan 即当前正式参考。

采纳后全量 287 条参考合法、18 组既有目标可达，287 个 problem 独立解析通过，
4,108 步 scene/PDDL 回放一致。三个场景和两个 domain 均未改动。

第一道采用主菜、主食、蔬菜构成可供餐晚餐的具体解释；第二道对 elegant 使用供餐、装饰和点亮蜡烛的具体解释，不能仅凭可达性认证主观品质。第三道必须同时检查先供餐后撤餐的过程；末态目标不足以证明完整任务。

沿用 heated 模型，不增加 cooked、进食或等待动作。没有将选定菜单、餐桌或餐具作为其他正确方案的必要条件。第三道的 cleanup 具体实现为食物收纳、餐具撤到水槽、餐巾归位及熄灯；不声称模拟了洗盘或就餐后的变脏。

用户已接受这些具体供餐、氛围及撤餐解释作为成功方案。仅替换三条 plan；指令、场景、domain 和 reference_goal 字段不变。以下目标及阶段见证用于离线参考验证，不要求其他正确方案复制相同菜单或步骤；第三道最终目标没有单独写成完整任务的 reference_goal。

## Plan and serve a complete evening meal

任务 ID：`a55dd1af-59ee-4e0c-8139-208e2134ed49`。正式参考 44 步，VAL 合法、目标可达、逐步回放一致。

最终目标：

```lisp
(and
  (heated chicken_breast_162)
  (heated potatoes_163)
  (heated broccoli_164)
  (item_on_surface chicken_breast_162 plate_set_37)
  (item_on_surface potatoes_163 plate_set_37)
  (item_on_surface broccoli_164 plate_set_37)
  (item_on_surface plate_set_37 dining_table_16)
  (is_clean plate_set_37)
  (is_clean dining_table_16)
  (not (is_powered_on stove_49))
  (handempty agent_0)
  (not (is_open refrigerator_19))
)
```

正式参考 plan：

```lisp
(navigate agent_0 corridor_12 plate_set_37)
(pick_from_surface agent_0 plate_set_37 dining_table_17)
(navigate agent_0 plate_set_37 dining_table_16)
(place_on_surface agent_0 plate_set_37 dining_table_16)
(navigate agent_0 dining_table_16 refrigerator_19)
(open agent_0 refrigerator_19)
(navigate agent_0 refrigerator_19 chicken_breast_162)
(pick_from_receptacle agent_0 chicken_breast_162 refrigerator_19)
(navigate agent_0 chicken_breast_162 cooking_pot_72)
(place_on_surface agent_0 chicken_breast_162 cooking_pot_72)
(navigate agent_0 cooking_pot_72 stove_49)
(power_on agent_0 stove_49)
(heat_on_heating_device agent_0 chicken_breast_162 cooking_pot_72 stove_49)
(power_off agent_0 stove_49)
(navigate agent_0 stove_49 chicken_breast_162)
(pick_from_surface agent_0 chicken_breast_162 cooking_pot_72)
(navigate agent_0 chicken_breast_162 plate_set_37)
(place_on_surface agent_0 chicken_breast_162 plate_set_37)
(navigate agent_0 plate_set_37 potatoes_163)
(pick_from_receptacle agent_0 potatoes_163 refrigerator_19)
(navigate agent_0 potatoes_163 cooking_pot_72)
(place_on_surface agent_0 potatoes_163 cooking_pot_72)
(navigate agent_0 cooking_pot_72 stove_49)
(power_on agent_0 stove_49)
(heat_on_heating_device agent_0 potatoes_163 cooking_pot_72 stove_49)
(power_off agent_0 stove_49)
(navigate agent_0 stove_49 potatoes_163)
(pick_from_surface agent_0 potatoes_163 cooking_pot_72)
(navigate agent_0 potatoes_163 plate_set_37)
(place_on_surface agent_0 potatoes_163 plate_set_37)
(navigate agent_0 plate_set_37 broccoli_164)
(pick_from_receptacle agent_0 broccoli_164 refrigerator_19)
(navigate agent_0 broccoli_164 cooking_pot_72)
(place_on_surface agent_0 broccoli_164 cooking_pot_72)
(navigate agent_0 cooking_pot_72 stove_49)
(power_on agent_0 stove_49)
(heat_on_heating_device agent_0 broccoli_164 cooking_pot_72 stove_49)
(power_off agent_0 stove_49)
(navigate agent_0 stove_49 broccoli_164)
(pick_from_surface agent_0 broccoli_164 cooking_pot_72)
(navigate agent_0 broccoli_164 plate_set_37)
(place_on_surface agent_0 broccoli_164 plate_set_37)
(navigate agent_0 plate_set_37 refrigerator_19)
(close agent_0 refrigerator_19)
```

## Prepare an elegant dinner and ambiance

任务 ID：`3cf1736a-3b96-4913-b9c5-df4688ee9053`。正式参考 62 步，VAL 合法、目标可达、逐步回放一致。

最终目标：

```lisp
(and
  (heated salmon_fillet_220)
  (heated potatoes_221)
  (heated carrots_218)
  (item_on_surface salmon_fillet_220 plate_143)
  (item_on_surface potatoes_221 plate_143)
  (item_on_surface carrots_218 plate_143)
  (item_on_surface plate_143 dining_table_18)
  (is_clean plate_143)
  (is_clean dining_table_18)
  (not (is_powered_on stove_33))
  (handempty agent_0)
  (item_on_surface centerpiece_202 dining_table_18)
  (item_on_surface candle_128 dining_table_18)
  (is_light_on candle_128)
  (item_on_surface wine_bottle_90 dining_table_18)
  (not (is_open refrigerator_32))
)
```

正式参考 plan：

```lisp
(navigate agent_0 bedroom_7 cabinet_set_34)
(open agent_0 cabinet_set_34)
(navigate agent_0 cabinet_set_34 plate_143)
(pick_from_receptacle agent_0 plate_143 cabinet_set_34)
(navigate agent_0 plate_143 dining_table_18)
(place_on_surface agent_0 plate_143 dining_table_18)
(navigate agent_0 dining_table_18 refrigerator_32)
(open agent_0 refrigerator_32)
(navigate agent_0 refrigerator_32 salmon_fillet_220)
(pick_from_receptacle agent_0 salmon_fillet_220 refrigerator_32)
(navigate agent_0 salmon_fillet_220 pot_63)
(place_on_surface agent_0 salmon_fillet_220 pot_63)
(navigate agent_0 pot_63 stove_33)
(power_on agent_0 stove_33)
(heat_on_heating_device agent_0 salmon_fillet_220 pot_63 stove_33)
(power_off agent_0 stove_33)
(navigate agent_0 stove_33 salmon_fillet_220)
(pick_from_surface agent_0 salmon_fillet_220 pot_63)
(navigate agent_0 salmon_fillet_220 plate_143)
(place_on_surface agent_0 salmon_fillet_220 plate_143)
(navigate agent_0 plate_143 potatoes_221)
(pick_from_receptacle agent_0 potatoes_221 refrigerator_32)
(navigate agent_0 potatoes_221 pot_63)
(place_on_surface agent_0 potatoes_221 pot_63)
(navigate agent_0 pot_63 stove_33)
(power_on agent_0 stove_33)
(heat_on_heating_device agent_0 potatoes_221 pot_63 stove_33)
(power_off agent_0 stove_33)
(navigate agent_0 stove_33 potatoes_221)
(pick_from_surface agent_0 potatoes_221 pot_63)
(navigate agent_0 potatoes_221 plate_143)
(place_on_surface agent_0 potatoes_221 plate_143)
(navigate agent_0 plate_143 carrots_218)
(pick_from_receptacle agent_0 carrots_218 refrigerator_32)
(navigate agent_0 carrots_218 pot_63)
(place_on_surface agent_0 carrots_218 pot_63)
(navigate agent_0 pot_63 stove_33)
(power_on agent_0 stove_33)
(heat_on_heating_device agent_0 carrots_218 pot_63 stove_33)
(power_off agent_0 stove_33)
(navigate agent_0 stove_33 carrots_218)
(pick_from_surface agent_0 carrots_218 pot_63)
(navigate agent_0 carrots_218 plate_143)
(place_on_surface agent_0 carrots_218 plate_143)
(navigate agent_0 plate_143 centerpiece_202)
(pick_from_surface agent_0 centerpiece_202 dining_table_set_58)
(navigate agent_0 centerpiece_202 dining_table_18)
(place_on_surface agent_0 centerpiece_202 dining_table_18)
(navigate agent_0 dining_table_18 candle_128)
(pick_from_surface agent_0 candle_128 dining_table_set_58)
(navigate agent_0 candle_128 dining_table_18)
(place_on_surface agent_0 candle_128 dining_table_18)
(navigate agent_0 dining_table_18 wine_bottle_90)
(pick_from_surface agent_0 wine_bottle_90 dining_table_71)
(navigate agent_0 wine_bottle_90 dining_table_18)
(place_on_surface agent_0 wine_bottle_90 dining_table_18)
(navigate agent_0 dining_table_18 candle_128)
(light_on agent_0 candle_128)
(navigate agent_0 candle_128 refrigerator_32)
(close agent_0 refrigerator_32)
(navigate agent_0 refrigerator_32 cabinet_set_34)
(close agent_0 cabinet_set_34)
```

## Host a formal dinner and cleanup

任务 ID：`4a3dc074-3cd6-4241-a4a5-2c37f31c99a1`。正式参考 76 步，VAL 合法、目标可达、逐步回放一致。

必须先在第 50 步后达到供餐阶段目标：

```lisp
(and
  (heated beef_steak_99)
  (heated potatoes_100)
  (heated green_beans_101)
  (item_on_surface beef_steak_99 plate_set_15)
  (item_on_surface potatoes_100 plate_set_15)
  (item_on_surface green_beans_101 plate_set_15)
  (item_on_surface plate_set_15 dining_table_19)
  (is_clean plate_set_15)
  (is_clean dining_table_19)
  (not (is_powered_on stove_15))
  (handempty agent_0)
  (item_on_surface napkin_24 dining_table_19)
  (item_on_surface candle_set_21 dining_table_19)
  (is_light_on candle_set_21)
)
```

最终目标：

```lisp
(and
  (heated beef_steak_99)
  (heated potatoes_100)
  (heated green_beans_101)
  (item_in_receptacle beef_steak_99 refrigerator_14)
  (item_in_receptacle potatoes_100 refrigerator_14)
  (item_in_receptacle green_beans_101 refrigerator_14)
  (item_on_surface plate_set_15 sink_16)
  (item_on_surface napkin_24 dining_table_31)
  (is_clean dining_table_19)
  (not (is_light_on candle_set_21))
  (not (is_powered_on stove_15))
  (not (is_open refrigerator_14))
  (not (is_open cabinets_17))
  (handempty agent_0)
)
```

正式参考 plan：

```lisp
(navigate agent_0 dining_room_12 cabinets_17)
(open agent_0 cabinets_17)
(navigate agent_0 cabinets_17 plate_set_15)
(pick_from_receptacle agent_0 plate_set_15 cabinets_17)
(navigate agent_0 plate_set_15 dining_table_19)
(place_on_surface agent_0 plate_set_15 dining_table_19)
(navigate agent_0 dining_table_19 napkin_24)
(pick_from_surface agent_0 napkin_24 dining_table_31)
(navigate agent_0 napkin_24 dining_table_19)
(place_on_surface agent_0 napkin_24 dining_table_19)
(navigate agent_0 dining_table_19 candle_set_21)
(light_on agent_0 candle_set_21)
(navigate agent_0 candle_set_21 refrigerator_14)
(open agent_0 refrigerator_14)
(navigate agent_0 refrigerator_14 beef_steak_99)
(pick_from_receptacle agent_0 beef_steak_99 refrigerator_14)
(navigate agent_0 beef_steak_99 cooking_pot_13)
(place_on_surface agent_0 beef_steak_99 cooking_pot_13)
(navigate agent_0 cooking_pot_13 stove_15)
(power_on agent_0 stove_15)
(heat_on_heating_device agent_0 beef_steak_99 cooking_pot_13 stove_15)
(power_off agent_0 stove_15)
(navigate agent_0 stove_15 beef_steak_99)
(pick_from_surface agent_0 beef_steak_99 cooking_pot_13)
(navigate agent_0 beef_steak_99 plate_set_15)
(place_on_surface agent_0 beef_steak_99 plate_set_15)
(navigate agent_0 plate_set_15 potatoes_100)
(pick_from_receptacle agent_0 potatoes_100 refrigerator_14)
(navigate agent_0 potatoes_100 cooking_pot_13)
(place_on_surface agent_0 potatoes_100 cooking_pot_13)
(navigate agent_0 cooking_pot_13 stove_15)
(power_on agent_0 stove_15)
(heat_on_heating_device agent_0 potatoes_100 cooking_pot_13 stove_15)
(power_off agent_0 stove_15)
(navigate agent_0 stove_15 potatoes_100)
(pick_from_surface agent_0 potatoes_100 cooking_pot_13)
(navigate agent_0 potatoes_100 plate_set_15)
(place_on_surface agent_0 potatoes_100 plate_set_15)
(navigate agent_0 plate_set_15 green_beans_101)
(pick_from_receptacle agent_0 green_beans_101 refrigerator_14)
(navigate agent_0 green_beans_101 cooking_pot_13)
(place_on_surface agent_0 green_beans_101 cooking_pot_13)
(navigate agent_0 cooking_pot_13 stove_15)
(power_on agent_0 stove_15)
(heat_on_heating_device agent_0 green_beans_101 cooking_pot_13 stove_15)
(power_off agent_0 stove_15)
(navigate agent_0 stove_15 green_beans_101)
(pick_from_surface agent_0 green_beans_101 cooking_pot_13)
(navigate agent_0 green_beans_101 plate_set_15)
(place_on_surface agent_0 green_beans_101 plate_set_15)
(navigate agent_0 plate_set_15 beef_steak_99)
(pick_from_surface agent_0 beef_steak_99 plate_set_15)
(navigate agent_0 beef_steak_99 refrigerator_14)
(place_in_receptacle agent_0 beef_steak_99 refrigerator_14)
(navigate agent_0 refrigerator_14 potatoes_100)
(pick_from_surface agent_0 potatoes_100 plate_set_15)
(navigate agent_0 potatoes_100 refrigerator_14)
(place_in_receptacle agent_0 potatoes_100 refrigerator_14)
(navigate agent_0 refrigerator_14 green_beans_101)
(pick_from_surface agent_0 green_beans_101 plate_set_15)
(navigate agent_0 green_beans_101 refrigerator_14)
(place_in_receptacle agent_0 green_beans_101 refrigerator_14)
(navigate agent_0 refrigerator_14 plate_set_15)
(pick_from_surface agent_0 plate_set_15 dining_table_19)
(navigate agent_0 plate_set_15 sink_16)
(place_on_surface agent_0 plate_set_15 sink_16)
(navigate agent_0 sink_16 napkin_24)
(pick_from_surface agent_0 napkin_24 dining_table_19)
(navigate agent_0 napkin_24 dining_table_31)
(place_on_surface agent_0 napkin_24 dining_table_31)
(navigate agent_0 dining_table_31 candle_set_21)
(light_off agent_0 candle_set_21)
(navigate agent_0 candle_set_21 refrigerator_14)
(close agent_0 refrigerator_14)
(navigate agent_0 refrigerator_14 cabinets_17)
(close agent_0 cabinets_17)
```

反例验证：另有合法计划完全不把食物摆上餐桌，也能满足以上最终目标；它未达到供餐阶段目标。因此不能将末态列表直接作为该题完整充分 reference_goal。

历史候选证据见 [候选验证](validation/dinner_reference_candidates.json)；正式采纳记录见 [前后计划](validation/dinner_reference_v1_adoption.json)，当前目标与反例检查见 [目标检查](validation/dinner_reference_v1_goal_checks.json)。

可运行 `python scripts/check_dinner_references.py` 检查三条正式参考、供餐阶段及省略动作对照；该检查已加入 CI，不改变运行时评分。
