# AHAT Benchmark 修复记录

本文件持续记录 ahat-benchmark 的数据、参考标注及评测实现修复。每次修复追加一条记录，包含问题证据、具体修改、验证结果和受影响文件；尚未完成的检查应明确标为“未验证”。

## 记录约定

- 任务以稳定的 `id` 为主键，同时记录数据集和从 **0 开始**的索引。JSONL 行号从 1 开始，等于源索引加 1；不同 split 的索引不一定等于源索引。
- `benchmarks/ahat_eval_set.jsonl` 中的 `plan` 是参考计划；可选的 `reference_goal` 是 PDDL 谓词字符串列表，列表内目标必须同时成立。正谓词 `(is_clean sink_6)` 表示该水槽的 `is_clean` 为 `true`。
- 运行时 `cases.json` 仅保留 `id`、`instruction`、`scene_graph` 和可选的 `domain_id`。修复场景时同步对应 split；参考计划和参考目标保留在 JSONL 中。
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
| FIX-015 | 2026-11-11 | 液体种类、内容加热、倒出传递和制作缺少状态；全局 domain 不隔离 | 32 道迁移、2 道器具参考修复、7 道隔离；任务级 domain 与裁判路由 | 本地实现及离线验证通过，289 道正式任务 |
| FIX-016 | 2026-11-11 | 家具／设备移动保留旧机器人位置；相邻和容器摆放绕过单物体容量 | 两个 domain 的 5 个共享动作；任务数据不变 | 91 项测试通过，289 条参考末态不变 |
| FIX-017 | 2026-11-12 | 多物交付回放丢失、照明类型／状态混用、咖啡机放置、非法名称、机器人房间边与缓存计划错配 | 235 条记录、两个 domain 照明动作、scene 回放、裁判和缓存 | 102 项测试，289 条参考合法，3,997 步回放一致；防环暂缓 |
| FIX-018 | 2026-11-12 | 水瓶任务重复，液体 fill_from_faucet 允许闭瓶注水 | 四留二、补开瓶前置条件及两条参考计划；289→287 | 104 项测试，287 条参考合法，18 个既有目标可达 |
| FIX-019 | 2026-11-12 | 柜内胶囊盒先于柜门打开 | 一道 medium 任务改用胶囊原料，参考 24→22 步 | 单任务目标及液体回归通过 |
| FIX-020 | 2026-11-12 | 人物位置边未生成 person_at | 61 道场景初态／末态、共享位置转换及 D2 摘要；数据和 domain 不变 | 108 项测试，287 条参考合法，18 个既有目标可达 |
| FIX-021 | 2026-11-12 | 普通 domain 允许非容器装水等宽松液体操作 | 删除五个普通动作，液体生成器独立定义；287 条任务数据不变 | 287 条参考与 18 个目标通过，液体 domain 字节不变 |
| FIX-022 | 2026-11-12 | PDDL 内置 object 被重定义，item 自继承 | 两个 domain、scene 类型映射及共享类型判断；任务数据不变 | 113 项测试、287 条参考及独立 problem 解析、3,985 步回放通过 |
| FIX-023 | 2026-11-12 | 三道晚餐场景可用食物不足或只有包装 | 三道 open scene 新增 8 个实际食物及位置边；计划和 domain 不变 | 三条食物使用见证及原参考通过，177 步回放一致 |
| FIX-024 | 2026-11-12 | 三道晚餐参考未使用新增食物或缺少供餐／撤餐 | 采纳三组已确认的成功方案；仅替换正式 plan | 三组末态目标、先供餐后撤餐及省略动作对照通过 |
| FIX-028 | 2026-11-13 | easy 同类语义任务过多 | 按批准清单归档 13 题，287→274（117/65/92） | 参考计划、目标、回放及数据一致性检查通过 |

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

## FIX-015：液体专用 domain、任务分流与内容状态

