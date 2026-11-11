# 备餐任务语义去重 — meal-pruning-v1

2026-11-11，按用户选择执行。保留其余 23 道备餐任务中的 7 道，删除 16 道 open 变体；另保留之前修好的 4 道处理任务。

**当前数据：339 道（easy 149 / medium 98 / open 92）。备餐候选 27→11；明确两人用餐候选 9→4。** open 版本 1.5.0→1.6.0，easy 1.6.0、medium 1.5.0 不变。

## 如何判断相似

23 道由 12 道晚餐、9 道早餐、2 道早午餐构成。其中 7 道明确两人用餐，是这 23 道的子集。主要重复是 prepare/host/make、cozy/comforting/elegant/hearty/full 等措辞变体。场景有多种布局，也有成对复用同一模板的记录。因此本次是按能力覆盖精简，并非声称所有任务完全等价。

保留普通供餐、餐食与氛围、两人晚餐、客人晚餐、未明确要求加热的两人早午餐、家庭早餐、餐后清理。已修的简单早餐、两人 hot 早餐、两人 warm 早午餐、烤箱复热返回全部保留，保证显式热处理和顺序约束仍有覆盖。

## 其余 23 道的完整原指令与处理

索引指去重前 355 条快照内从 0 开始的源位置；去重后定位以稳定 ID 为准。保留任务的所有字段、原始 JSONL 行与相对顺序不变。

| 去重前源索引 | 稳定 ID | 原指令 | 本次处理 |
| --- | --- | --- | --- |
| 238 | `7b007eb0-dfe0-4bcd-8697-8926d4572585` | Prepare a cozy dinner tonight | 删除相似变体 |
| 240 | `cb22d87c-0879-4709-9985-4f367772bf44` | Host an elegant dinner this evening | 删除相似变体 |
| 243 | `a55dd1af-59ee-4e0c-8139-208e2134ed49` | Plan and serve a complete evening meal | 保留：普通完整供餐 |
| 246 | `3cf1736a-3b96-4913-b9c5-df4688ee9053` | Prepare an elegant dinner and ambiance | 保留：餐食与氛围组合 |
| 249 | `5e8f884f-03be-4d9d-aa32-14003a8aaf52` | Prepare a comforting breakfast and serve it | 删除相似变体 |
| 254 | `590bda12-228f-4784-9caa-404aa7340332` | Prepare an inviting meal for family tonight. | 删除相似变体 |
| 255 | `861111df-3fbf-4569-9df9-2d3a9da81415` | Host an elegant evening meal | 删除相似变体 |
| 260 | `7853d8d5-fccc-42e1-8540-cfe67325b42d` | Prepare a complete breakfast for two. | 删除相似变体 |
| 261 | `f3ee3e87-d782-4870-8ed3-2bc92f344010` | Host a cozy dinner for two tonight. | 保留：明确两人晚餐 |
| 268 | `21d63cf0-3045-4d01-a88a-fe6f7d3e3499` | Prepare a cozy family dinner tonight | 删除相似变体 |
| 269 | `ff25ff1c-035a-474b-a42a-e16c6ea1965f` | Make tonight's dinner special for everyone | 删除相似变体 |
| 270 | `b2ac8958-c1dc-42d9-a41a-b6e0d8b8dd39` | Prepare a relaxed family breakfast | 删除相似变体 |
| 273 | `bc56e4a3-3772-456f-9ae6-8c3396f52880` | Prepare breakfast for two | 删除相似变体 |
| 279 | `f623e258-d97b-4a07-9121-0337a5fd3277` | Prepare a hearty breakfast for two guests | 删除相似变体 |
| 284 | `7bc96205-5b58-4310-b056-8768d2c9ca7a` | Host a cozy dinner for guests | 删除相似变体 |
| 292 | `e2d7a48c-0bc8-4a23-a932-83b4cbee492a` | Make breakfast for two and serve | 删除相似变体 |
| 300 | `43f14fb2-001a-495e-b9f6-ae11b67c964b` | Prepare an elaborate breakfast and serve it | 删除相似变体 |
| 301 | `dec162ab-e453-419f-971a-2e32987350f2` | Prepare an elegant dinner for guests | 保留：客人晚餐 |
| 303 | `0cf41a97-9f6a-4e13-8542-1def6889483d` | Host a cozy brunch for two. | 保留：未要求加热的两人早午餐 |
| 308 | `4a3dc074-3cd6-4241-a4a5-2c37f31c99a1` | Host a formal dinner and cleanup | 保留：举办用餐后清理的过程约束 |
| 327 | `2608e618-305d-46d2-b563-2ca9bc351c7b` | Prepare a full weekend brunch. | 删除相似变体 |
| 330 | `198fd035-6f65-4740-8b01-0643a215ccb4` | Prepare a full family breakfast service | 保留：未指定确切人数的家庭早餐 |
| 338 | `e8f12ff2-1929-497a-9d87-103ff77d2110` | Prepare a comforting weekend breakfast for two | 删除相似变体 |

