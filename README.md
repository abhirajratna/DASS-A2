# DASS-A2

This repository contains Assignment 2 work for DASS, including:

- Blackbox testing
- Whitebox testing
- Integration testing (`StreetRace Manager` command-line system)

## Links

- GitHub Repository: https://github.com/abhirajratna/DASS-A2/tree/main
- Google Drive Submission Folder: https://drive.google.com/drive/folders/1xLgpr5w5_ibhodUdzNofRtPhmzGYeeaK?usp=sharing

## Repository Structure

```text
DASS-A2/
├── blackbox/
│   └── tests/
│       ├── conftest.py
│       └── test_blackbox_api.py
├── whitebox/
│   └── tests/
│       ├── conftest.py
│       └── test_white_box_cases.py
├── integration/
│   ├── code/
│   │   ├── main.py
│   │   └── streetrace_manager/
│   │       ├── registration.py
│   │       ├── crew_management.py
│   │       ├── inventory.py
│   │       ├── race_management.py
│   │       ├── results.py
│   │       ├── mission_planning.py
│   │       ├── vehicle_maintenance.py
│   │       ├── reputation.py
│   │       ├── models.py
│   │       └── system.py
│   ├── diagrams/
│   └── tests/
│       ├── conftest.py
│       └── test_streetrace_integration.py
└── README.md
```

## Prerequisites

- Linux/macOS/Windows
- Python 3.10+
- `pip`

## Setup

From the repository root (`DASS-A2`):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip pytest
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -U pip pytest
```

## How to Run the Code (StreetRace Manager CLI)

From repository root:

```bash
python integration/code/main.py
```

You can use commands such as:

- `help`
- `register <name>`
- `assign <name> <role> <skill_level>`
- `addcar <car_id> <model words...>`
- `createrace <race_id> <driver_name> <car_id> <race name words...>`
- `completerace <race_id> <position> <prize_money> <damaged:true|false>`
- `mission <mission_id> <mission_type> <roles comma separated>`
- `showcash`
- `showrep`
- `exit`

## How to Run Tests

Run all tests:

```bash
pytest -q
```

Run only blackbox tests:

```bash
pytest -q blackbox/tests/test_blackbox_api.py
```

Run only whitebox tests:

```bash
pytest -q whitebox/tests/test_white_box_cases.py
```

Run only integration tests:

```bash
pytest -q integration/tests/test_streetrace_integration.py
```

Run all suites folder-wise (explicit):

```bash
pytest -q blackbox/tests whitebox/tests integration/tests
```

## Integration Module Summary

Required modules implemented:

- Registration
- Crew Management
- Inventory
- Race Management
- Results
- Mission Planning

Additional modules implemented:

- Vehicle Maintenance
- Reputation

## Artifacts

Integration diagrams and report files are available under:

- `integration/diagrams/`
- `integration/tests/integration_test_design_and_results.md`

