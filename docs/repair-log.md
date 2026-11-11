# AHAT Benchmark 修复记录

本文件持续记录 ahat-benchmark 的数据、参考标注及评测实现修复。每次修复追加一条记录，包含问题证据、具体修改、验证结果和受影响文件；尚未完成的检查应明确标为“未验证”。

## 记录约定

- 任务以稳定的 `id` 为主键，同时记录数据集和从 **0 开始**的索引。JSONL 行号从 1 开始，等于源索引加 1；不同 split 的索引不一定等于源索引。
- `benchmarks/ahat_eval_set.jsonl` 中的 `plan` 是参考计划；可选的 `reference_goal` 是 PDDL 谓词字符串列表，列表内目标必须同时成立。正谓词 `(is_clean sink_6)` 表示该水槽的 `is_clean` 为 `true`。
- 运行时 `cases.json` 仅保留 `id`、`instruction`、`scene_graph`。修复场景时同步对应 split；参考计划和参考目标保留在 JSONL 中。
- 本地修订保留真实的上游 revision 和 source SHA-256；在 `benchmarks/hf_sync.json` 记录本地修订及实际 artifact 哈希，并更新受影响 split 的版本和 manifest。
- 区分“动作有效”和“目标达成”：常规 VAL 检查使用空目标，不能单独证明 `reference_goal` 已达成。验证参考目标时，应将其作为合取目标写入 PDDL problem 再运行 VAL。
- 修改场景或评测协议后，使用新的评测输出目录。文档中的验证结果属于对应修复时点。
- 删除记录后，历史索引和行号不再代表当前位置；FIX-001、FIX-002 及 FIX-003 的原索引均基于精简前的 348 条快照，当前定位使用稳定 ID。

## 修复索引

| 编号 | 日期 | 问题 | 影响范围 | 状态 |
| --- | --- | --- | --- | --- |
| FIX-001 | 2026-11-04 | 清理水槽任务的目标初始已满足，参考计划缺少清洁动作 | ahat-easy 索引 39、70 | 本地修复完成，验证通过 |
| FIX-002 | 2026-11-04 | 明确清洁所有浴室水槽，并补齐四水槽参考目标与计划 | ahat-easy 索引 54、70 | 本地修复完成，验证通过 |
| FIX-003 | 2026-11-04 | 精简取饼干、送水、取方便面的重复指令实例 | ahat-easy 删除 3 条，总数 348 → 345 | 本地精简完成，验证通过 |
| FIX-004 | 2026-11-10 | 修复邻接关系生命周期、统一 scene/PDDL，并区分必需和可选相邻摆放 | 新领域与 rubric；新增 10 道任务，总数 345 → 355 | 本地修复完成，离线验证通过 |
| FIX-005 | 2026-11-11 | 未声明对象、参数类型不兼容被误记为 VAL 系统错误 | VAL 参数预检查与协议版本 | 本地修复完成，离线验证通过 |
| FIX-006 | 2026-11-11 | 烹饪设备分支混用、炊具属性缺失及 cooked/heated 语义不分 | domain、294 个场景、4 条参考计划及 rubric | 本地修复完成，离线验证通过 |
| FIX-007 | 2026-11-11 | 区分参考目标可达与充分，审查烹饪任务的完整供餐和份量语义 | 调查 27 个备餐候选，仅完善 2 组目标和 1 条计划 | 本地修复完成，离线验证通过；25 条候选保留待审 |
| FIX-008 | 2026-11-11 | D3 的 prepare dinner 示例只列摆桌，备餐与布置口径不清 | D3 提示词、rubric 版本及哈希 | 本地修复完成，离线验证通过；未运行真实裁判 |
| FIX-009 | 2026-11-11 | 温热早午餐参考目标漏 cooked，允许温热生鸡蛋 | 1 条参考目标、幂等脚本及反例控制 | 本地修复完成，离线验证通过 |
| FIX-010 | 2026-11-11 | 按统一抽象移除熟度区分，仅用 heated 表示热处理结果 | domain、7 个场景、4 组参考目标、3 条计划及四维 rubric | 本地修复完成，离线验证通过 |
| FIX-011 | 2026-11-11 | 两人热早餐／温热早午餐缺少可传给 D1 的份量事实 | 2 个食物节点、2 组参考目标、domain 静态谓词和 D1 提示词 | 本地修复完成，离线验证通过 |
| FIX-012 | 2026-11-11 | 备餐指令语义及部分场景高度重复，同类任务过多 | 23 道候选保留 7 道，删除 16 道 open 变体；355→339 道 | 本地精简完成，离线验证通过 |
| FIX-013 | 2026-11-11 | 剩余两人／群体用餐缺份量声明，末态不能独立证明前序阶段 | 4 个场景、静态群体容量、D1/D3/D4；另整理 85 道液体指令 | 本地修复与分类完成，离线验证通过 |
| FIX-014 | 2026-11-11 | 四类液体任务数量过多，且上一轮分类有一处索引错误 | 四类各保留 6 道，删除 43 道；339→296，液体 85→42 | 本地精简完成，离线验证通过 |

## FIX-001：修正水槽初始状态、参考目标和参考计划

### 问题与定位

两条指令要求清理浴室水槽，但浴室中的水槽初始均为 `is_clean: true`。原参考计划仅移动到清洁工具并拿起工具，没有执行清洁。领域中的 `clean_furniture` 要求目标满足 `(not (is_clean ?f))`，因此无法直接对已干净的水槽执行该动作。

| 源索引 / easy 索引 | JSONL 行号 | 任务 ID | 指令 |
| --- | --- | --- | --- |
| 39 / 39 | 40 | `913ca94e-5eb2-44ec-8c82-867844780d57` | `Clean the sink in bathroom.` |
| 70 / 70 | 71 | `fa3376d5-18a6-41e1-9a80-42bdb5349c75` | `Clean the sink in the bathroom.` |

### 修改内容

按指定修复范围修改初始状态，保留任务 ID、指令及其他场景内容：

| 任务索引 | 对象及位置 | 修改前 | 修改后 | 新增 `reference_goal` |
| --- | --- | --- | --- | --- |
| 39 | `bathroom_3/sink_6` | `is_clean: true` | `is_clean: false` | `["(is_clean sink_6)"]` |
| 70 | `bathroom_1/sink_4`、`bathroom_1/sink_5` | 两者均为 `is_clean: true` | 两者均为 `is_clean: false` | `["(is_clean sink_4)", "(is_clean sink_5)"]` |

任务 39 的完整修复后参考计划（原计划仅含前两步）：

```lisp
(navigate agent_0 bathroom_3 cleaning_sponge_29)
(pick_from_surface agent_0 cleaning_sponge_29 sink_6)
(navigate agent_0 cleaning_sponge_29 sink_6)
(clean_furniture agent_0 cleaning_sponge_29 sink_6)
```

任务 70 的完整修复后参考计划（原计划仅含前两步）：

```lisp
(navigate agent_0 kitchen_7 cleaning_cloth_10)
(pick_from_surface agent_0 cleaning_cloth_10 sink_4)
(navigate agent_0 cleaning_cloth_10 sink_4)
(clean_furniture agent_0 cleaning_cloth_10 sink_4)
(navigate agent_0 sink_4 sink_5)
(clean_furniture agent_0 cleaning_cloth_10 sink_5)
```

### 同步与溯源