## 其中 7 道两人用餐任务

| 去重前源索引 | 原指令 | 本次处理 |
| --- | --- | --- |
| 260 | Prepare a complete breakfast for two. | 删除 |
| 261 | Host a cozy dinner for two tonight. | 保留 |
| 273 | Prepare breakfast for two | 删除 |
| 279 | Prepare a hearty breakfast for two guests | 删除 |
| 292 | Make breakfast for two and serve | 删除 |
| 303 | Host a cozy brunch for two. | 保留 |
| 338 | Prepare a comforting weekend breakfast for two | 删除 |

其中 260、273、279、292、338 都是早餐／早午餐的措辞和人数变体。260 与保留的家庭早餐 330 使用完全相同 scene；303 与 338 只改了少量食物信息。261 的两人晚餐与 303 的两人早午餐保留；另保留已修的 293（warm brunch）和 319（hot breakfast）。删除早餐变体减少部分不同布局的覆盖，这是精简数量的有意取舍，不代表这些 scene 都相同。

## 场景复用的量化证据

完整节点按“类别、名称及全部属性”组成集合，关系边先用 normalize_links 规范化。下表为交集/并集（Jaccard）；没有忽略名称，也不是语义嵌入或模型生成的相似度。

| 去重前源索引对 | 完整节点重合率 | 关系边重合率 |
| --- | --- | --- |
| 240 / 246 | 98.5% | 98.3% |
| 249 / 292 | 98.4% | 98.2% |
| 255 / 301 | 98.1% | 97.9% |
| 260 / 330 | 100.0% | 100.0% |
| 261 / 319 | 97.7% | 98.7% |
| 273 / 327 | 98.9% | 98.8% |
| 303 / 338 | 99.3% | 99.2% |
| 238 / 293 | 98.2% | 98.0% |
| 260 / 319 | 3.3% | 2.0% |

260/319 同属两人早餐，但 scene 节点重合率很低，说明指令语义相似与场景重复必须分别判断。261/319 场景高度相似，但晚餐与明确 hot 早餐仍保留不同指令条件。

## 删除项的覆盖参照

以下映射用于说明精简后由哪些任务提供相近能力覆盖，不代表指令等价、目标可替换或完成条件相同。

