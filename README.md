# Tracer

Tracer is a prototype computer-use agent that converts bug reports into
reproducible browser traces, screenshots, and structured evidence for human
review.

It combines bug-report ingestion, LLM-generated task graphs, and browser
automation. The repository demonstrates the pipeline and its intermediate
artifacts; it is not a production bug tracker or an autonomous security-testing
system.

## What Tracer does

1. Accepts a structured JSON bug report or extracts text and images from a PDF.
2. Normalizes supported public bug-report formats into a common schema.
3. Uses Gemini to translate the report and attachment context into a directed
   task graph.
4. Sends each graph node to an Anthropic computer-use demo through Selenium.
5. Records prompts, responses, execution metadata, and browser screenshots in a
   run-specific output directory.
6. Leaves the resulting evidence for a person to review. Tracer does not update
   an external issue tracker or declare a production bug fixed.

The included React application visualizes this flow with public AcademyBugs
sample data. It is a deterministic UI prototype, not a live frontend for the
Python pipeline.

## Architecture

```text
Bug report JSON or PDF
        |
        v
Normalizer / PDF extraction
        |
        v
Gemini task-graph generation
        |
        v
Selenium -> Anthropic computer-use demo -> target browser
        |
        v
Prompts + responses + screenshots + execution_results.json
        |
        v
Human review
```

| Component | Responsibility |
| --- | --- |
| `src/scripts/convert_to_standard_input.py` | Converts AcademyBugs and OWASP Juice Shop-style JSON into Tracer's input schema. |
| `src/ingestion/pdf_processor.py` | Extracts PDF text, embedded images, metadata, and optional OCR text. |
| `src/ingestion/task_graph_generator.py` | Prompts Gemini and validates the returned task-graph structure. |
| `task_graph_integrator.py` | Orders graph nodes and drives the local Anthropic computer-use web UI with Selenium. |
| `src/main_controller.py` | Experimental direct Anthropic agent loop and local execution logging. |
| `frontend/` | React visualization of intake, graph execution, guidance, and review states using static sample data. |

The canonical input shape is documented in
[`docs/standard_input_schema.md`](docs/standard_input_schema.md). Two manually
authored browser graphs are available in `data/task_graphs/`.

## Setup

### Python pipeline

Prerequisites:

- Python 3.10 or newer
- Google Chrome and a compatible ChromeDriver for Selenium workflows
- Tesseract installed on the host if OCR is required
- Docker only for the Anthropic computer-use quickstart workflow

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Add only the credentials needed for the workflow you run:

```dotenv
ANTHROPIC_API_KEY=replace_me
GEMINI_API_KEY=replace_me
```

`.env` and generated run artifacts are ignored. Do not use production customer
reports or credentials in this prototype.

### Frontend visualization

Use a current Node.js LTS release:

```bash
cd frontend
npm ci
npm start
```

The UI opens at `http://localhost:3000` by default. It contains no backend API
integration and labels its execution as a simulation.

## Commands

### Offline checks

Run the JSON utility tests:

```bash
python3 tests/test_json_utils.py
```

Normalize the three public AcademyBugs examples:

```bash
python3 -m src.scripts.convert_to_standard_input \
  --source_file academybugs_bug_reports.json \
  --source_format academybugs \
  --output_dir data/standardized_inputs
```

Compile the Python sources and build the frontend:

```bash
python3 -m compileall -q src task_graph_integrator.py
cd frontend && npm ci && npm run build
```

Run the frontend smoke test without Watchman:

```bash
cd frontend
CI=true npm test -- --watchAll=false --watchman=false
```

### Credential-dependent workflows

Extract a local PDF fixture:

```bash
python3 tests/integration/test_pdf_processor.py /path/to/authorized-report.pdf
```

Generate a task graph from an extracted or normalized input:

```bash
python3 tests/integration/test_task_graph_generator.py \
  data/standardized_inputs/academybugs_currency_freeze_01_standard.json
```

Run the Selenium integration against an already-running Anthropic computer-use
quickstart at `http://localhost:8080`:

```bash
python3 test_firefox_search.py
```

`run_firefox_test.sh` can start the referenced Docker image, but it also replaces
a local container named `anthropic-computer-use`; inspect the script before use.

## Example input and evidence

An included public input looks like this:

```json
{
  "id": "academybugs_currency_freeze_01",
  "title": "Website freezes when changing currency on product page",
  "target_url": "https://academybugs.com/find-bugs/",
  "detailed_steps": [
    "Navigate to the Find Bugs page",
    "Open a product",
    "Select a different currency",
    "Observe whether the page becomes unresponsive"
  ]
}
```

A task-graph run writes evidence with this general shape:

```text
data/outputs/<run>/
├── execution_results.json
├── prompts/
│   └── <timestamp>_<node>.txt
└── responses/
    ├── <timestamp>_<node>.json
    └── <timestamp>_<node>_*.png
```

Exact evidence depends on the external model response, browser state, and target
application. This repository does not claim a measured reproduction rate.

## Tests

| Check | External requirements | What it verifies |
| --- | --- | --- |
| `python3 tests/test_json_utils.py` | None | Dataclass/datetime serialization and file round trips. |
| `python3 -m compileall ...` | None | Python syntax and import-independent compilation. |
| `CI=true npm test -- --watchAll=false --watchman=false` | Installed npm dependencies | Rendering of the public demo fixture list. |
| `npm run build` | Installed npm dependencies | Production compilation of the React visualization. |
| `test_pdf_processor.py` | Local PDF; Tesseract for OCR | PDF extraction and artifact creation. |
| `test_task_graph_generator.py` | `GEMINI_API_KEY` | LLM task-graph generation from prepared input. |
| `test_chrome_search.py` | `ANTHROPIC_API_KEY`; supported Anthropic API behavior | Experimental direct agent execution. |
| `test_firefox_search.py` | `ANTHROPIC_API_KEY`, Docker quickstart, Chrome/ChromeDriver | Selenium orchestration of the computer-use demo. |

The integration files are executable smoke-test scripts rather than a hermetic
CI suite. Credential-dependent results must be reviewed manually.

## Supported environments

- The Python modules are intended for macOS or Linux with Python 3.10+.
- Browser execution assumes Chrome/ChromeDriver. The target browser inside the
  Anthropic quickstart may be Firefox.
- The frontend is a Create React App project and is best run with a current
  Node.js LTS version.
- Windows is not currently verified; the shell and Docker helpers are POSIX
  scripts.

## Current status and limitations

Tracer is an archived prototype rather than a maintained service. The repository
demonstrates the ingestion-to-evidence architecture, but several boundaries are
important:

- The React frontend uses static public sample data and is not connected to the
  Python pipeline.
- The legacy Create React App dependency tree retains known transitive audit
  findings. Do not deploy it without migrating to maintained build tooling and
  reviewing the replacement lockfile.
- End-to-end execution requires external API credentials and, for the Selenium
  path, Anthropic's separate computer-use quickstart container.
- Browser selectors are coupled to the quickstart UI and may break as that UI
  changes.
- Model identifiers in the prototype are dated and may need an explicit upgrade
  before credential-dependent runs work.
- `src/main_controller.py` can execute model-requested shell commands with only a
  minimal denylist. Run it only in an isolated environment with non-sensitive
  data.
- Some screenshot handling in the direct controller is placeholder behavior; the
  Selenium integrator is the path that captures browser screenshots.
- Task graphs and confidence values are model outputs, not calibrated success
  probabilities.
- There is no reliability benchmark, hosted demo, CI workflow, persistence layer,
  authentication, or production security hardening in the current tree.
- No license file is included, so reuse rights are not granted by this repository.

Only run Tracer against applications and data you are authorized to test.

## Demo capture checklist

No safe end-to-end demo recording is currently committed. To create one without
fabricating results:

1. Use one of the public AcademyBugs fixtures.
2. Start from a clean browser profile with no personal accounts, bookmarks, or
   extension data visible.
3. Record the input report, generated task graph, live browser actions, and final
   evidence directory in one continuous capture.
4. Redact API keys, local usernames, filesystem paths, cookies, and unrelated
   browser tabs.
5. Add a caption distinguishing live agent output from the static frontend
   simulation.
6. Review every frame before committing a GIF, video, or screenshot.

## Recognition and history

Tracer was built during a short 2025 prototype sprint and contributed to a YC
Summer 2025 interview. That recognition is historical context, not evidence of
product adoption or current operational status.

Git history shows the core ingestion, task-graph, and agent-controller work was
built by Rohan Katakam. Jonathan Politzki contributed the React frontend prototype
and portions of the task-graph generator. The historical `roadmap.md` records
planned work and should not be read as a list of completed features.