- [源评测集](../benchmarks/ahat_eval_set.jsonl)：仅修改索引 39、70 的上述初始状态及 `plan`，新增各自的 `reference_goal`。
- [easy 快照](../benchmarks/ahat-easy/cases.json)：同步三个水槽的初始状态。
- [easy manifest](../benchmarks/ahat-easy/manifest.json)：版本从 `1.2.0` 更新到 `1.2.1`，更新数据哈希，记录两个修复 ID。
- [HF 溯源清单](../benchmarks/hf_sync.json)：新增本地修订 `sink-cleaning-v1`，更新实际文件哈希；保留上游 revision 和原始文件哈希。
- [发布检查](../scripts/check_release.py)：支持区分上游原始哈希与本地修订后的 artifact 哈希，并检查记录的 artifact。
- [数据说明](datasets.md)、[README](../README.md)、[CHANGELOG](../CHANGELOG.md)：记录本地修订及参考目标格式。

### 验证结果

验证使用当前领域 `ahat-v3-physobj-floor-cleaning` 和仓库附带的 VAL：

| 检查 | 结果 |
| --- | --- |
| 修复后的全部参考计划动作有效性 | 348/348 通过（easy 146、medium 94、open 108） |
| 将 `reference_goal` 写入 PDDL problem 后验证新计划 | 两条均通过，目标水槽最终均干净 |
| 修复后的初始场景 + 原两步计划 + 相同目标 | 两条均未达成目标，确认清洁步骤必需 |
| 数据改动范围及 source/split 一致性 | 仅两条源记录变化；场景仅改变指定三个水槽；easy 快照与源记录投影一致 |
| `PYTHONPATH=src python -m unittest discover -s tests -v` | 41 项通过 |
| `PYTHONPATH=src python -m ahat_benchmark doctor` | 通过 |
| `python scripts/check_release.py` | 源文件检查通过；此次未检查构建分发包 |
| `git diff --check` | 通过 |

修复完成于本地工作区；本记录不代表已发布到 GitHub 或 Hugging Face。新增参考目标用于数据标注，此次未将它接入运行时自动评分，也未重新运行 LLM 评分。

## FIX-002：明确全部浴室水槽的清洁范围

- 日期：2026-11-04
- 范围：源评测集 / ahat-easy 的 0-based 索引 54、70
- 关联记录：FIX-001；本次更新其任务 70 的指令。

### 问题与修改

任务 70 的指令使用单数，但参考目标和计划要求清洁两个水槽。任务 54
原参考计划只清洁一个水槽；按用户要求，改为清洁所有浴室水槽，其中四个初始为脏。

| 索引 / ID | 原指令 | 新指令 | 参考目标与计划 |
| --- | --- | --- | --- |
| 54 / `8c934a7d-48a8-4069-b6cf-3e9fb9451316` | `Clean the sink in bathroom.` | `Clean all the sinks in the bathrooms.` | 新增四个目标：`sink_51`、`sink_53`、`sink_54`、`sink_56` 均为干净；计划由 4 步扩展为 10 步 |
| 70 / `fa3376d5-18a6-41e1-9a80-42bdb5349c75` | `Clean the sink in the bathroom.` | `Clean all the sinks in the bathroom.` | 保留双水槽参考目标和 6 步计划 |

任务 54 使用复数 `bathrooms`，明确覆盖 `bathroom_2` 和 `bathroom_3` 中的脏水槽。
其余浴室水槽 `sink_50`、`sink_55` 初始已干净。场景初始状态不变。

任务 54 的完整参考计划：

```lisp
(navigate agent_0 bathroom_2 cleaning_cloth_19)
(pick_from_surface agent_0 cleaning_cloth_19 sink_50)
(navigate agent_0 cleaning_cloth_19 sink_51)
(clean_furniture agent_0 cleaning_cloth_19 sink_51)
(navigate agent_0 sink_51 sink_53)
(clean_furniture agent_0 cleaning_cloth_19 sink_53)
(navigate agent_0 sink_53 sink_54)
(clean_furniture agent_0 cleaning_cloth_19 sink_54)
(navigate agent_0 sink_54 sink_56)
(clean_furniture agent_0 cleaning_cloth_19 sink_56)
```

### 同步与溯源

- 同步源 JSONL 和 easy split 的指令；参考目标和计划保留在源 JSONL。
- easy manifest 更新为 `1.2.2`，本地修订更新为 `sink-cleaning-v2`，同步 artifact 哈希。
- 保留上游 revision 和 source 哈希；更新 CHANGELOG 和数据说明。

### 验证结果

| 检查 | 结果 |
| --- | --- |
| 54、70 的参考计划动作有效性 | 两条均通过 VAL |
| 将完整 `reference_goal` 作为合取目标写入 PDDL problem | 两条均通过 VAL，分别满足 4 个、2 个目标 |
| 不完整计划对照：54 仅原 4 步、70 仅前 2 步 | 均无法满足完整参考目标 |
| 根据领域效果重放后的全部浴室水槽状态 | 54 的 6 个水槽均干净（含初始已干净的 2 个）；70 的 2 个水槽均干净 |
| 本次修改范围 | 54 仅修改指令、参考目标和计划；70 仅修改指令；场景不变 |
| easy split 与源数据投影一致性 | 146/146 一致 |
| `python scripts/check_release.py` | 通过；未检查构建分发包 |
| `git diff --check` | 通过 |

未运行 LLM 评分，未发布到 GitHub 或 Hugging Face。

## FIX-003：精简三组重复指令实例

- 日期：2026-11-04
- 范围：ahat-easy；按用户要求，取饼干、送一杯水、厨房拿方便面各保留一条。
- 关联记录：保留 FIX-001、FIX-002 的全部修改；其历史索引不随本次删除重写。

### 选择与修改

这些指令的场景并非完全重复，本次为指定范围的实例精简。
以下索引均为精简前源 JSONL / easy split 的 0-based 索引。

| 任务 | 删除 ID / 原索引 | 保留 ID / 原索引 | 保留依据 |
| --- | --- | --- | --- |
| 柜子取饼干 | `921cf3ea-7615-4272-b50a-700cd2a39230` / 45 | `b87dc669-7852-4267-8d4e-7dd2fd167f4a` / 115 | 两条均需开柜，保留家具候选更多的场景（93 对 72），参考计划 5 步。 |
| 送一杯水 | `f496da5a-81d0-4c4a-a1d0-04d61aee0e1d` / 142 | `78caec8e-5332-4cd0-82f1-0550a430df58` / 80 | 保留从餐桌取杯、到厨房水槽装水、交付给人的场景，参考计划 6 步。 |
| 厨房拿方便面 | `1e347a4c-ab36-4e80-9008-1d3e3ecaaeee` / 114 | `8f039a4c-e583-4152-82be-bce9d2112dfc` / 124 | 保留需要开柜并从柜内取物后交付的场景，参考计划 6 步。 |

仅从 JSONL 和 easy split 删除上述三条，其余记录的 ID、顺序及全部内容不变。
当前为 easy 143、medium 94、open 108，共 345 条。

### 同步与溯源

- easy manifest 版本更新为 `1.3.0`，更新数量和数据哈希。
- `hf_sync.json` 新增 `local_pruning`，记录版本 `repeated-instruction-pruning-v1`、删除/保留 ID、原索引及选择理由；同步数量、转换说明和 artifact 哈希。
- 保留上游 revision、原始 SHA-256 及已有 `local_corrections`。
- 更新 README、数据说明、CHANGELOG 及发布检查的预期数量。
- 历史验证报告仍对应原 348 条快照。新旧全量平均分不能直接比较；旧推理结果中的删除 ID 会被拒绝，需按当前任务集合生成输入并使用新的输出目录。

### 验证结果

