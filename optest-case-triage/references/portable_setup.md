# Portable Setup

Read this reference at the start of every triage run. Resolve paths and tools
from the current environment; never assume the original development container
exists.

## Contents

- [Resolve The Skill Directory](#resolve-the-skill-directory)
- [Resolve The Working Repository](#resolve-the-working-repository)
- [Resolve Python And PyTorch](#resolve-python-and-pytorch)
- [Resolve Workbook And Output](#resolve-workbook-and-output)
- [Map Git Remotes](#map-git-remotes)
- [Handle Runtime Source Validation](#handle-runtime-source-validation)

## Resolve The Skill Directory

Set `<skill-dir>` to the directory containing the loaded `SKILL.md`. Required
bundled files are relative to it:

```text
<skill-dir>/requirements.txt
<skill-dir>/scripts/find_case_in_xlsx.py
<skill-dir>/scripts/backfill_triage_csv.py
<skill-dir>/references/portable_setup.md
<skill-dir>/references/official_pytorch_skills.md
<skill-dir>/references/commit_workflow.md
<skill-dir>/references/csv_report_backfill.md
```

Do not reconstruct the path from a hard-coded clone location. The skill may be
installed by symlink, copied into a skills directory, or loaded directly from a
clone.

Before workbook lookup, check the helper dependency:

```bash
python3 -c "import openpyxl"
```

If it is missing, report this command but do not install without permission:

```bash
python3 -m pip install -r <skill-dir>/requirements.txt
```

## Resolve The Working Repository

Use the PyTorch checkout explicitly named by the user. If none is named, use the
current directory only when all of these checks succeed:

```bash
git rev-parse --show-toplevel
test -d torch
test -d test
test -f torch/version.py
```

Otherwise ask for the PyTorch checkout path. Do not guess a host-specific
location.

Resolve repository-relative test paths against the Git top level. Accept both
`test/dynamo/test_x.py` and `dynamo/test_x.py`; the second form normally assumes
the command runs from `<repo>/test`.

## Resolve Python And PyTorch

Use the environment activation command provided by the user. If none is
provided, use the current shell environment and record it rather than sourcing a
guessed script.

Run these checks before pytest:

```bash
command -v python
python -c "import sys, torch; print(sys.executable); print(torch.__version__); print(torch.__file__)"
python -m pytest --version
```

The reported `torch.__file__` determines which runtime code pytest imports. Do
not assume a Python version, virtualenv layout, or site-packages prefix.

## Resolve Workbook And Output

Use the workbook path provided by the user. If only a basename or row is given,
search the current task directory for a unique matching `.xlsx`; ask when more
than one candidate remains.

By default, write the analysis beside the workbook with `.xlsx` replaced by
`.md`. For `/data/run.xlsx`, use `/data/run.md`. When there is no workbook, use
the output path requested by the user or create a clearly named file in the
current task directory.

Never default output to a machine-specific directory.

## Map Git Remotes

Treat `origin`, `upstream`, and `official` as logical roles, not guaranteed
names. Inspect before fetching:

```bash
git -C <repo> remote -v
git -C <repo> branch -vv
```

Preferred role mapping:

| Role | Typical name | Purpose |
| --- | --- | --- |
| user fork | `origin` | working branches and explicitly requested pushes |
| internal main | `upstream` | target branch synchronization and internal comparisons |
| PyTorch GitHub | `official` | official main, releases, commits, PRs, issues, and skills |

Map by URL or user instruction when names differ. Fetch only remotes that exist.
Do not add, rename, or rewrite remotes unless the user explicitly asks.

If the official remote is absent, use the bundled
`official_pytorch_skills.md` guidance and its GitHub links. Official fix search
can use GitHub browsing. Record that local official branch-containment checks
were unavailable; do not block the whole triage.

## Handle Runtime Source Validation

Source-tree test changes run directly from the working repository. Runtime
changes may not if the active environment imports an installed torch build.

First prefer the environment's supported editable/build workflow. If the user
explicitly wants a validation-only installed-tree patch, derive the root:

```bash
python -c "from pathlib import Path; import torch; print(Path(torch.__file__).resolve().parent)"
```

Apply only the same minimal runtime diff, record every validation-only file, and
never stage or commit files outside the working repository. Do not hard-code an
installation prefix, a Python version, or a package-manager layout.
