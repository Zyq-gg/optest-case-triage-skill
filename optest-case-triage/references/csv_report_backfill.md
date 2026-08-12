# CSV 报告回填

本文只用于独立文档处理：把已经完成的 Markdown 分析结论写入用户提供的 CSV。不要把它混入 case 复现、根因诊断、源码修改或 pytest 验证。

## 目录

- [目标与证据权威性](#目标与证据权威性)
- [检查输入](#检查输入)
- [建立-case-证据台账](#建立-case-证据台账)
- [填写四个字段](#填写四个字段)
- [创建并应用-update-plan](#创建并应用-update-plan)
- [验证结果](#验证结果)

## 目标与证据权威性

用户已有 Markdown 分析报告并要求填写以下 CSV 列时使用本流程：

- `测试目的`
- `解决方案`
- `最终状态`
- `遗留原因`

证据优先级：

1. Markdown 中当前、精确 case 的验证记录；
2. Markdown 中当前根因、修复、环境约束和残余风险；
3. 按表头和内容选出的相关 CSV 辅助列；
4. CSV 中较旧的错误、结论或历史备注。

来源冲突时，以 Markdown 为准。旧 `问题结论` 等辅助字段只提供背景，不是证明。其位置不稳定，可能在某个文件的 L 列，也可能改名或移到其他位置；绝不能写死列字母。

本流程只汇总已经完成的分析，不会静默开始新一轮单 case 分析。Markdown 对某行证据不足时，应报告缺口。用户要求每行都填时，只能配合具体遗留原因使用 `无法验证`，例如 `Markdown 无该精确 case 的当前验证记录`；不能把旧辅助结论升级成当前测试结果。

## 检查输入

用 Python `csv` 模块解析 CSV，不能使用逐行 shell 工具；带引号字段可能包含逗号和换行。

编辑前记录：

- encoding，以及是否有 UTF-8 BOM；
- delimiter、line ending、表头顺序、列数和逻辑行数；
- case 身份列，优先选择文件、class、case/test 名；
- 按名称定位的四个目标表头；
- 根据表头和抽样值发现的全部潜在辅助列。

前三列通常是 `test_file`、`class_name`、`case_name`，但实际名称可能不同。必须结合表头和内容确认含义；前三列不是身份字段时不能盲用。

完整读取足以覆盖所有目标行的 Markdown。写 CSV 前合并重复或历史小节：最新的精确 case 结果优先，旧尝试只作为背景证据。

## 建立 case 证据台账

每个逻辑 CSV 行建立一条内部记录：

```text
CSV 行号和精确身份
Markdown 小节及记录的 XLSX 行/nodeid
当前复现结果
根因或能力限制
已验证源码修复或环境配置
剩余 blocker 或风险
参考过的辅助列
```

按最强可用组合匹配：

1. 已记录的工作簿行号加精确 case 身份；
2. 精确 pytest nodeid；
3. 文件、class、case 名三者组合；
4. 只有确认全局唯一后，才单独使用 case 名。

仅在匹配时规范可选的前导 `test/` 和无意义空白。update plan 中保留 CSV 的原始身份值。重复名称或 Markdown 冲突小节仍然有歧义时，不能猜测。

## 填写四个字段

每个单元格保持简洁，并让不同列回答不同问题。

### `测试目的`

说明测试验证的行为，而不是复述错误信息。优先采用 Markdown 中已解释的目的；不存在时，只有既有 purpose 字段可信且与 Markdown 一致才可采用。

推荐形式：

```text
验证 FSDP 多进程训练中参数、梯度与 eager 基线一致。
```

### `解决方案`

记录当前证据支持的动作：

- 已验证的源码修改；
- 必要的 runtime/环境配置；
- 当前环境已通过，因此无需源码修改；
- 明确的不支持能力或仍需完成的 upstream 修复。

不能把 `pass` 当成解决方案。区分源码修复和环境 workaround，也不能把未经测试的建议称为解决方案。

### `最终状态`

使用简短、一致的词汇。优先延续报告已有措辞，否则从以下值中选择：

```text
pass
pass（已修复）
环境规避后pass
环境配置后pass
fail
fail（hang）
fail（硬件相关）
fail（性能门限）
不支持（<能力或版本>）
无法验证
```

只有 Markdown 同时记录修复和修复后成功验证时，才能写 `pass（已修复）`。源码不是根因时使用环境状态。当前精确 case 仍失败时保留 `fail`。

### `遗留原因`

只写尚未解决或限制结论的因素：

- 已无遗留问题，以及旧失败为何过时；
- 当前 backend/hardware/version 能力缺口；
- timeout、hang、性能阈值、缺少资源或证据；
- 尚未完成的验证范围。

不要重复整段解决方案。已解决行可写 `无；当前环境已通过` 或 `无；修复后精确 case 已通过`。

## 创建并应用 update plan

修改 CSV 前，先把语义决定写成可审查的 UTF-8 JSON：

```json
{
  "source_markdown": "/path/to/report.md",
  "reference_columns": ["问题结论"],
  "updates": [
    {
      "row": 2,
      "identity": {
        "test_file": "test/example.py",
        "class_name": "TestExample",
        "case_name": "test_example"
      },
      "values": {
        "测试目的": "验证示例行为。",
        "解决方案": "当前环境实测通过，无需源码修改。",
        "最终状态": "pass",
        "遗留原因": "无；历史错误未复现。"
      }
    }
  ]
}
```

使用 CSV 中准确的身份表头和值。同时写逻辑 CSV 行号（表头计为第 1 行）和足以防止 stale plan 修改重排后错误行的身份字段。

先 dry-run，不写文件：

```bash
python3 <skill-dir>/scripts/backfill_triage_csv.py \
  --csv <input.csv> \
  --plan <updates.json> \
  --dry-run
```

默认建议生成新文件供审查：

```bash
python3 <skill-dir>/scripts/backfill_triage_csv.py \
  --csv <input.csv> \
  --plan <updates.json> \
  --output <updated.csv>
```

只有用户要求覆盖原文件时使用 `--in-place`。helper 会：

- 按精确表头而非固定字母定位目标列；
- 拒绝缺失/重复目标表头和 stale identity；
- 要求每个计划行都提供四个值；
- 保留输入 BOM 状态和 CSV dialect；
- 原子写入；
- 重新解析输出，确认非目标字段和未计划行均未改变。

## 验证结果

写入后独立比较解析后的输入和输出：

- 表头、逻辑行数、宽度、行序和 case 身份相同；
- 每个非目标列的值相同；
- 只有四个目标列中的计划行发生变化；
- 所有请求的目标单元格非空；
- BOM、delimiter、quoting 和内嵌换行仍可正确读取；
- 每个最终状态与最新精确 case 的 Markdown 结果一致；
- 未解决行都有具体遗留原因。

最后汇总更新行数、状态分布、Markdown 证据不足的行和输出路径。有歧义或未匹配行时，不得宣称文档已经完整。