- 已确认仅删除指定 3 条，其余 345 条与修改前完全一致；三个 split 与源数据投影一致，三个指定指令各只剩一条。
- 全部 345 条参考计划通过 VAL 动作有效性检查；本次未新增目标达成或 LLM 质量判断。
- `PYTHONPATH=src python -m unittest discover -s tests -v`：41 项通过。
- `PYTHONPATH=src python -m ahat_benchmark doctor`：通过，三组数量及哈希一致。
- `PYTHONPATH=src python examples/offline_demo.py`：通过。
- `python scripts/check_release.py`、`git diff --check`：通过；未构建或检查分发包。
- 未运行 LLM 评分，未发布到 GitHub 或 Hugging Face。

## FIX-004：统一邻接关系与任务要求，扩充显式相邻任务

- 日期：2026-11-10
- 范围：`next_to` 场景表示、初态转换、动作效果、scene 更新、末态模拟、四维 rubric 和显式任务覆盖。
- 关联记录：FIX-001～FIX-003 的修改全部保留；原 345 条任务的指令、场景和计划保持一致，原 laptop 相邻任务仅增加目标标注。

### 问题与修改

1. 拿起物体后旧 `next_to` 未删除，导致 3 条参考计划存在与支撑位置不符的残留关系。领域中的两类拿起动作新增 typed `forall` 效果，删除该物体在该支撑位置参与的双向邻接，保留无关物体对。
2. scene 使用 `links` 字典 `{relation: next_to, obj1, obj2, location}`；单条关系规范化为一个无向记录，并转换成双向 PDDL 事实。初态检查对象存在、不同名、同表面或同容器且非持有状态；不从共位置推断邻接，也不推断传递性。不完整旧列表和写入 states 的 next_to 明确报错。
3. SceneGraphManager 和 PDDL 末态模拟器共享类型解析及无条件量化效果展开；以同时删除/添加方式更新。D2 摘要支持列表/字典位置链接与初始邻接，不再因字典链接而构造失败。
4. 四维提示词区分任务要求：显式相邻缺失影响目标完整达成；未要求时，合法的额外相邻不算错误，缺少相邻也不算失败，不能仅靠 next_to 获得奖励或替代其他任务目标。按指令要求重排或清理不视为自相矛盾。
5. 新增 10 道独立本地任务（6 easy、4 medium），显式相邻题从 1 道增至 11 道。覆盖桌面、容器内、初始关系保留、旧关系撤销、多目标及搬走后在新支撑上重建关系。定义与稳定 ID 由 `scripts/next_to_cases.py` 确定性生成，详见 [任务清单](next-to.md)。
6. 原题 `ab270610-f68d-4ccf-8ced-455a237f8dc5` 增加玻璃杯、冰容器及饮料瓶分别在 laptop_1 旁的三个 reference_goal；不将邻接传递关系当作满足目标。

### 同步与溯源

- 开发版本 `2.3.0`；领域 `ahat-v4-next-to-consistency`；裁判协议 `ahat-rubric-next-to-v1`。新提示词为本地修订，不再声称逐字保持论文原文。
- 数据总数 355（easy 149、medium 98、open 108）；split 版本分别为 `1.4.0`、`1.3.0`、`1.2.1`。open 数据字节不变，manifest 更新反映领域升级。
- 保留 HF 原始 revision/source/domain 哈希，实际本地领域另记 `local_domain`；新增任务记为 `local_authored`，记录生成脚本和哈希，与上游 provenance 区分，采用相同 CC BY-NC 4.0 数据许可。
- 同步 package/citation/benchmark manifest、split 和 artifact 哈希、发布检查、贡献与来源文档。历史论文快照及验证报告不重写。

### 验证结果

- 50 项单元/集成测试通过，覆盖初态规范化、双向且不传递、非法初态、两类拿起清理、无关关系保留、普通放回不恢复、scene/PDDL 对照与字典链接裁判输入。
- 全部 **355/355** 条参考计划通过 VAL；14 条带 reference_goal 的记录全部满足合取目标。
- 11 道显式相邻任务，把参考计划中的相邻放置替换为普通放置：动作均有效，但全部无法满足完整相邻目标。
- 独立对照：仅要求放到桌面时，普通放置与合法相邻放置均达成目标；显式要求相邻时，仅相邻放置达成目标。
- 新增 10 道参考计划的 **61/61** 个动作步骤，SceneGraphManager 更新后重新生成的 PDDL 与领域效果模拟状态逐步一致。
- 源/split 投影一致，原 345 条记录仅有上述单条 reference_goal 注释变更；新增记录与生成脚本一致。
- `scripts/check_reference_plans.py` 已加入 CI；[机器验证结果](validation/next_to_v1_checks.json) 记录数据、领域和实现哈希。
- `doctor`、离线示例和发布源文件检查通过；sdist/wheel 构建与两类分发包内容检查通过。在仓库外以已安装 wheel 运行 doctor、离线示例及新增 10 题的 VAL、目标和 scene 重放检查，均通过。

未重新运行真实 LLM 评分；离线检查不能证明裁判模型的实际遵循程度或历史分数改变多少。此次不将 reference_goal 接入运行时评分覆盖逻辑。采用新任务集合、领域或提示词时，应生成对应推理输入并使用新的评测输出目录。

## FIX-005：在调用 VAL 前识别非法对象与参数类型

- 日期：2026-11-11
- 范围：`src/ahat_benchmark/val/validator.py`、validator 协议标识及评测文档。
- 关联记录：保留 FIX-001～FIX-004；本次不修改 domain、scene、任务数据或 rubric。

### 问题与修改

原预检查只覆盖动作名和参数个数。计划引用不存在的 `ghost_1` 时，native VAL 返回进程错误；把 agent 当作 navigate 的 location 参数时可能超时。这两类确定的计划错误因而被计入 system_errors，阻止结果汇总发布。

现在在启动 native VAL 前，对所有动作的每个参数执行以下检查：

- 从实际生成的 PDDL problem 的 `:objects` 及 domain 的 `:constants` 读取声明，不以未经筛选的 scene 名称代替。
- 检查对象是否已声明，并根据 domain 的类型继承关系判断参数兼容性；沿用 PDDL 大小写不敏感的匹配。
- 未声明或类型不兼容均返回 `invalid`，附 `invalid_action`、可读原因和结构化 `argument_error`。后者包含错误类别、从 1 开始的参数位置、形参名、实参、预期类型与实际类型。
- 这些计划按现有规则计零分，不调用裁判，也不计作系统故障。真实的进程失败、超时及 scene/problem 构造失败仍保留原系统错误分类。

### 同步与溯源

validator 协议从 `full-scene-val-next-to-v2` 升级为 `full-scene-val-typed-arguments-v3`，同步 `benchmark_manifest.json`、评测说明和 CHANGELOG。package 继续使用尚未发布的 2.3.0。历史验证证据不重写；升级后使用新的评测输出目录，旧检查点不能直接续跑。

### 验证结果

- `PYTHONPATH=src python -m unittest discover -s tests -v`：56 项通过，新增 6 项测试，覆盖非法对象/类型的提前拒绝、实际对象声明、类型继承与大小写、domain 常量、场景构造故障保留，以及端到端零分和无 system_errors。
- 既有 native 无判决错误及超时回归检查通过；未将这些真正的系统错误改判为 invalid。
- `scripts/check_reference_plans.py`：355/355 条参考计划通过 VAL；14/14 条参考目标、11/11 个邻接反例控制及 61/61 步 scene/PDDL 对照通过，无失败。当前机器记录保留在本地 `outputs/typed-arguments-v3/reference_checks.json`。
- `doctor`、发布源文件检查和 `git diff --check` 通过。本次未重新构建分发包、调用真实 LLM 或发布。

