# PDDL 类型层级修复：type-hierarchy-v1

2026-11-12。普通及液体 domain 均使用 revision `type-hierarchy-v1`，保留各自逻辑 ID，
通过 SHA-256 绑定具体版本。三个 split manifest 更新为 1.10.0；287 条任务源记录和
三个 cases.json 原字节不变，指令、scene、计划、目标及任务 domain 分配不变。

此前 `item agent - item` 将 item 声明为自身子类；`object - physobj` 又将 PDDL
内置根类型 object 当作小物品类型重新定义。自带 VAL 接受旧文件，但独立解析器
pddl 0.4.6 在 object 声明处失败。现在类型树等价于：

```lisp
(:types
  item - object
  agent location - item
  person physobj - location
  room furniture device small_object - physobj
  container - small_object)
```

object 只作为内置根类型出现，不在 :types 左侧重新声明。原小物品类型改为
small_object；container 仍是小物品子类。clean_item 的 target 签名同步为
small_object，其余动作的参数适用对象不变。两个 domain 的解析结构差异严格限于
类型声明和相应签名，没有改写动作前置条件或效果。

SceneGraphManager 将 JSON 的 objects 分类映射为 small_object，因此全场景 PDDL、
参考无关推理导出及旧 problem generator 共同使用新映射。JSON 分类仍叫 objects，
节点的业务 type（例如 coffee_pod）和名称不变。类型过滤、VAL 参数预检查和效果
回放共用类型解析／祖先判断；无类型标注时的默认 object 仍表示内置根类型，
没有把根类型默认值替换成 small_object。

普通 domain 保留 ordinary-core-v1 的边界：25 个动作，不含 fill_from_faucet、
fill_device_with_water、dispense_from_device、pour_into、pour。液体生成器独立加入
这五个动作及其他液体动作，共 38 个；本次重新生成液体 domain 仅同步类型修改。
清洗、浸泡、热处理和液体内容语义均不变。

验证结果：

- 113 项单元／集成测试通过，包含根类型量化的原生 VAL、Python 和 scene 对照，
  小容器的子类型接受、家具误用小物品参数时拒绝，以及普通 domain 液体动作拒绝。
- pddl 0.4.6 独立解析两个 domain 和全部 287 个生成的 problem；类型树无环且
  所有类型可追溯到内置根，初态没有事实因类型过滤而丢失。
- 287 条参考经原生 VAL 判合法，18 组既有目标可达，11 个邻接和 4 个热处理对照通过。
- 287 道任务的初态／参考末态与修复前完全一致，3,985 步 scene/PDDL 回放一致。
- 32 组液体／器具结果、483 步回放、74 个遗漏动作对照通过；备餐审计仍为
  2 道已确认充分目标、9 道待完整认证，没有提高已有充分性声明。

机器证据：[全量类型与回放](validation/type_hierarchy_v1_checks.json)、
[参考与目标](validation/type_hierarchy_v1_reference_checks.json)、
[液体回归](validation/type_hierarchy_v1_liquid_checks.json)、
[备餐审计](validation/type_hierarchy_v1_cooking_checks.json)。
计数仅覆盖 287 道正式任务，7 道隔离任务及历史去重归档不属于正式评测集。

可重跑的离线检查（先安装 `.[dev]`）：

```sh
python -m unittest discover -s tests -v
python scripts/build_liquid_domain.py --check
python scripts/check_domain_types.py
python scripts/check_reference_plans.py
python scripts/audit_liquid.py
python scripts/audit_cooking_goals.py
ahat-benchmark doctor
python scripts/check_release.py
```

check_domain_types.py 已加入 CI；它覆盖所有正式场景及每个参考步骤，独立解析器
作为开发依赖，不增加运行评测所需的依赖。检查证明当前 VAL、pddl 0.4.6 和
项目回放器的兼容性，不代表已验证所有外部规划器。

sdist/wheel 构建及发布文件检查通过；在独立环境中安装 wheel、离开源码目录后，
doctor、全部 287 条参考、50 组目标检查及混合 domain 模拟裁判流程通过。
安装包的参考无关推理导出及液体逐步回放也通过，见
[安装包验证](validation/type_hierarchy_v1_package_checks.json)。

两个 domain 的哈希及生成的 PDDL 类型声明均已改变。应重新导出推理输入、生成
带新 domain ID/hash 的结果，并使用新的评测目录；旧缓存不能复用。项目仍为未发布
2.3.0，未运行真实 LLM 裁判或重新测量算法排名。空间防环和通用关闭容器可访问性
不属于本次类型修复。
