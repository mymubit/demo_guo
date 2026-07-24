# knowledge/ · 行业与工艺参考长文

> **注入策略（C5）**：默认 `knowledge_policy.mode: index`（文件名 + 首行）；`full` 须显式声明且带正数 `max_chars`；`off` 完全不灌。

## 用途

- **人读 / 作者侧**：题材基准、方法论、平台细则、S 级标准等。
- **模型侧**：优先靠 `foundation/rules/*.yaml` 的 `body` + 可选 `description`；长文只作索引指针（`source_ref`）。

## 硬约束

- **禁止无替代删除**行业基准（如 `market/industry-benchmarks.md`）及同类 SSOT 长文。
- 若内容迁入规则，须保留文件为指针或同步更新模块/SKILL 引用后再归档。
- `inject: doc` 文件默认不进 prompt（见 loader `_is_doc_only`）。