## FIX-006：拆分设备烹饪能力，区分食物、加热能力和处理结果

- 日期：2026-11-11
- 范围：domain、scene 属性、源/split、参考计划和目标、rubric、溯源及版本哈希。
- 关联记录：保留 FIX-001～FIX-005；任务数和指令不变。

### 问题与修改

原 cook_on_heating_device 用 OR 合并封闭设备与炉灶，封闭设备分支错误要求开门；全量 scene 没有 is_heating_container，炉灶烹饪不可用；动作也没有食物检查。原参考计划没有 cook，部分只开关设备，早餐案例还把 egg_carton 当作食物。

1. 三个 cook 动作分别检查 is_microwave、is_oven、is_cooking_surface；三个对应 heat 动作支持单独加热和复热。微波炉、烤箱要求关门且开机；炉灶要求耐热锅具及原有 food-on-container-on-device 关系。
2. is_food 表示实际食物；can_be_heated 表示允许加热。cook 要求二者并产生 cooked 和 heated；heat 只要求加热能力、只产生 heated，保留已有 cooked。开机不自动完成处理，初始已熟的冷菜可以 cooked=true、heated=false。
3. 幂等脚本 scripts/repair_cooking.py 按明确语义类型补标设备、锅具、食物；294 条 scene 变化（114 easy、74 medium、106 open）。181 个场景的 345 个对象有 is_heating_container。排除花盆、玩具和包装，不在运行时按名称推断属性。
4. 修正四条参考计划并新增目标：明确做早餐、热早餐、温热早午餐和烤箱复热 casserole。两条 carton 案例增加真实鸡蛋节点并显式取出；复热案例将该 casserole 明确为已经烹饪的冷菜。具体稳定 ID、修改和目标见 [烹饪说明](cooking.md)。其他 351 条计划及全部指令不变，不给取食物或摆桌任务追加 cooked 要求。
5. 四维 rubric 明确区分能力、cooked/ heated 结果、开关电源与实际处理；保留必需/可选邻接政策。reference_goal 仍只用于离线检查，不覆盖运行时评分。

### 同步与溯源

- 仍为未发布的 2.3.0；domain 升级 ahat-v5-cooking-and-heating，rubric 升级 ahat-rubric-cooking-v2；validator 保留 typed-arguments-v3。
- split 版本 easy 1.5.0、medium 1.4.0、open 1.3.0；数量仍为 149/98/108。同步源数据、split、manifest、HF local_cooking 记录、来源文档和发布说明。
- upstream revision/hash 保持准确，294 个修订 ID、节点名、四条参考修订、脚本及基础数据哈希单独溯源。旧 next-to 验证记录保留；新增 [当前机器检查](validation/cooking_v1_checks.json)。

### 验证结果

- 63 项单元/集成测试通过。覆盖六类处理动作、非法食物/设备/锅具、未开机、错误位置、开门处理拒绝、关门处理成功、熟食复热、开机不等于处理、初态及 scene 回写。
- 355/355 条参考计划通过 native VAL，18/18 条参考目标达成。4/4 条删除 cook/heat 的计划合法但不满足目标；11 个原邻接对照继续通过。
- 四条修订计划的 83/83 个步骤及原新增邻接计划的 61/61 个步骤，scene 转 PDDL 与模拟执行一致。
- 已确认任务 ID、指令和数量不变，其他 351 条参考计划不变；修订脚本再次运行报告 0 条待修改。
- doctor、离线示例、发布源文件检查和公开副本导出通过；sdist/wheel 构建及分发包检查通过。仓库外安装 wheel 后，doctor、离线示例及四条烹饪参考计划、目标、对照与 83 步 scene 重放检查通过。
- 液体仍使用原有容器/设备状态抽象，本次不增加液体温度模型；四维提示词不要求未声明的液体对象或温度事实。
- 未运行真实 LLM 评分，未对外发布；采用新场景、领域和提示词时需要重新生成推理并使用新的评测输出目录。

## FIX-007：审查 cook 相关任务的充分参考目标

- 日期：2026-11-11
- 关联记录：FIX-006；本次不改 domain、scene、指令、ID、任务数或 rubric。
- 完整逐题理由、两条新目标与完整计划见 [参考目标审查](cooking-goal-audit.md)。

### 问题与证据

294 是上次能力补标的场景数，不是烹饪任务数。人工审阅 355 条指令，筛出 27 道备餐／供餐候选，其中 4 道明确要求烹饪、复热或热食。另列 17 道餐桌／氛围、17 道准备／收纳和 33 道液体／饮品相关任务，不自动添加 cooked 要求。

旧 warm-brunch 目标允许把 cook 换成 heat：native VAL 判为合法且达到旧 goal，但鸡蛋 cooked=false。warm brunch 和 hot breakfast 的 “for two” 也没有食物份数或份量模型。目标可达不能证明完整指令已完成；两条旧标注保留为部分检查，本次不将其认证为充分条件。

### 修改内容

仅修改有充分语义依据的两条源记录：

| 源索引 | 稳定 ID | 目标与计划 |
| --- | --- | --- |
| 210 | `02a5f844-c663-4336-b6c9-fad5540b7cd5` | 完善 cooked、heated、餐桌、房间、关机及空手目标；利用唯一烤箱和初始已熟未热的场景前提确认指定处理方法。计划 19 → 16 步，明确加热后关机、取出、返回。 |
| 302 | `fd22ff41-4720-497c-bad3-7411b468b6cc` | 完善熟热鸡蛋、干净餐盘／餐桌及餐厅位置、关机和空手目标；保留已达成新目标的 16 步计划。 |

这两组是当前符号模型内的充分参考目标，不声称必要；运行时评分不要求所有方案达到这组目标。本次新增 reference_goal 字段为 0，完善已有目标 2 组，修改计划 1 条。其余 353 条源记录完全不变，其中 25 道备餐候选因餐食、份量或历史过程不确定而不修改。没有虚构食物、份数或液体状态。

### 同步与溯源

保留 FIX-006 的历史证据及 upstream hash。源 artifact 哈希和 hf_sync.json 的 local_cooking_goals 记录本次基础快照、确认 ID、脚本及清单哈希；split 投影与版本不变，仍为未发布的 2.3.0。repair_cooking.py 统一生成新目标／计划并保持幂等。新增审计脚本和逐题机器清单，可独立复查。

### 验证结果

- 写入前对独立候选快照通过 native VAL 计划／合取目标、6 个合法的不完整计划控制和 32 步 scene/PDDL 重放，并确认修改仅涉及两条已认证记录的参考字段，才写入源数据。
- 66 项单元／集成测试全部通过，包括移除 cooked 会放过生鸡蛋、增加新的 heated 产生动作会使语义前提检查失败的回归。
- 355/355 参考计划合法，18/18 参考目标达成；11 个邻接控制、4 个处理省略控制通过，烹饪 80 步和邻接 61 步重放一致。目标达成计数仍不等于所有 18 组都已认证充分。
- [本次语义前提与控制证据](validation/cooking_goal_checks.json) 和 [全量参考证据](validation/cooking_goal_reference_checks.json) 记录当前输入与实现哈希；不重写历史 cooking_v1_checks.json。
- 修订脚本复跑 0 条待修改；发布源文件检查、数据哈希检查和 git diff --check 通过。本次未重建分发包、运行 LLM 评分或发布。

