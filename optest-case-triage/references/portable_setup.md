# 可移植环境准备

每次开始 case 分析都要完整阅读本文。路径和工具必须从当前环境解析，不得假设最初开发 skill 的容器仍然存在。

## 目录

- [定位 skill 目录](#定位-skill-目录)
- [定位工作仓库](#定位工作仓库)
- [确认 Python 与 PyTorch](#确认-python-与-pytorch)
- [定位工作簿与输出](#定位工作簿与输出)
- [映射 Git remote](#映射-git-remote)
- [处理 runtime 源码验证](#处理-runtime-源码验证)

## 定位 skill 目录

将 `<skill-dir>` 解析为当前所加载 `SKILL.md` 的所在目录。以下配套文件均相对于该目录：

```text
<skill-dir>/requirements.txt
<skill-dir>/scripts/find_case_in_xlsx.py
<skill-dir>/scripts/backfill_triage_csv.py
<skill-dir>/references/portable_setup.md
<skill-dir>/references/official_pytorch_skills.md
<skill-dir>/references/commit_workflow.md
<skill-dir>/references/csv_report_backfill.md
<skill-dir>/references/markdown_report.md
```

不要通过硬编码 clone 路径反推 skill 位置。skill 可能通过符号链接安装、复制到 skills 目录，或直接从 clone 加载。

读取工作簿前检查依赖：

```bash
python3 -c "import openpyxl"
```

缺少依赖时报告下列安装命令，但未经用户允许不要安装：

```bash
python3 -m pip install -r <skill-dir>/requirements.txt
```

## 定位工作仓库

优先使用用户明确指定的 PyTorch checkout。未指定时，只有下列检查全部成功才可采用当前目录：

```bash
git rev-parse --show-toplevel
test -d torch
test -d test
test -f torch/version.py
```

否则应向用户取得 PyTorch checkout 路径，不能猜测主机专用位置。

以 Git 顶层目录为基准解析仓库内测试路径。接受 `test/dynamo/test_x.py` 和 `dynamo/test_x.py`；后者通常表示命令从 `<repo>/test` 运行。

## 确认 Python 与 PyTorch

使用用户提供的环境激活命令。若未提供，保留并记录当前 shell 环境，不 source 猜测的脚本。

pytest 前执行：

```bash
command -v python
python -c "import sys, torch; print(sys.executable); print(torch.__version__); print(torch.__file__)"
python -m pytest --version
```

`torch.__file__` 决定 pytest 实际导入的 runtime 代码。不得假设 Python 版本、virtualenv 布局或 site-packages 前缀。

## 定位工作簿与输出

使用用户提供的工作簿路径。若只给 basename 或行号，在当前任务目录查找唯一匹配的 `.xlsx`；存在多个候选时询问用户。

默认在工作簿旁创建同 basename 的 `.md`。例如 `/data/run.xlsx` 对应 `/data/run.md`。没有工作簿时，使用用户指定的输出路径，或在当前任务目录创建含义清晰的文件。

不得把输出默认到某台机器专用目录。

## 映射 Git remote

`origin`、`upstream`、`official` 是逻辑角色，不保证就是实际 remote 名。fetch 前先检查：

```bash
git -C <repo> remote -v
git -C <repo> branch -vv
```

推荐角色映射：

| 逻辑角色 | 常见名称 | 用途 |
| --- | --- | --- |
| 用户 fork | `origin` | 工作分支，以及用户明确要求的 push |
| 内部主线 | `upstream` | 目标分支同步和内部版本对比 |
| PyTorch GitHub | `official` | 官方 main、release、commit、PR、issue 和 skill |

名称不同时按 URL 或用户说明映射。只 fetch 已存在的 remote。未经用户明确要求，不新增、重命名或重写 remote。

若缺少 official remote，使用 `official_pytorch_skills.md` 的内置指导和 GitHub 链接检索官方修复。文档要注明无法进行本地官方分支包含关系检查，但不能因此阻止整个分析流程。

## 处理 runtime 源码验证

源码树中的测试修改会直接从工作仓库运行。runtime 修改则不一定如此，因为当前环境可能导入已经安装的 torch build。

优先使用该环境支持的 editable/build 工作流。只有用户明确要求“修改安装目录仅用于验证”时，才动态解析包根目录：

```bash
python -c "from pathlib import Path; import torch; print(Path(torch.__file__).resolve().parent)"
```

只同步同一份最小 runtime diff，记录每个仅验证用文件，并且绝不 stage 或 commit 工作仓库之外的文件。不得硬编码安装前缀、Python 版本或包管理器布局。