| 删除 ID | 原指令 | 保留的覆盖参照 ID |
| --- | --- | --- |
| `7b007eb0-dfe0-4bcd-8697-8926d4572585` | Prepare a cozy dinner tonight | `a55dd1af-59ee-4e0c-8139-208e2134ed49` |
| `cb22d87c-0879-4709-9985-4f367772bf44` | Host an elegant dinner this evening | `3cf1736a-3b96-4913-b9c5-df4688ee9053` |
| `5e8f884f-03be-4d9d-aa32-14003a8aaf52` | Prepare a comforting breakfast and serve it | `4bddb476-f1ae-44e1-9558-add1571dd936` |
| `590bda12-228f-4784-9caa-404aa7340332` | Prepare an inviting meal for family tonight. | `198fd035-6f65-4740-8b01-0643a215ccb4` |
| `861111df-3fbf-4569-9df9-2d3a9da81415` | Host an elegant evening meal | `dec162ab-e453-419f-971a-2e32987350f2` |
| `7853d8d5-fccc-42e1-8540-cfe67325b42d` | Prepare a complete breakfast for two. | `198fd035-6f65-4740-8b01-0643a215ccb4` |
| `21d63cf0-3045-4d01-a88a-fe6f7d3e3499` | Prepare a cozy family dinner tonight | `198fd035-6f65-4740-8b01-0643a215ccb4` |
| `ff25ff1c-035a-474b-a42a-e16c6ea1965f` | Make tonight's dinner special for everyone | `3cf1736a-3b96-4913-b9c5-df4688ee9053` |
| `b2ac8958-c1dc-42d9-a41a-b6e0d8b8dd39` | Prepare a relaxed family breakfast | `198fd035-6f65-4740-8b01-0643a215ccb4` |
| `bc56e4a3-3772-456f-9ae6-8c3396f52880` | Prepare breakfast for two | `4bddb476-f1ae-44e1-9558-add1571dd936` |
| `f623e258-d97b-4a07-9121-0337a5fd3277` | Prepare a hearty breakfast for two guests | `4bddb476-f1ae-44e1-9558-add1571dd936` |
| `7bc96205-5b58-4310-b056-8768d2c9ca7a` | Host a cozy dinner for guests | `dec162ab-e453-419f-971a-2e32987350f2` |
| `e2d7a48c-0bc8-4a23-a932-83b4cbee492a` | Make breakfast for two and serve | `4bddb476-f1ae-44e1-9558-add1571dd936` |
| `43f14fb2-001a-495e-b9f6-ae11b67c964b` | Prepare an elaborate breakfast and serve it | `4bddb476-f1ae-44e1-9558-add1571dd936` |
| `2608e618-305d-46d2-b563-2ca9bc351c7b` | Prepare a full weekend brunch. | `0cf41a97-9f6a-4e13-8542-1def6889483d` |
| `e8f12ff2-1929-497a-9d87-103ff77d2110` | Prepare a comforting weekend breakfast for two | `0cf41a97-9f6a-4e13-8542-1def6889483d` |

## 验证、溯源与剩余问题

- `scripts/prune_meal_cases.py` 使用明确 ID 清单，拒绝候选记录被修改、只删一部分及保留代表缺失的输入。重复运行报告 0 条待删除。
- 所有存活 JSONL 行及顺序不变；easy/medium 数据和 manifest、domain、rubric 不变。open split、manifest、hf_sync 数量和哈希同步。
- 原备餐审查清单保留历史证据。当前审计只排除已批准删除的 16 个 ID，不允许静默忽略其他丢失任务；11 道备餐候选中仍有历史确认 2 道、待完整认证 9 道（7 个代表加刚补份量的 2 道）。
- 保留不表示原参考计划已完成用餐指令。7 个代表的食物、份量、供餐及过程证据仍需逐题完善；本次不修改 scene、plan、goal 或评价提示词。
- 当前 339 条参考计划全部合法，18 组已标注目标可达；74 项测试通过。11 个邻接控制、4 个处理省略控制及 80/61 步处理／邻接重放通过。
- doctor、发布检查、sdist/wheel 构建和隔离安装检查通过。未运行真实裁判或对外发布。
- 任务数改变，旧 348/355 题成绩不直接与 339 题成绩比较；使用新推理集合和新评测输出目录。

机器证据：[批准清单及相似度](validation/meal_pruning_inventory.json)、[迁移检查](validation/meal_pruning_migration_checks.json)、[当前目标审计](validation/meal_pruning_goal_checks.json)、[全量参考检查](validation/meal_pruning_reference_checks.json)。`hf_sync.json.local_meal_pruning` 保存删留 ID、原指令、候选记录哈希、迁移前后源哈希和脚本／清单哈希；更早的修订记录保持原样。