## FIX-008：统一 D3 备餐与用餐环境布置的评分口径

- 日期：2026-11-11
- 关联记录：FIX-006、FIX-007；本次落实已有备餐语义要求，不扩展场景或食物份量模型。
- 完整政策及人工对照案例见 [D3 备餐说明](d3-meal-policy.md)。

### 问题与修改

旧 D3 用摆好 plates/utensils 说明 prepare dinner 的最低要求，未明确必须有可食用餐食，容易与 D1 的供餐目标及 FIX-007 的审查口径冲突。现删除该示例并明确：

1. 准备餐食必须使实际可食用餐食准备就绪；serve、host meal、meal service 等指令还需覆盖相应供餐或交付。
2. 只要求摆桌或营造用餐氛围时，不添加备餐、cook 或供餐要求；取食材、准备设备也不等于要求完成整餐。
3. 没有烹饪／温热要求时允许合理冷食或预制餐；不自行指定菜单、桌子、餐盘或餐具。需要 cook/heat 时沿用原处理规则，温热生鸡蛋不能代表准备好了可食用蛋餐。
4. 不从包装或空锅虚构食物、熟度或份量；显式 for two 要覆盖相应供餐人数，两只杯子或复数名称不是两份食物的证据，不给 family/guests 自行指定人数，也不要求未建模的数量谓词。
5. 对备餐指令，仅摆桌／装饰的 D3 最高 0.25；不适用“向主要意图取得进展至少 0.50”的兜底。对仅要求布置的任务，正常评价布置完成度。可选 next_to 和装饰不能补偿缺失的备餐或必要供餐。

### 同步与溯源

rubric 升级为 ahat-rubric-meal-completeness-v3，更新 prompts.py、benchmark_manifest.json 的版本及 D3 SHA-256，并同步 README、评测文档和 CHANGELOG。D1/D2/D4 提示词、分值集合、聚合权重与封顶规则、domain、所有源任务和 split 数据哈希不变。package 保持未发布的 2.3.0。历史机器验证文件保留原协议，不将其改写为本次评分证据。

提示词哈希属于 judge stage 的协议签名；旧 judge checkpoint 不能续跑到新口径，需使用新的 judge 输出目录。本次没有重跑真实 LLM，也没有宣称历史分数变化或裁判模型遵循率。

### 验证结果

- 67 项单元／集成测试通过；新增回归确认 D3 提示词变化时，在 API 调用或覆盖旧 checkpoint 前拒绝复用。
- doctor、发布源检查、manifest 提示词哈希和 git diff --check 通过；独立前后快照对比确认只有 D3 提示词和总体 rubric 版本／manifest 哈希变化，其他提示词、domain、源任务与 split 数据不变。
- [机器检查记录](validation/d3_meal_policy_checks.json) 标注离线检查范围。政策对照案例为人工审查材料，未用模拟裁判输出冒充语义验证。
- 本次未重建分发包、未改变参考 goal/plan、未运行真实评分或对外发布。

## FIX-009：修正温热早午餐的熟度参考目标

- 日期：2026-11-11
- 关联记录：FIX-006、FIX-007。纠正 FIX-007 将“整体两人份尚不可认证”与“局部漏 cooked”一同搁置的处理；后者是可独立修复的确定错误。
- 稳定 ID：`9027ed1b-fcf9-4f17-8b39-c397d4db7563`，源索引 293，open。
- 原指令：`Prepare a warm brunch for two.`，保持不变。

### 问题与修改

旧目标只有 heated 和餐桌位置等状态；把计划中的 cook 换成 heat 仍合法且达成目标，鸡蛋却未熟。当前选择的参考餐食是生鸡蛋，因此补 `(cooked breakfast_eggs_1)` 合理且必要。这里不是把所有 warm brunch 都强制成鸡蛋或 cook，也不排除其他温热熟食方案。

完整新参考目标如下；原 24 步计划已 cook，无需改动。

```lisp
(cooked breakfast_eggs_1)
(heated breakfast_eggs_1)
(item_on_surface breakfast_eggs_1 dining_table_21)
(item_on_surface butter_54 dining_table_21)
(item_on_surface fruit_bowl_48 dining_table_21)
(not (is_powered_on stove_16))
```

两人份仍缺少明确表示：食物节点是聚合对象，初态未声明份数，不能判断份量足够或不足。因此该目标仍是部分检查，未扩大两道已认证充分目标的集合。模型缺少证据不等于已证明该餐不够两人吃。后续可用明确的两份食物节点或静态“足够两份”属性表达，不必引入重量、营养或复杂分餐模拟。

### 同步与溯源

仅修改这一条源记录的 reference_goal。原计划、指令、scene、全部运行时 split、domain 和 rubric 均保持本次修改前的哈希；package 仍为未发布的 2.3.0。更新幂等修订脚本、source artifact 哈希和 hf_sync.json 的 local_warm_brunch_goal 溯源。保留 FIX-007 的逐题清单和历史证据，审查说明加注后续修复，避免重写历史检查结果。

### 验证结果

- 写入前对候选快照确认原参考计划达到新目标；合法的 heat-only 反例达到旧目标但达不到新目标，且 cooked=false。
- 68 项单元／集成测试通过，含删除温热早午餐 cooked 目标会被审计拒绝的回归。
- 355/355 参考计划合法，18/18 已标注目标达成；11 个邻接控制、4 个处理省略控制通过，80 步烹饪和 61 步邻接重放一致。
- [目标与反例检查](validation/warm_brunch_goal_checks.json)、[全量参考检查](validation/warm_brunch_reference_checks.json) 记录当前输入和实现哈希。
- 幂等检查 0 条待修改，发布源文件检查及 git diff --check 通过。未运行真实裁判或发布。

## FIX-010：统一热处理，仅保留 heated

- 日期：2026-11-11
- 用户要求：不区分初始熟食，只用 heated 表示食物或者其他物品的状态。
- 关联记录：替代 FIX-006～FIX-009 中 cooked/heat 分立及初始熟食的语义；保留历史证据。FIX-008 的备餐／布置区分继续有效。
- 当前完整语义、动作和迁移说明见 [heated-v2](heated.md)。

### 修改内容

1. 删除 domain 的 cooked 谓词和三个 cook 动作；保留 heat_with_microwave、heat_with_oven、heat_on_heating_device。三者统一检查 can_be_heated、尚未 heated、对应设备、开机、位置及空手。封闭设备仍须关门，炉灶仍须合适锅具。食物与非食物使用同一规则，is_food 只保留描述身份，不作为热处理前提。
2. 统一效果为 heated=true；开机仍不自动完成处理。不模拟生熟、初始熟度、冷却、重复加热周期或液体温度传递。原 cooked=true 不转换成 heated=true。
3. 删除三个场景的 cooked 属性；casserole 类型改为 casserole_dish，表示食物对象而不标初始熟度。另外四个场景共五个旧 is_heated=false 迁移为 heated=false。共七个场景变化，原指令、对象 ID 及任务数量不变。
4. 四道处理任务去掉 cooked 目标，去重后以 heated 作为唯一处理结果。三条早餐／早午餐计划的 cook 步骤重命名为对应 heat，烤箱计划已用 heat 不变。共八条源记录变化（easy 1 / medium 4 / open 3），其余 347 条记录完全不变。
5. 四维 rubric 同步接受用 heat 完成烹饪、温热和复热，不再要求熟度谓词或将热处理鸡蛋判为“尚未做熟”。保留真实食物与包装区分、备餐与摆桌区分、显式人数和必需／可选邻接政策。FIX-009 的生鸡蛋反例在新抽象下退役，改用“省略热处理”反例；两人份仍为未表示的独立条件。