日期：2026-11-11。前序工作已提交 `c14898f`；本修订随后实施。

问题：普通 domain 只记录 is_filled，不能证明内容种类、加热完成或倒水后的属性，
旧参考中存在漏装料、错误水源、空杯交付及把房间当浇水目标等问题。全部任务共享
全局 domain，直接修改会扩大影响；历史 42 道分类也未覆盖全部相关任务。

处理：

1. 保留普通 domain 和四份普通裁判提示词的字节，生成独立 ahat-liquid-v1。
   在容器上声明内容种类和 contents_heated，补齐加热、原料装载、制作、传递、
   浇水及检查水壶动作。条件效果读取执行前状态并同时应用，scene/PDDL 共用实现。
2. 审查 46 道：原分类 42 道、计划包含液体动作的额外 3 道，以及全量指令扫描
   发现的“检查一壶水”任务。32 道迁移，2 道器具准备参考修复，5 道保留原记录，
   7 道隔离；289 道正式任务为 130/67/92，domain 分布为普通 257／液体 32。
3. 数据加载、VAL、回放、裁判、缓存和汇总按固定任务 domain 路由。液体推理结果
   必须包含匹配 ID/hash；export-inputs 导出正确 domain 与初态，不包含参考答案。
4. 补充 scene、参考计划和离线 liquid_reference 见证。见证结合过程与结果，
   不把局部末态宣称为完整充分目标。保留全部 18 个既有 reference_goal。
5. 归档全部 41 道受影响原记录；7 道隔离项包含原因，不计入正式分母。
   所有存活指令、ID、split 不变，255 道记录行及参考末态不变。

验证：87 项单元／集成测试通过；289/289 参考计划合法，18/18 原目标可达，
11 个邻接反例、4 个固体处理省略反例通过。液体／器具参考 34 组结果达成，
495 步 scene/PDDL 回放一致，76 个关键动作省略反例可由非法动作、结果缺失或
明确要求的阶段遗漏识别。混合 domain 的验证、裁判输入、缓存恢复和错配拒绝通过。
离线示例使用真实 VAL 和模拟裁判；未运行真实 LLM 裁判或重新测量算法分数。

当前语义、完整映射和限制见 [液体修订](liquid-domain.md)。机器证据见
[清单](validation/liquid_v1_inventory.json)、[液体检查](validation/liquid_v1_checks.json)、
[全量参考检查](validation/liquid_v1_reference_checks.json)、
[既有烹饪审计](validation/liquid_v1_cooking_checks.json)。

FIX-015 安装复核：sdist/wheel 检查通过；独立安装后 289 条参考计划、52 组结果断言、
483 步液体回放及混合 domain 模拟裁判流程通过。见
[完成审计](validation/liquid_v1_completion_checks.json)。

## FIX-016：移动位置唯一与摆放容量一致

日期：2026-11-11；修订 location-capacity-v1。两种移动动作删除旧 agent_at；
表面相邻、容器相邻和普通容器放置补充与对应普通表面规则一致的容量前置条件。
液体 domain 从修复后的普通 domain 重新生成，协议 revision 和哈希同步。

当前没有参考计划调用两个移动动作，没有场景启用单物体容量标记，因此不改任务数据。
91 项测试通过；12 组原生 VAL 漏洞对照通过；289 条参考计划合法且末态不变，
18 个既有目标可达，11 个邻接及 4 个固体处理反例通过。
详细语义、影响范围及证据见 [动作不变量修复](action-invariants.md)。

## FIX-017：多物持有、照明、场景位置与缓存一致性

日期：2026-11-12；修订 scene-lighting-v1。已按确认方案执行，PDDL 防环仅记录、暂缓。

