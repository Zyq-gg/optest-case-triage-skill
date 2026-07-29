# CSV Report Backfill

Use this reference only for the standalone document-processing workflow that
copies completed triage conclusions from Markdown into a user-provided CSV. Do
not mix it into case reproduction, diagnosis, source patching, or pytest
validation.

## Contents

- [Purpose And Authority](#purpose-and-authority)
- [Inspect The Inputs](#inspect-the-inputs)
- [Build A Case Evidence Ledger](#build-a-case-evidence-ledger)
- [Write The Four Fields](#write-the-four-fields)
- [Create And Apply An Update Plan](#create-and-apply-an-update-plan)
- [Validate The Result](#validate-the-result)

## Purpose And Authority

Use this flow when the user already has a Markdown triage report and asks to
populate these CSV columns:

- `测试目的`
- `解决方案`
- `最终状态`
- `遗留原因`

Apply this evidence order:

1. Current, exact-case validation recorded in the Markdown report.
2. Current root cause, fix, environment constraint, and residual risk recorded
   in the Markdown report.
3. Relevant auxiliary CSV columns selected by header and content.
4. Older CSV errors, conclusions, or historical notes.

Treat the Markdown report as authoritative when sources conflict. Auxiliary
information such as a prior `问题结论` column is context, not proof. Its position
is not stable: it may be column L in one file and a differently named or
positioned column in another. Never hard-code a column letter.

This flow summarizes completed analysis. It does not silently start a new
one-case triage run. If the Markdown lacks enough evidence for a row, report the
gap. When the user requires every row to be populated, use `无法验证` only with a
specific residual reason such as `Markdown 无该精确 case 的当前验证记录`; do not
promote an old auxiliary conclusion to a current result.

## Inspect The Inputs

Parse the CSV with Python's `csv` module, not line-oriented shell tools. Quoted
fields can contain commas and newlines.

Before editing, record:

- encoding and whether a UTF-8 BOM is present;
- delimiter, line ending, header order, column count, and logical row count;
- the case identity columns, preferably file, class, and case/test name;
- the positions of the four target headers by their names;
- all potentially useful auxiliary columns based on their headers and sampled
  values.

The first three columns are often `test_file`, `class_name`, and `case_name`,
but names vary. Confirm their meaning from the header and contents. Do not use
the first three columns blindly when they are not case identity fields.

Read the Markdown report completely enough to cover every requested row.
Consolidate repeated or historical sections before writing the CSV: the newest
exact-case result wins, while older attempts remain background evidence.

## Build A Case Evidence Ledger

Create one internal record per logical CSV row:

```text
CSV row + exact CSV identity
Markdown section(s) and any recorded XLSX row/nodeid
current reproduction result
root cause or capability limitation
validated source fix or environment configuration
remaining blocker or risk
auxiliary columns consulted
```

Match with the strongest available combination:

1. recorded spreadsheet row plus exact case identity;
2. exact pytest nodeid;
3. file, class, and case name together;
4. unique case name only when uniqueness has been checked.

For matching only, normalize an optional leading `test/` path prefix and trivial
whitespace. Preserve the CSV's original identity values in the update plan.
When duplicate names or conflicting Markdown sections remain ambiguous, do not
guess.

## Write The Four Fields

Keep every cell concise and make each column answer a different question.

### `测试目的`

State the behavior the test verifies, not its error message. Prefer the purpose
already explained in Markdown. If absent, use a trustworthy existing purpose
field only when it is consistent with the Markdown evidence.

Good form:

```text
验证 FSDP 多进程训练中参数、梯度与 eager 基线一致。
```

### `解决方案`

State the action supported by current evidence:

- the validated source change;
- the required runtime/environment configuration;
- no source change because the current environment passes;
- a precise unsupported capability or still-needed upstream fix.

Do not write `pass` as a solution. Distinguish a source fix from an environment
workaround, and do not call an untested proposal a solution.

### `最终状态`

Use a compact, consistent vocabulary. Prefer the report's established wording;
otherwise use one of:

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

Use `pass（已修复）` only when the Markdown records both the fix and a successful
post-fix validation. Use an environment status when source code was not the
cause. Keep `fail` when the current exact-case run still fails.

### `遗留原因`

Describe only what remains unresolved or what constrains the conclusion:

- no residual issue and why an older failure is obsolete;
- current backend/hardware/version capability gap;
- timeout, hang, performance threshold, missing resource, or missing evidence;
- validation scope that is still incomplete.

Do not duplicate the whole solution. For resolved rows, a short form such as
`无；当前环境已通过` or `无；修复后精确 case 已通过` is sufficient.

## Create And Apply An Update Plan

Make semantic decisions reviewable before changing the CSV. Write a UTF-8 JSON
plan in this form:

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

Use the exact identity header names and values from the CSV. Include both the
logical CSV row number, counting the header as row 1, and enough identity fields
to prevent a stale plan from touching a reordered row.

Validate without writing:

```bash
python3 <skill-dir>/scripts/backfill_triage_csv.py \
  --csv <input.csv> \
  --plan <updates.json> \
  --dry-run
```

Prefer writing a new file for review:

```bash
python3 <skill-dir>/scripts/backfill_triage_csv.py \
  --csv <input.csv> \
  --plan <updates.json> \
  --output <updated.csv>
```

Use `--in-place` only when the user asked to update the original. The helper:

- resolves target columns by exact header, not fixed letters;
- rejects missing/duplicate target headers and stale identity matches;
- requires all four values for every planned row;
- preserves the input BOM state and CSV dialect;
- writes atomically;
- reparses the output and verifies that no non-target field or unplanned row
  changed.

## Validate The Result

After writing, independently compare parsed input and output:

- identical headers, logical row count, width, row order, and case identities;
- identical values in every non-target column;
- changes only in the four target columns and only for planned rows;
- all requested target cells are non-empty;
- BOM, delimiter, quoting behavior, and embedded newlines remain readable;
- each final status agrees with the newest exact-case Markdown result;
- unresolved rows have a concrete residual reason.

Summarize the number of updated rows, status distribution, rows without adequate
Markdown evidence, and output path. Do not claim the document is complete when
ambiguous or unmatched rows remain.