### 同步与溯源

- domain 升级 ahat-v6-heated-only，rubric 升级 ahat-rubric-heated-v4。package 保持未发布 2.3.0；validator 保留 typed-arguments-v3。
- split 版本 easy 1.6.0、medium 1.5.0、open 1.4.0；同步 source、split、manifest、domain／prompt／artifact 哈希。
- hf_sync.json.local_heated 记录本次基础源哈希、八条修订记录、脚本与审计哈希。旧 local_cooking、local_cooking_goals、local_warm_brunch_goal 及验证文件保留为历史记录，不改写其原始语义。
- 修订脚本保持幂等；当前审计脚本拒绝旧 cooked 状态／目标与 cook 动作，并重新验证统一模型下两道充分参考目标。旧调查文档加历史快照说明，当前说明和公开入口指向 heated-v2。
- 动作及提示词协议已变化，采用新输出目录重新生成推理与评分；未运行真实 LLM 评分或对外发布。

### 验证结果

- 写入前先在候选快照检查新目标、热处理／供餐／关机／返回反例及 scene 重放，再写入数据。当前审计验证迁移与确定性脚本一致，全部任务 ID、指令和 split 不变。
- 69 项单元／集成测试通过。覆盖三种设备上食物／非食物产生同一 heated 结果、能力／设备／锅具／位置／空手／关门约束、初始 heated、拒绝旧动作、开机不等于处理、旧状态迁移不虚构加热、幂等性、scene 回写和参考目标反例。
- 355/355 参考计划合法，18/18 已标注目标达成；11 个邻接控制、4 个处理省略控制通过；80 步热处理参考及 61 步邻接参考的 scene/PDDL 重放一致。两道确认目标另有 6 个合法的不完整方案控制，早午餐的省略热处理控制也通过。
- doctor、离线示例、发布源及分发包检查通过；sdist/wheel 构建成功。隔离环境安装 wheel 后通过 doctor、四道处理参考目标及 80 步 scene 重放、离线示例。离线示例使用模拟回复，不是评分语义证据。
- 修订脚本复跑报告 0 条待修改。当前 [目标审计](validation/heated_v2_goal_checks.json)、[全量参考检查](validation/heated_v2_reference_checks.json) 和 [迁移／构建检查](validation/heated_v2_migration_checks.json) 记录新输入及实现哈希。

## FIX-011：声明两人份食物容量，并传递给 D1

- 日期：2026-11-11
- 状态：本地修复完成，未发布；未运行真实 LLM 裁判
- 范围：open 中两人热早餐和温热早午餐；关联 FIX-007、FIX-010

### 问题与证据

先前鸡蛋是聚合食物节点，未声明足够几人食用。两个餐位、包装名称和复数名称不能证明两人份，
也不能据此断言只够一人。按用户授权，在这两个具体场景显式设计 `serves_two=true`，
表示整个食物对象足够两人；这是本地场景补充，不声称从上游恢复了实际重量。

### 修改内容

| 任务 ID | 原指令（不变） | 补标食物 |
| --- | --- | --- |
| `4bddb476-f1ae-44e1-9558-add1571dd936` | Make a hot breakfast for two. | `eggs_116` |
| `9027ed1b-fcf9-4f17-8b39-c397d4db7563` | Prepare a warm brunch for two. | `breakfast_eggs_1` |

domain 声明一元静态谓词 `(serves_two ?o - physobj)`；无动作增删它。现有布尔状态转换
将其写入 initial PDDL，执行保留该事实，D1 在 final PDDL 中看到它。scene 回写也保留该属性。
D1 提示词解释：允许共享供餐，无需强制分盘；份量属性不替代 heated、准备和供餐条件，
未标注表示未知容量，无人数要求时不给额外奖励。只改 D1；D2/D3/D4 提示词和实际输入不变。
没有给其他备餐任务、包装或伴餐自动推断份量，没有添加重量、食用消耗或分餐模型。

两条参考计划均保持不变。热早餐的新完整合取目标：

```lisp
(heated eggs_116)
(item_on_surface eggs_116 dining_table_19)
(item_on_surface yogurt_cup_33 dining_table_19)
(item_on_surface milk_114 dining_table_19)
(not (is_powered_on stove_26))
(serves_two eggs_116)
```

温热早午餐的新完整合取目标：

```lisp
(heated breakfast_eggs_1)
(item_on_surface breakfast_eggs_1 dining_table_21)
(item_on_surface butter_54 dining_table_21)
(item_on_surface fruit_bowl_48 dining_table_21)
(not (is_powered_on stove_16))
(serves_two breakfast_eggs_1)
```

本次解决这两条任务的份量证据缺口，不自动扩大历史审查清单中的两道完整充分目标认证集合。
运行时仍使用 rubric，reference_goal 不变成唯一方案或评分覆盖规则。

### 同步与溯源

- domain `ahat-v7-serves-two`，rubric `ahat-rubric-serves-two-v5`；未发布 package 仍为 2.3.0。
- source 仅变更两条 open 记录，各增加一个食物属性和一个 goal 合取项；355 个 ID、指令、计划和 split 均不变。
- split 版本 1.6.0/1.5.0/1.5.0；easy/medium 数据字节不变，全部 manifest 同步当前 domain/hash。
- `hf_sync.json.local_serves_two` 保存基础源哈希、精确食物映射、语义和脚本哈希；此前 local 修订记录原样保留。
- 更新公开文档、提示词哈希与幂等修订脚本。采用新的评测输出目录；没有发布或运行真实评分。

### 验证结果

- 写入前候选审计通过，逐记录对比确认只增加两处属性和两处目标，计划／指令不变。
- 74 项测试通过；模拟客户端检查两条任务实际发送给 D1 的请求同时包含份量、heated 和供餐位置。
- 两条新目标由原计划达到；去掉容量声明后计划仍合法但目标失败；保留容量而省略加热或供餐也失败。
- 355/355 参考计划合法，18/18 参考目标达成；11 个邻接控制、4 个处理省略控制通过；80 步处理参考和 61 步邻接参考的 scene/PDDL 重放一致。
- 比较实际 build_inputs 及提示词哈希，D2/D3/D4 均不变；修订脚本幂等，doctor 和发布源检查通过。
- sdist/wheel 构建及包内容检查、隔离安装验证通过；安装包内两条容量事实到达 D1，四条处理参考目标和 80 步重放通过。
- 当前证据：[目标审计](validation/serves_two_goal_checks.json)、[参考检查](validation/serves_two_reference_checks.json)、[迁移检查](validation/serves_two_migration_checks.json)；[语义说明](serves-two.md)。模拟回复只验证证据通路，不代表真实裁判评分。

## FIX-012：按语义覆盖精简备餐任务

- 日期：2026-11-11
- 状态：本地精简完成，未发布；未运行真实裁判
- 范围：16 道 open 变体；关联 FIX-007、FIX-011

### 问题与证据

其余 23 道备餐候选包含 12 道晚餐、9 道早餐、2 道早午餐，其中明确两人用餐的 7 道是子集。
大量差异集中在 prepare/host/make 和 cozy/comforting/elegant/hearty/full 等措辞。
场景也存在复用：260/330 完全相同；303/338 完整节点重合率为 99.3%，249/292 为 98.4%。
重合率按包含类别、名称和全部属性的完整节点集合计算 Jaccard，不是语义模型分数。
不同 scene 也可能测试近似能力，因此精简明确接受减少部分布局覆盖，不声称所有任务等价。