人的持有列表保留所有交付物，修复 14 条参考计划回放时丢失的 22 条事实。
两台咖啡机从厨岛内改放台面，五道场景同步修正非法名称和引用。
61 条反向 on-agent 边删除（含此前发现的 59 条及新增两条 room-on-agent），
58 个冲突房间边按精确 location 校正，并在后续回放中同步推导。
light_on / is_light_on 参数扩展为 physobj，新增 light_off；184 道场景的
1,629 个照明节点移除冗余通电字段，11 条参考计划改用 light_on。
VAL 缓存核对规范化 inference 计划与当前初态，阶段内容 hash 参与上游结果绑定。

修改合计 235 条记录，保留 54 条源数据行原字节；289 个 ID、指令、难度和
18 组既有目标不变。源及 split 的零基索引、具体修改见
[修改清单](validation/scene_lighting_v1_inventory.json)。

102 项测试通过；289 条参考合法，18 组目标可达，11 个邻接和 4 个热处理对照通过；
液体／器具 34 组结果及 76 个省略对照通过；全量 3,997 步 scene/PDDL 回放一致。
基线末态变化严格限于批准的照明、名称恢复及咖啡机位置；所有非照明动作定义不变。
未运行真实 LLM 裁判。完整说明及验证文件见 [修复文档](scene-lighting.md)。

## FIX-018：水瓶任务去重与液体开瓶注水约束

日期：2026-11-12；修订 bottle-refill-v1。保留交付给人、指定水源后归位两个代表，
完整归档两个重复 medium 任务。保留任务原本已绑定 ahat-liquid-v1，继续使用该 domain。
只在液体 fill_from_faucet 加入 `(imply (can_be_opened ?c) (is_open ?c))`；
两条参考计划在 pickup 前加入 open，原指令、scene 和结果断言不变。
不新增最终盖好瓶子的条件，普通 domain 原字节及其他动作不变。

正式任务 289→287（130/65/92），液体 32→30；其余 285 条记录和源行原字节保持不变。
104 项测试通过，287 条参考合法，18 组既有目标可达；32 组液体／器具结果断言、
485 步液体回放及 74 个遗漏步骤对照通过。两道参考省略 open 后均被新 domain 拒绝，
而旧 domain 接受；无盖杯子仍可直接注水。迁移幂等。
任务 ID、修复前源／split 索引、归档及完整证据见 [水瓶修复](bottle-refill.md)。

## FIX-019：咖啡胶囊原料与参考计划简化

日期：2026-11-12；修订 coffee-pod-v1。任务
`05f9fb16-de68-4fb8-8cc7-4ad1714f7f72` 的原指令为
“Prepare a hot cup of coffee in the kitchen and deliver it to the bedroom nightstand.”
原参考先打开关闭柜子内的胶囊盒，再打开柜门。按用户选择，将
`coffee_pod_box_44` 改为 `coffee_pod_44`，类型改为 `coffee_pod`，
删除 can_dispense、can_be_opened，保留 coffee_supply、ingredient_available。
原料仍在 kitchen_cabinet_84 内，必须先开柜再取出，装料后原料可用状态被消耗。
实体节点作为已用原料载体保留，沿用现有液体模型。

同步源 scene、split scene、边引用、参考计划及 liquid_reference.required_actions。
删除开盒和多余导航，参考 24→22 步；保留开柜、取料、装料、制作和送达。
原指令、ID、难度、domain 绑定与四个结果断言不变：杯子在床头柜、非空、
含咖啡、内容已加热。其余 286 条源记录原字节不变，正式任务数仍为 287。
medium 版本 1.9.0→1.9.1；两个 domain 原字节不变。

原生 VAL 验证计划合法及四个结果断言达成；22 步 scene/PDDL 回放一致。
省略开柜、装料均判 invalid。液体／器具回归的 32 组结果断言、483 步回放、
74 个遗漏动作对照全部通过。完整前后节点、计划、数据哈希和单任务证据见
[单任务验证](validation/coffee_pod_v1_checks.json)，回归见
[液体验证](validation/coffee_pod_v1_liquid_checks.json)。

