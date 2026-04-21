
# 🏭 LinguaFrancaWarehouse

A reactive simulation of an automated vertical warehouse robot, built with [LinguaFranca](https://lf-lang.org/) (Python target) and the [Frost framework](https://github.com/glacier-project/frost.git). Robot motion planning is handled declaratively through **egglog** (e-graph rewriting rules), making the planning logic formal, composable, and inspectable.

> **Reference paper:** *Frost: A Simulation Platform for Early Validation and Testing of Manufacturing Software* — IEEE INDIN 2025

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Warehouse Layout](#warehouse-layout)
- [Mission Types](#mission-types)
- [Planning Engine (egglog)](#planning-engine-egglog)
- [LinguaFranca Reactors](#linguafranca-reactors)
- [Data Models](#data-models)
- [Production Plan (JSON)](#production-plan-json)
- [Getting Started](#getting-started)
- [Development](#development)

---

## Overview

The system simulates a robotic vertical warehouse capable of autonomously executing the following operations:

- **ExtractTray** — retrieve a specific tray (by ID) or the first queued tray and deliver it to the bay
- **SendBack** — return the tray at the bay to a free storage slot
- **FetchAnyEmpty** — fetch any empty tray and bring it to the bay

A **Scheduler** reads a JSON production plan and dispatches tasks sequentially over a Frost message bus. The **WarehouseUnit** receives tasks, executes them tick by tick via a 50 ms control loop, and reports completion back to the scheduler.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     FactoryMain (.lf)                        │
│                                                              │
│  ┌─────────────┐        FrostBus       ┌──────────────────┐  │
│  │  Scheduler  │◄──────────────────────►│  WarehouseUnit   │  │
│  │    (.lf)    │    (width=2, 10ms lag) │      (.lf)       │  │
│  └─────────────┘                        └────────┬─────────┘  │
│                                                  │             │
│                                         ┌────────▼──────────┐ │
│                                         │WarehouseController │ │
│                                         │   (Python)         │ │
│                                         └────────┬──────────┘ │
│                                                  │             │
│                                    ┌─────────────▼──────────┐ │
│                                    │      cfg_engine.py      │ │
│                                    │  (egglog, per-tick)     │ │
│                                    └────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

Communication uses typed `FrostMessage` objects routed through `FrostBus`. Each request carries a UUID correlation ID that the WarehouseUnit echoes back in its `PHYSICAL_DONE` completion signal, allowing the Scheduler to match responses precisely.

---

## Repository Structure

```
LinguaFrancaWarehouse/
│
├── frost/                          # Frost framework (bundled as subdirectory)
│   └── src/
│       ├── lib/
│       │   ├── FrostBase.lf
│       │   ├── FrostBus.lf
│       │   ├── FrostDataModel.lf
│       │   ├── FrostInterface.lf
│       │   ├── FrostMachine.lf
│       │   ├── FrostReactor.lf
│       │   └── message_protocol/MessageFilter.lf
│       └── python_lib/
│           ├── frost.py
│           ├── l_formatter.py
│           └── time_utils.py
│
├── src/                            # Application source
│   ├── FactoryMain.lf              # Top-level reactor (entry point)
│   ├── WarehouseUnit.lf            # Physical machine reactor
│   ├── Scheduler.lf                # Mission scheduler reactor
│   └── python/
│       ├── warehouse.py            # Warehouse layout & slot management
│       ├── warehouse_platform.py   # Robot platform (position, pick/place)
│       ├── warehouse_controller.py # Mission state machine (IDLE/FETCH/DELIVER)
│       ├── cfg_engine.py           # egglog planning engine
│       ├── slot.py                 # Slot data model
│       └── tray.py                 # Tray data model
│
├── models/                         # YAML data models & JSON plans
│   ├── warehouse.yml               # WarehouseUnit data model (nodes & methods)
│   ├── scheduler.yml               # Scheduler data model
│   ├── frost_bus.yml               # FrostBus data model
│   └── production_plan.json        # Example mission plan
│
├── tests/                          # Pytest test suite
│   ├── test_cfg_engine.py
│   ├── test_platform.py
│   ├── test_slot.py
│   ├── test_tray.py
│   ├── test_warehouse.py
│   └── test_warehouse_controller.py
│
├── docs/                           # Sphinx documentation (autoapi)
├── scripts/                        # Dev utility scripts
├── utils/
│   └── commands.yaml               # Manual command sequence example
│
├── pyproject.toml                  # Poetry project definition
├── requirements.txt                # Runtime deps (pinned)
├── requirements-dev.txt            # Dev/CI deps (pinned)
├── tox.ini                         # Tox environments (test, type, lint, coverage)
└── pytest.ini                      # Pytest configuration
```

---

## Warehouse Layout

The warehouse is a vertical structure with **20 rows** and two columns.

```
Row   X = +0.7 (Right)        X = -0.7 (Left)
───   ──────────────────       ────────────────
 0    queue_0   (Queue)        storage_L_0
 1    queue_1   (Queue)        storage_L_1
 2    queue_2   (Queue)        storage_L_2
 3    in_view   (Bay  )        storage_L_3
 4    storage_R_4              storage_L_4
...   ...                      ...
19    storage_R_19             storage_L_19

Row height: 0.16725 m   |   Y position = row × 0.16725
```

**Slot types:**

| Type | ID pattern | Count | Role |
|---|---|---|---|
| `storage` | `storage_L_N`, `storage_R_N` | 36 | Long-term tray storage |
| `queue` | `queue_0`, `queue_1`, `queue_2` | 3 | Staging between storage and bay |
| `bay` | `in_view` | 1 | Operator access / inspection point |

**Initial tray configuration (auto-assigned IDs 1–6):**

| Tray ID | Slot | Weight |
|---|---|---|
| 1 | storage_L_0 | 3.5 kg (full) |
| 2 | storage_L_5 | 2.9 kg (full) |
| 3 | storage_R_7 | 2.6 kg (full) |
| 4 | storage_L_10 | 3.0 kg (full) |
| 5 | storage_R_15 | 3.1 kg (full) |
| 6 | queue_0 | 2.0 kg (empty) |

A **Tray** is considered empty if `weight ≤ 2.97 kg` (i.e. `MIN_W + 0.01`, where `MIN_W = 2.960 kg`).

**Platform kinematics (50 ms tick):**

| Axis | Speed | Step per tick |
|---|---|---|
| Y (vertical) | 0.20 m/s | 0.010 m |
| X (horizontal) | 0.15 m/s | 0.0075 m |

---

## Mission Types

| Mission | Method call | Description |
|---|---|---|
| `ExtractTray(N)` | `extract(tray_id=N)` | Fetch tray N from anywhere and deliver to bay |
| `ExtractTray()` | `extract()` | Fetch the first occupied queue slot and deliver to bay |
| `SendBack` | `sendback()` | Move tray from bay to any free storage slot |
| `FetchAnyEmpty` | `fetch_any_empty()` | Pick any empty tray and deliver to bay |
| `Enqueue(N)` | enqueue(tray_id=N) | Move a specific tray from storage to a free queue slot |

Every mission goes through two phases managed by `WarehouseController`:

1. **FETCH** — navigate to the source slot, pick up the tray
2. **DELIVER** — navigate to the destination slot, place the tray

On each 50 ms tick, the controller queries the egglog engine for the next atomic action and executes it on the `Platform`.

---

## Planning Engine (egglog)

`cfg_engine.py` encodes all navigation decisions as **e-graph rewriting rules** using `egglog` (≥ 13.0.0).

On every tick, `get_next_action_from_egglog(...)` builds a fresh `EGraph`, registers the full warehouse state (every slot with its type, position, and tray contents), and extracts the next action for the given robot state and command.

**Rule groups:**

| Rule | Condition | Action produced |
|---|---|---|
| FETCH: move Y | robot not at target Y | `update_y(sy)` |
| FETCH: move X | at target Y, not at target X | `update_x(sx)` |
| FETCH: pick | at exact target position | `pick()` |
| FETCH_ANY_EMPTY | same, but targets trays with `is_full = False` | same sequence |
| SEARCH_TARGET | holding tray, seeking a free typed slot | `lock(slot_id)` |
| DELIVER: move Y/X/place | locked target slot exists | navigation + `place()` |
| IDLE | any state with `Command.idle()` | `wait()` |

Navigation is always **Y-first, then X**. The `lock` action reserves a destination slot before the robot starts moving, preventing reassignment mid-mission.

**Possible actions:**

| Action | Meaning |
|---|---|
| `update_y(val)` | Move platform one step toward Y = `val` |
| `update_x(val)` | Move platform one step toward X = `val` |
| `pick()` | Pick up tray at current position |
| `place()` | Place tray at current position |
| `lock(slot_id)` | Reserve destination slot for delivery |
| `wait()` | No action (idle or preconditions unmet) |

---

## LinguaFranca Reactors

### WarehouseUnit (`src/WarehouseUnit.lf`)

Extends `FrostMachine`. Owns the physical warehouse simulation.

- **`startup`**: initializes `Warehouse` and `WarehouseController`, sets data model nodes (`pos_y`, `tray_at_bay`, `Busy`).
- **`message_filter.requests`**: dispatches `ExtractTray`, `SendBack`, `FetchAnyEmpty` to the controller. If the controller is already busy, tasks are queued in `pending_tasks` (keyed by correlation ID). Rejected tasks (e.g. bay already full) return a `PHYSICAL_ERROR_IMPOSSIBLE` error immediately.
- **`control_loop`** (timer, every **50 ms**): calls `wh_ctrl.tick()`. On mission completion, sends a `PHYSICAL_DONE` response to the originating sender, removes the task from the queue, and attempts to start the next pending task.

### Scheduler (`src/Scheduler.lf`)

Extends `FrostReactor`. Reads a JSON plan and drives tasks sequentially.

- **`startup`**: parses the `scheduling_instance` JSON file into an internal `task_queue`.
- **`connected_to_bus`**: sends the first task as soon as the bus is available.
- **`message_filter.responses`**: waits for `PHYSICAL_DONE` with the matching `correlation_id` before scheduling the next task (50 ms delay). Intermediate responses (e.g. status updates) are skipped.
- **`message_filter.errors`**: on error, resets waiting state and schedules the next task after 1 second.

### FactoryMain (`src/FactoryMain.lf`)

Top-level composition. Timeout: **200 seconds**, single-threaded.

```
warehouse.channel_out  ┐
scheduler.channel_out  ┘─→ bus.channel_in

bus.channel_out ─→ warehouse.channel_in   (after 10 msec)
             ─→ scheduler.channel_in    (after 10 msec)
```

The 10 ms logical delay on bus output prevents zero-time causality cycles.

---

## Data Models

YAML data models in `models/` define the node tree exposed by each Frost machine.

**`models/warehouse.yml`** — nodes on `WarehouseUnit`:

| Node | Type | Description |
|---|---|---|
| `Machine/ExtractTray` | AsyncMethod | Extract tray (optional `tray_number` arg) |
| `Machine/SendBack` | AsyncMethod | Return tray to storage |
| `Machine/FetchAnyEmpty` | AsyncMethod | Fetch any empty tray |
| `Machine/Status/pos_y` | NumericalVariable | Current Y position |
| `Machine/Status/tray_at_bay` | NumericalVariable | Tray ID at bay (0 = empty) |
| `Machine/Status/Busy` | BooleanVariable | True while a mission is running |
| `Machine/Control/target_y` | NumericalVariable | Target Y position |
| `Machine/Enqueue` | AsyncMethod | Move tray N from storage to a free queue slot |

---

## Production Plan (JSON)

The scheduler loads a JSON file structured as follows (see `models/production_plan.json`):

```json
{
  "jobs": [
    {
      "id": "Job_Stress",
      "name": "Stress_Test_Sequenziale",
      "tasks": [
        {
          "id": "T1",
          "name": "ExtractTray",
          "eligible_machines": ["warehouseunit"],
          "processing_time": 20,
          "parameters": {
            "tray_number": 2
          }
        },
        {
          "id": "T2",
          "name": "SendBack",
          "eligible_machines": ["warehouseunit"],
          "processing_time": 20,
          "dependencies": ["T1"]
        },
        {
          "id": "T3",
          "name": "FetchAnyEmpty",
          "eligible_machines": ["warehouseunit"],
          "processing_time": 20,
          "dependencies": ["T1", "T2"]
        },
        {
          "id": "T4",
          "name": "SendBack",
          "eligible_machines": ["warehouseunit"],
          "processing_time": 20,
          "dependencies": ["T1", "T2", "T3"]
        },
        {
          "id": "T5",
          "name": "Enqueue",
          "eligible_machines": ["warehouseunit"],
          "processing_time": 20,
          "parameters": {
            "tray_number": 3
          },
          "dependencies": ["T1", "T2", "T3", "T4"]
        }
      ]
    }
  ],
  "machines": [
    { "id": "warehouseunit", "name": "warehouseunit" }
  ]
}
```

- `name` maps to a `Machine/` method on the WarehouseUnit.
- `parameters.tray_number` is optional; if present, it is passed as the first method argument.
- `dependencies` are read by the planner; the Scheduler currently dispatches tasks sequentially in list order.

---

## Getting Started

### Prerequisites

- Python ≥ 3.12
- [Poetry](https://python-poetry.org/)
- [LinguaFranca CLI (`lfc`)](https://www.lf-lang.org/docs/installation)
- **Internal dependencies** (available from the organization's repository):
  - `machine-data-model` 
  - `frost-planner`

### Clone and setup

```bash
# Clone the main repository
git clone https://github.com/Eragon77/LinguaFrancaWarehouse.git
cd LinguaFrancaWarehouse

# Clone required dependencies alongside the main project
git clone https://github.com/glacier-project/machine-data-model.git ../machine-data-model
git clone https://github.com/glacier-project/frost-planner.git ../frost-planner
```

### Install dependencies

```bash
poetry install
```

> The Frost framework is **bundled** inside the `frost/` subdirectory — no separate clone is required.

### Run the simulation

```bash
# Compile
lfc src/FactoryMain.lf

# Execute
python src-gen/FactoryMain/FactoryMain.py
```

Make sure the `scheduling_instance` state in `Scheduler.lf` points to your JSON plan (e.g. `models/production_plan.json`).

---

## Development

### Run tests

```bash
# Direct
poetry run pytest tests/
```

### Scripts

| Script | Purpose |
|---|---|
| `scripts/apply_cstyle.sh` | Apply code style (ruff / black) |
| `scripts/gen_requirements.sh` | Regenerate pinned requirements files |
| `scripts/radon.sh` | Complexity metrics |
| `scripts/run_tox.sh` | Run the full tox suite |

### Build documentation

```bash
cd docs
make html
# Output: docs/build/html/
```

---

## References

- Frost framework: [https://github.com/glacier-project/frost.git](https://github.com/glacier-project/frost.git)
- LinguaFranca: [https://lf-lang.org](https://lf-lang.org)
- egglog: [https://github.com/egraphs-good/egglog](https://github.com/egraphs-good/egglog)
- Frost paper: *Frost: A Simulation Platform for Early Validation and Testing of Manufacturing Software*, IEEE INDIN 2025