用户选择“按建议按语义去重，23 道保留 7 道”。完整原指令、稳定 ID、相似度及删除映射
见 [备餐去重记录](meal-pruning.md) 和 [批准清单](validation/meal_pruning_inventory.json)。

### 修改内容

保留以下七道（索引来自去重前 355 条快照，从 0 开始）：

| 旧源索引 | 稳定 ID | 保留原指令 | 覆盖 |
| --- | --- | --- | --- |
| 243 | `a55dd1af-59ee-4e0c-8139-208e2134ed49` | Plan and serve a complete evening meal | 普通完整供餐 |
| 246 | `3cf1736a-3b96-4913-b9c5-df4688ee9053` | Prepare an elegant dinner and ambiance | 餐食与氛围组合 |
| 261 | `f3ee3e87-d782-4870-8ed3-2bc92f344010` | Host a cozy dinner for two tonight. | 两人晚餐 |
| 301 | `dec162ab-e453-419f-971a-2e32987350f2` | Prepare an elegant dinner for guests | 客人晚餐 |
| 303 | `0cf41a97-9f6a-4e13-8542-1def6889483d` | Host a cozy brunch for two. | 未明确要求热处理的两人早午餐 |
| 308 | `4a3dc074-3cd6-4241-a4a5-2c37f31c99a1` | Host a formal dinner and cleanup | 用餐后清理的过程约束 |
| 330 | `198fd035-6f65-4740-8b01-0643a215ccb4` | Prepare a full family breakfast service | 家庭早餐 |

删除旧源索引 238、240、249、254、255、260、268、269、270、273、279、284、292、300、327、338，
全部为 open。另保留原先修好的四道处理任务。备餐候选 27→11，明确两人用餐候选 9→4。
355→339 道（149/98/92）；所有存活记录的原始 JSONL 行、全部字段和顺序不变。

保留项仍需完善食物、份量、供餐与历史证据；精简不等于认证原参考计划完整。
本次没有新增 reference_goal，也没有修改任何存活 scene、指令或计划。

### 同步与溯源

- open split 1.5.0→1.6.0；easy 1.6.0、medium 1.5.0 的数据和 manifest 字节不变。
- domain `ahat-v7-serves-two`、rubric `ahat-rubric-serves-two-v5`、benchmark_manifest 均不变；package 仍为未发布 2.3.0。
- 同步 open cases/manifest、source JSONL、hf_sync 总数／split 数量／artifact 哈希。local_meal_pruning 保存删留 ID、原指令、逐记录哈希、迁移前后源哈希和脚本／清单哈希；历史 local 修订条目完全不变。
- 新增幂等 `scripts/prune_meal_cases.py`；热处理修订脚本保留较新的 split 版本，避免复跑时回退 open 版本。
- 历史 cooking_goal_inventory 保留；当前审计只排除已批准删除的 ID，对其他缺失仍报错。当前 11 道备餐候选保留历史“已确认 2 道、待完整认证 9 道”的分类。
- 更新当前公开数量、发布检查和测试；采用新推理与评测输出目录，旧 348/355 题均分不直接对比。

### 验证结果

- 写入前候选迁移通过；候选记录被修改、只删一部分、保留代表缺失这三个反例均被拒绝。
- 写入后源行逐字节过滤比对一致；339 条存活记录和相对顺序完全不变，全部 split 投影匹配。
- 74 项测试通过，339/339 参考计划合法，18/18 目标可达；11 个邻接控制、4 个处理省略控制和 80/61 步处理／邻接重放通过。
- 当前备餐审计核对 16 个批准删除项、11 个存活备餐候选及全部四道处理任务；幂等脚本复跑 0 条待删除。
- doctor、发布源／包检查、sdist/wheel 构建及隔离安装检查通过；安装包内包含 339 条记录、四道处理目标和两条 D1 份量事实，80 步处理重放通过。
- [迁移检查](validation/meal_pruning_migration_checks.json)、[目标审计](validation/meal_pruning_goal_checks.json)、[参考检查](validation/meal_pruning_reference_checks.json)。未进行真实裁判评分或发布。

## FIX-013：补齐用餐份量，明确前序阶段检查并分类液体指令

- 日期：2026-11-11
- 状态：本地修改完成，未发布；未运行真实 LLM 裁判
- 范围：4 个 open 场景、静态谓词和 D1/D3/D4 提示词；关联 FIX-011、FIX-012

### 问题与证据

去重后有 4 道明确两人用餐、2 道家庭／客人用餐。此前只给热早餐与温热早午餐的鸡蛋标注容量，
其余 4 道仍无份量声明。用户要求补齐食物状态，同时整理液体指令，并询问能否由其他维度检查前序步骤。

### 修改内容

| 稳定任务 ID | 原指令（不变） | 食物及新增容量 |
| --- | --- | --- |
| `f3ee3e87-d782-4870-8ed3-2bc92f344010` | Host a cozy dinner for two tonight. | `eggs_116`：serves_two=true |
| `0cf41a97-9f6a-4e13-8542-1def6889483d` | Host a cozy brunch for two. | `eggs_66`：serves_two=true |
| `198fd035-6f65-4740-8b01-0643a215ccb4` | Prepare a full family breakfast service | `eggs_90`：serves_group=true |
| `dec162ab-e453-419f-971a-2e32987350f2` | Prepare an elegant dinner for guests | `cheese_block_106`：serves_group=true |

新增静态一元谓词 serves_group：这份实际食物足够本场景指令所指的家庭／客人群体，
不擅自指定人数，也不声称足够任意大小群体。奶酪块本身是食物，局部补 is_food/can_be_heated；
四个目标均明确 heated=false，不凭容量虚构处理完成、熟度、菜单或供餐。其余包装／容器不推断内容。
经现有布尔属性转换，D1 可看到初态到末态保留的容量事实；scene 回写保留，动作不增删容量。
此前两道 serves_two 标注保持，因此六道用餐任务均有合适食物的容量证据。

原指令、plan 和 reference_goal 全部不变；四个新容量声明不认证原参考计划完成整条用餐指令。
例如两人早午餐的原计划仍未搬出鸡蛋，容量补标不代表已供餐。

D3 提示词明确检查必需前序阶段是否存在，D4 检查已出现阶段之间的明确／必要先后顺序；
缺少阶段不额外虚构导航冗余或顺序颠倒。用餐后清理不能由摆桌后撤桌或移动海绵替代用餐，
准备性清洗也不等于餐后清理。D1 不从末态桌面干净推断已用过餐，不要求临时供餐布置永久保留。
不添加模型没有的 eat/wait/host 动作。D2 提示词和四维输入格式均不变，D3/D4 不额外获得份量属性。

权重与聚合不变，没有硬性时序成功门槛。若只有 D3=0，其余维度为 1，加权分仍为 0.8；
本次补充的是可用证据与评分规则，不能声称前序阶段缺失必然整题失败或真实裁判一定遵循。

### 液体指令整理

逐题核对当前指令，按互斥主意图分为 9 类共 85 道：常温装水／交付 26、现成饮料取用 13、
热水 16、茶 5、咖啡 5、泛指温热饮品 2、浇植物／花瓶及相关装水 12、沐浴用水 4、方便面 2。
此前 33 道只是烹饪审查的保守筛查集，未包括常温水和大量现成饮料、植物用水任务。
另列 6 道相关器具上下文；咖啡桌、浴巾、空杯和取干方便面包装不自动引入液体处理要求。
只整理原指令和范围，不修改液体状态、动作、计划或目标；不从只开水壶、只准备杯子或取现成茶中强加完整冲泡要求。
完整指令、稳定 ID、类别和源哈希见 [液体分类](liquid-tasks.md) 及其机器清单。