本修复解决该参考实例，不代表已实现通用外层容器可访问性限制；PDDL 防环仍暂缓。
未发布，未重新测量算法分数；此任务需使用新 scene 重新推理并使用新评测输出。

## FIX-020：人物位置从 scene 到 PDDL 的转换

日期：2026-11-12；修订 person-location-v1。当前 277 个带人物的场景中，
216 个有与位置边一致的 person.location，61 个只有人物 in-room 边。
旧提取器跳过人物位置边，仅从 location 字段生成 person_at，导致后者位置丢失。
这 61 条参考均无交付动作，不能将信息丢失等同于 61 条交付失败。

在共享 scene 转换层补充人物位置规范化，SceneGraphManager 与 D2 场景摘要
使用同一逻辑；在私有副本上处理，不修改调用者输入或正式任务数据。
location 缺失／null 时，从规范化 on/in 边选择唯一物理位置，兼容旧数组边与字典边。
存在精确位置时保留精确位置，房间边只用于核对其沿 on/in 路径推导的房间，
不生成第二条 person_at。多个精确位置、多个房间、显式位置与边冲突，
或位置指向未知／非物理对象时明确拒绝；完全没有位置证据时保持未指定。

287 条任务源数据、split、参考计划、目标及两个 domain 原字节保持不变。
D1 获得恢复的人物末态位置，D2 新增规范化 person_locations；裁判提示词未改。
现有代码指纹与初态一致性校验会阻止复用旧评测缓存，需要重新运行 VAL／judge。
对于直接使用导出 PDDL 初态的算法，需要重新导出并使用新版输入。

验证：108 项单元／集成测试通过，包括两种 domain 的位置边转换、真实 VAL 交付、
逐步回放、精确位置与房间归属、冲突拒绝及输入不被修改；287 条参考合法、
18 组既有目标可达，11 个邻接及 4 个热处理对照通过。
液体／器具 32 组结果、483 步回放及 74 个遗漏动作对照通过。
全量前后初态／末态差异和逐步回放证据见
[位置转换验证](validation/person_location_v1_checks.json)，其他证据见
[参考检查](validation/person_location_v1_reference_checks.json)及
[液体检查](validation/person_location_v1_liquid_checks.json)。
全量 3,985 步 scene/PDDL 回放一致；前后状态只新增预期的 61 条 person_at，
其余初态／末态事实完全不变，277 个场景的人物位置均完整保留。
未运行真实 LLM 裁判，未重新测量算法分数，未发布。通用容器访问和 PDDL 防环不在本次范围内。

## FIX-021：普通 domain 移除液体制作与转移动作

日期：2026-11-12；普通 domain 修订 ordinary-core-v1，逻辑 ID 仍为
ahat-v8-group-portions，通过新 revision／SHA-256 区分。257 条普通参考均未调用
fill_from_faucet、fill_device_with_water、dispense_from_device、pour_into、pour，
但旧 domain 的这些动作允许给非容器装水等不合理操作。

从普通 domain 删除这五个动作，动作数 30→25。其他动作、谓词、类型和 requirements
的解析结构完全不变；保留 has_faucet、is_filled 等初态属性及清洗／浸泡动作，
它们仍供清洗前置条件、现成饮品搬运等用途使用。类型规范化仅给出方案，本次未实施。

液体生成器改为独立加入这五个完整液体动作，不再以普通 domain 中同名动作作为替换入口。
保留原生成顺序，生成器 --check 通过，液体 domain 字节与 bottle-refill-v1 完全相同。
普通 domain 指纹、全局及 split manifest 同步，split 版本均为 1.9.2；
287 条源记录、三个 cases.json、指令、scene、计划和目标不变。
benchmarks/hf_sync.json 的 local_ordinary_core 保存前后 domain 和未变数据哈希。

验证：109 项单元／集成测试通过，287 条参考合法，18 组目标可达，11 个邻接和 4 个热处理对照通过。
液体／器具 32 组结果、483 步回放及 74 个遗漏动作对照通过。
全量 287 条参考的初态／末态与修改前完全一致；五个旧动作反例在旧 domain 中合法，
新普通 domain 均以 Unknown domain action 判 invalid；原生 VAL 用于旧反例及参考验证。
旧加热生产者反例测试改为在 open 上注入额外 heated 效果，继续验证同一审计约束。
证据见 [动作与状态差异](validation/ordinary_core_v1_checks.json)、
[参考验证](validation/ordinary_core_v1_reference_checks.json)、
[液体回归](validation/ordinary_core_v1_liquid_checks.json)。

自定义任务如需装液、倒液、制作饮品，应使用液体 domain 并补齐对应容器／内容状态，
不能继续提交旧普通动作。使用新版普通 domain 重新推理并使用新的评测输出；
含旧 domain hash 的推理／缓存会被拒绝。未运行真实 LLM 裁判、未测量算法排名、未发布。
doctor、发布源文件检查和 git diff --check 均通过。

## FIX-022：PDDL 根类型与小物品类型分离

日期：2026-11-12；两个 domain 修订 type-hierarchy-v1。普通 domain 保持 FIX-021
已删除五个液体动作后的 25 动作边界；液体 domain 保持 38 个动作。
将 item 显式声明为内置 object 的子类，原小物品 object 改为 small_object，
container 父类型与 clean_item 目标签名同步修改。根类型不再重定义，类型树无环。

SceneGraphManager 将 objects 分类转换为 small_object，所有 problem 导出共享该映射；
初态类型过滤复用与 VAL 参数检查、效果回放相同的类型祖先判断。
无类型标注时的默认 object 仍指内置根类型。保留任务 JSON 分类、业务 type、
对象名、指令、参考计划和目标；287 条源记录及三个 cases.json 原字节不变。
重新生成液体 domain 并同步两个 domain 的哈希；三个 split manifest 均为 1.10.0。

全量验证：113 项测试；287 条参考经原生 VAL 判合法；18 组既有目标、11 个邻接
和 4 个热处理对照通过；液体／器具 32 组结果、483 步回放及 74 个遗漏动作对照通过。
独立 pddl 0.4.6 接受两个 domain 和全部 287 个 problem；初态无被过滤事实。
287 道初态／参考末态与修改前完全一致，3,985 步 scene/PDDL 回放一致。
语法树对照确认两个 domain 仅有预期类型修改，动作前置条件与效果未改写。

新增 scripts/check_domain_types.py 并加入 CI；开发依赖增加 pddl 0.4.6，运行依赖不变。
类型与非法参数回归覆盖小物品／容器继承、家具误用拒绝，以及显式根类型量化的
原生 VAL、Python 和 scene 一致性。详见 [类型修复说明](domain-types.md)和其中的四份全量证据。
缓存与推理结果需绑定新 domain 哈希，应重新导出、推理和评测；未运行真实 LLM 裁判，
未测量算法排名，未发布。通用关闭容器访问、液体不变量与空间防环不在本次修复范围内。

FIX-022 安装复核：sdist/wheel 构建、发布源及分发包检查、doctor 和 git diff --check
通过。独立安装 wheel 后的 287 条参考、50 组目标及混合 domain 模拟裁判检查通过，
证据见 [安装包验证](validation/type_hierarchy_v1_package_checks.json)。

## 决策记录：三项模型问题暂缓处理