### 同步与溯源

- domain `ahat-v8-group-portions`，rubric `ahat-rubric-portions-and-order-v6`；open 1.6.0→1.7.0，easy 1.6.0／medium 1.5.0 数据版本不变。
- 数据仍为 339（149/98/92）；只改变上述四个食物节点的状态。easy/medium 数据字节不变，全部 manifest 同步 domain/hash。
- local_group_portions 保存场景映射、基础源哈希、语义和修订脚本哈希；旧 local 修订条目保持原样。D1/D3/D4 提示词哈希更新，D2 不变。
- 修订脚本幂等，当前审计验证 serves_group 静态性、合法计划和容量事实，而不把单个容量事实认证为完整任务目标。
- 当前入口见 [份量与前序阶段说明](group-portions-and-order.md)。采用新场景推理和新评测输出目录，未对外发布。

### 验证结果

- 写入前逐字段核对候选：仅 4 个 scene 节点状态变化，所有 ID、指令、计划、目标、顺序保持不变。
- 78 项测试通过。新增检查覆盖实际模拟 D1 请求、容量 false／缺失反例、原计划上的 scene/PDDL 重放，以及两个 native 合法计划末态相同但前序阶段不同的证据对照。
- 339/339 参考计划合法，18/18 参考目标达成；11 个邻接控制、4 个处理省略控制及 80/61 步处理／邻接重放通过。四条新增容量事实均到达 D1，关闭容量声明的合法计划不再满足对应容量事实。
- 85 道液体分类的 ID、原指令、源数据哈希及旧 33 道覆盖全部核对通过。
- doctor、发布源和分发包检查、sdist/wheel 构建及隔离安装验证通过；安装包包含 4 个两人容量与 2 个群体容量，处理目标与重放通过。
- [迁移检查](validation/group_portions_migration_checks.json)、[目标审计](validation/group_portions_goal_checks.json)、[全量参考检查](validation/group_portions_reference_checks.json)。模拟请求和离线规则检查不是实际裁判评分证据。

## FIX-014：四类液体任务各保留六道代表

- 日期：2026-11-11
- 状态：本地精简完成，未发布；未运行真实裁判
- 范围：常温水、现成饮料、热水、植物用水共 67 道；关联 FIX-013

### 问题与证据

用户要求调查同类超过 10 道的液体任务，合并高度相似变体，尽量每类不超过 6 道。
原四类分别为 26、13、16、12 道，多数差别是饮料／容器名称、房间、措辞和场景布局。
两道“Fill the kettle ... and [then] power it on ...”指令字符序列相似度 96.9%，
动作名序列相同，但 scene 节点重合率约 0.34%，说明语义／流程重复不一定是场景复制。

上一轮液体分类误用 184 代替 176：把“取蔬菜和肉准备火锅”当成了装水开炉任务。
本次修正稳定 ID 映射，两道 benchmark 记录都保留；纠正后精简前液体总数仍为 85。
旧机器清单保留历史证据，当前分类使用 liquid_instruction_current.json。

### 修改内容

| 类别 | 原数量 | 保留 | 删除 | 重点保留差异 |
| --- | ---: | ---: | ---: | --- |
| 常温水装填／交付 | 26 | 6 | 20 | 交人、只装壶、柜内取杯、返回原处、卧室／厨房备好 |
| 现成饮料取用 | 13 | 6 | 7 | 台面／冰箱、零食组合、学习组合、节庆组合、明确 next_to |
| 热水及设备准备 | 16 | 6 | 10 | 完整分杯交付、炉上方法、柜内取壶、移动炉锅准备、仅开壶、保温瓶 |
| 植物／花瓶用水 | 12 | 6 | 6 | 单株、多株补水、仅装壶交人、花瓶返回、室外菜地、柜内取壶浇香草 |

其余五类保持 5/5/2/4/2 道。全量液体分类 85→42，全部九类均不超过 6 道。
全 benchmark 339→296（easy 149→130，medium 98→74，open 92）。
采用现有代表，不拼接指令，不修改存活记录任何字段；源 JSONL 行及相对顺序逐字节保留。
全部 18 组 reference_goal、11 道显式邻接和四道处理参考保留；份量标注保留。

按指令目标和必要步骤为主，结合 scene 初始状态与参考结构人工审查。删项映射代表说明
相近能力覆盖，不是逻辑等价或正确性认证；减少了部分场景布局、目的房间和措辞差异。
保留项原有指定取水位置、炉上加热方法、温度／成分问题仍需独立修复。
完整原指令、稳定 ID、保留理由、每条删除项的代表与相似度指标见
[审查记录](liquid-pruning.md)、[机器清单](validation/liquid_pruning_inventory.json)。

### 同步与溯源

- easy 1.7.0、medium 1.6.0；open 1.7.0 的数据和 manifest 完全不变。
- domain、rubric、benchmark_manifest 不变；package 保持未发布 2.3.0。
- 新增幂等 prune_liquid_cases.py，按记录哈希与固定 ID 筛选，保留原始源行，保护已有目标。
- hf_sync 同步数量／artifact 哈希，local_liquid_pruning 保存迁移前后哈希、删留记录、映射和脚本／清单哈希；原有 local 条目保持原样。
- 历史烹饪审计允许明确登记的液体删项；包括旧清单外的删除也要校验批准范围，不静默放过未登记缺失。
- 当前公开数量和液体分类入口已同步；新旧任务均分分母不同，需新推理集合和新输出目录。

### 验证结果

- 候选迁移检查通过；修改删项内容、部分删除、丢失保留代表均被拒绝。
- 296 条存活原始源行／字段／顺序不变，split 投影一致，全部目标记录保留；分类纠正涉及的两条任务保留。
- 78 项测试通过；296/296 参考计划合法、18/18 目标达成，11 个邻接控制、4 个处理省略控制、80/61 步处理／邻接重放通过。
- 基于迁移前源文件的当前目标审计通过；未登记删除反例被拒绝。液体当前 42 个唯一 ID、原指令和每类数量核对通过。
- doctor、发布源／包检查、sdist/wheel 构建和隔离安装检查通过；三个修订脚本复跑无数据变更。
- [迁移检查](validation/liquid_pruning_migration_checks.json)、[目标审计](validation/liquid_pruning_goal_checks.json)、[参考检查](validation/liquid_pruning_reference_checks.json)。未运行真实裁判或发布。

## 后续修复模板

复制以下模板到“后续修复模板”之前，并在修复索引中追加条目。编号依次递增；如后续修复更改了旧记录涉及的数据，应注明关联编号。

```markdown
## FIX-NNN：修复标题

- 日期：YYYY-MM-DD
- 状态：待修复 / 修复中 / 本地修复完成 / 已发布
- 范围：数据集、源索引、split 索引、稳定任务 ID（非任务问题填写模块）
- 关联记录：无 / FIX-NNN

### 问题与证据

记录指令、初始状态、原参考标注或实现行为，以及具体冲突。

### 修改内容

列出修改前后值；涉及参考目标和计划时，记录完整新目标和新计划。

### 同步与溯源

列出受影响文件、数据/协议版本、manifest 与哈希更新情况。
明确是本地修订还是上游同步，保留准确的来源信息。

### 验证结果

列出实际执行的命令或验证方法及结果。
分别记录动作有效性、目标达成、相关回归检查和未验证事项。
注明发布状态及是否需要重新评测。
```