2026-11-12。用户确认当前任务不需要解决以下三项模型问题，要求记录、暂不实施：
外层关闭容器访问约束不完整、液体动作与 scene 不变量不完全一致、空间关系可能形成环。
当前正式参考验证未发现触发，保留已有构造反例及解决思路，不将暂缓标为已修复。
新增相关任务或实际发现触发时再复查；此轮仅更新文档，不修改 domain、实现或任务数据。
具体问题、当前任务依据及状态见 [暂缓清单](post-scene-lighting-audit.md#当前决定三项模型问题暂缓)。

## FIX-023：为三个晚餐场景补充实际食物

2026-11-12；修订 dinner-food-v1。第一道完整晚餐新增鸡肉、土豆、西兰花，
第二道优雅晚餐新增鱼肉、土豆并保留原有蔬菜，第三道正式晚餐新增牛排、土豆、四季豆。
共 8 个食物节点及 8 条指向现有冰箱的 in 边，明确 is_food、can_be_heated、
heated=false、is_clean 和 can_be_moved；不增加初始生熟分类或未指定的人数。

先验证候选后写入。三条独立见证通过真实 VAL 和加热、装盘、上桌结果检查；
原参考仍合法，既有对象的初态／末态事实不变，新增食物在原参考中保持存放状态。
见证与原参考共 177 步 scene/PDDL 回放一致。见证不写入正式 plan／goal，
不将补充食物视为已经完成原参考的供餐、氛围或清理修复。

仅三条 scene 与 open 副本变更；284 条其他源行原字节不变，两个 domain 不变。
open 版本 1.10.1，任务数仍为 287。脚本复跑报告 0 条待修改。
节点、位置、任务 ID、版本及验证见 [晚餐食物补充](dinner-food.md)。
全量 287 条参考合法、18 组既有目标可达，287 个 problem 独立解析通过、无初态事实丢失，
3,985 步回放一致；doctor、发布源检查和 git diff --check 通过。

## FIX-024：采纳三组晚餐成功参考方案

2026-11-12；修订 dinner-reference-v1。用户接受候选 plan 作为当前模型下的一种
成功情况，要求替换旧参考。三道任务分别为：完整晚餐 19→44 步，优雅晚餐与氛围
18→62 步，正式晚餐与清理 22→76 步。菜单、装盘、氛围和撤餐采用此前验证过的方案。

仅替换三条源记录的 plan，284 条其他源行原字节不变；三个 cases.json、场景、
指令、reference_goal、domain 绑定和两个 domain 文件均不变。open manifest 更新
为 1.10.2，记录参考修订；运行时输入和评分口径不变。

三条 plan 的最终结果目标均经真实 VAL 验证。第三道在第 50 步达到完整供餐阶段，
随后收纳食物、撤餐具到水槽、餐巾归位、熄灯和关闭柜门；不添加进食、等待或变脏动作。
此处 cleanup 的具体实现为撤餐收纳，不宣称模拟了洗盘。最终目标不能独立证明曾供餐，
因此保留阶段目标和反例，未将末态列表写为完整任务的 reference_goal。

新增 scripts/check_dinner_references.py 并加入 CI：核对正式计划、三组末态目标、
一组先供餐后撤餐阶段、四个省略加热／点灯对照及一个跳过供餐却满足末态的反例。
这些离线检查不要求其他正确方案复制参考菜单、餐桌或动作序列，也不新增评分门槛。
此前历史备餐清单中这三道的 deferred 原因不再代表当前参考状态；本次采纳成功实例
与为所有解认证完整充分 goal 是不同范围。

完整计划、目标和说明见 [已采纳参考](dinner-reference-candidates.md)，原计划与哈希见
[采纳记录](validation/dinner_reference_v1_adoption.json)，后续验证见
[参考检查](validation/dinner_reference_v1_reference_checks.json)、
[阶段与结果检查](validation/dinner_reference_v1_goal_checks.json)、
[全量回放](validation/dinner_reference_v1_scene_checks.json)。
全量验证：287 条参考合法、18 组既有目标可达，287 个 problem 独立解析通过，
初态无事实丢失，4,108 步 scene/PDDL 回放一致；doctor、发布源检查和 git diff --check 通过。

## FIX-025：修复三道两人／家庭备餐参考

2026-11-12；修订 group-meal-reference-v1。按用户“用刚才的方式先完成前三道”的
授权，采纳三种具体成功方案：两人温馨晚餐 28→42 步、两人温馨早午餐 19→34 步、
完整家庭早餐 33→36 步。均实际加热鸡蛋、装盘上桌，前两道点亮已有餐桌蜡烛。
晚餐另加热土豆与蔬菜，早午餐供应已有苹果，家庭早餐供应面包、黄油并摆放餐巾。

为使菜单完整，晚餐新增 potatoes_122、vegetables_123，明确 serves_two；家庭早餐
新增 bread_115，明确 serves_group。三个新食物初始 heated=false，存于现有冰箱。
原鸡蛋份量不变，面包不要求加热，容器／包装不代替食物。共享碗盘仅作为盛菜器皿；
家庭人数保持原指令的不定人数模型，不声称模拟营养、精确份数或主观舒适度。

写入前验证三条候选的真实 VAL、目标和逐步回放。三组结果目标、五个省略加热／点灯
对照、三个装盘前停止对照、六个分别删除份量事实的对照均通过。目标作为离线见证，
没有新增运行时 reference_goal 或评分门槛，也不将具体菜单作为其他成功方案的必要条件。
复用并扩展 check_dinner_references.py 的采纳记录参数，CI 覆盖本批和此前晚餐参考。
份量测试改为逐食物核对，允许同一场景存在多个明确两人／家庭份食物；同时继续检查
初始份量不会产生 heated，去掉加热动作后份量保留但 heated 不出现。

仅三个源记录的 scene_graph／plan 变更，其余 284 行原字节不变；同步 open 场景副本、
manifest 1.10.3 与 hf_sync 指纹。指令、两个 domain、评分实现不变。第四道客人晚餐及
已决定暂缓的三项模型问题不在本次范围。新增食物场景应重新导出输入并运行评测。

全量 287 条参考合法，18 组既有目标、11 个邻接与 4 个热处理对照通过；两个 domain
和 287 个 problem 独立解析通过，初态无事实丢失，4,140 步 scene/PDDL 回放一致。
完整 plan、goal、原计划和验证证据见 [三道备餐参考](group-meal-references.md)。
113 项测试、doctor、发布源检查和 git diff --check 通过；迁移复跑为 0 条变更。

## FIX-026：完善客人晚餐场景、参考 plan 与 goal

2026-11-12；修订 guest-dinner-v1。任务 dec162ab-e453-419f-971a-2e32987350f2
（Prepare an elegant dinner for guests）新增三文鱼、土豆、蔬菜三个真实食物节点，
各自显式 serves_group=true、heated=false，存入已有 refrigerator_33。原苹果、
奶酪和奶酪份量保留，已有场景状态不改写。三个新节点与三条位置边外无场景变更。

参考 plan 从 21 步变为 49 步：先取干净餐盘上桌，将三种食物放入已有烤箱，关门通电、
逐份 heat_with_oven、断电后开门取出装盘，关闭炉门／冰箱／柜门，点亮已有餐桌蜡烛。
干净桌布、花瓶、餐巾沿用初态布置。直接 in 烤箱加热沿用已有动作模型，无 domain 修改。

依用户要求将 33 个结果条件写入源任务 reference_goal，表示这一完整的具体成功方案，
包括实际食物、客人份量、加热、装盘上桌、干净餐具桌面、布置点灯及安全收尾。
不把所选菜单、加热方法或布置作为其他成功解的必要条件，不宣称符号谓词量化主观审美。
推理导出不含参考 plan／goal，运行时评分口径不变；目标只作为参考与离线验证数据。

写入前通过真实 VAL、目标可达和每步回放；省略加热、点灯、装盘前停止、分别删除三个
份量事实的六个对照均合法但不满足目标。CI 增加本任务采纳记录／正式 goal 一致性检查。
共有份量测试覆盖新增食物在实际 D1 请求中的可见性；热处理测试的显式目标清单纳入
新任务，并继续检验去掉热处理后无法满足 goal，保留全部逐步回放要求。

只有一条源任务的 scene_graph／plan／reference_goal 变化，其余 286 条源行原字节不变；
同步 open 场景、manifest 1.10.4 与 hf_sync。easy/medium 场景和两个 domain 不变。
应为该任务重新导出场景输入并推理评测；此前暂缓的三项模型问题仍不在范围。
全量 287 条参考合法、19 组既有及新增目标通过，287 个 problem 独立解析通过，
初态无事实丢失，4,168 步 scene/PDDL 回放一致。详见 [客人晚餐](guest-dinner.md)。
113 项测试、doctor、发布源检查和 git diff --check 通过，迁移复跑为 0 条变更。

## FIX-027：重测入口的任务 domain 绑定与审查状态更新

2026-11-12。全量复核发现 generate_inference.py 仍只发送全局普通 domain，
且输出缺少 domain_id/domain_sha256；30 道液体任务的输入定义及评测绑定因此不正确。
改为逐任务 resolve_domain/domain_binding，保留旧自定义数据的默认 domain 回退。
新增模拟 API 的普通／液体混合请求与结果真实 VAL 检查；不调用真实服务。

audit_cooking_goals.py 将历史 deferred 9 条与当前修复状态分开：逐条核对采纳 plan、
goal 与阶段结果，结合两道已修复份量的早餐，得到当前已修复 9、待修复参考 0。
历史两道严格语义审查 confirmed_count=2 保留；不将历史计数误报成当前问题数，
也不把实例可达性等同于所有自然语言任务充分必要条件。回归确认被更改的采纳计划
不能继续报告已修复。旧库存文件与历史证据不修改。

任务/source、两个 domain、评分规则均不变。115 项测试通过，重新导出并检查全部
287 条无参考答案的推理输入。液体专项 32 组结果、483 步回放、74 个遗漏动作对照通过。
全量 287 条参考、19 组目标及 4,168 步回放证据与当前数据/domain 指纹一致，可复用。
发现外部历史 Direct 启动器固定 348 题和单 domain，不能原样用于当前集合；该历史
文件未修改，实际重测须适配入口并另建新结果记录。本轮没有真实模型调用。
详见 [全量状态与重测准备](benchmark-recap-20261112.md)。


## FIX-028：执行 easy 的 13 题精简方案

日期：2026-11-13。采用已审阅并获确认的 13 题方案，不采用扩展方案的额外七题。
八组删留理由和全部稳定 ID 见 [easy 精简说明](easy-pruning.md)及
[批准清单](validation/easy_pruning_v1_inventory.json)。13 条完整原记录归档至
`benchmarks/easy-pruning-v1/removed.jsonl`，正式集合变为 117/65/92，共 274 题；
普通 domain 244 题、液体 domain 30 题。easy 版本 1.11.0；medium/open 数据和
manifest 原字节不变。保留记录的源行原字节和顺序、两个 domain、评分规则均不变。

更新源文件、easy 投影、manifest、hf_sync 指纹及当前说明。历史本地新增十题中两题
进入归档，生成器仍复现十题，测试覆盖八题活动、两题归档。备餐审计补入本次批准
删除的胡椒磨任务；历史人工审阅清单保留原内容。迁移脚本默认预览，校验审阅基线、
代表任务和归档冲突，拒绝部分删除；再次执行报告零条待移出。

验证：117 项回归测试通过；274 条原生 VAL 参考合法，17 组目标、九个邻接和四个热处理对照通过。
两个 domain、274 个 problem 独立解析及 4,107 步回放通过；保留与归档源行可重建
原始 SHA-256，medium/open 指纹不变。检查证据见 `docs/validation/easy_pruning_v1_*`。
未调用模型；旧 287 题 GPT/DS 结果保持历史口径。
