# Automated Warehouse Management System

A Python application built with **procedural programming** principles that simulates an automated warehouse: managing robots, workers, inventory, and multi-step product assembly tasks.

Originally developed for the *Introduction to Procedural Programming* module (CFS2103) at the University of Huddersfield.

## Features

- **Inventory management** — add/remove stock of raw resources, view a live inventory report
- **Robot & worker management** — add/remove robots and workers, with protection against removing ones currently busy on a task
- **Product recipes** — define multi-step assembly recipes (e.g. a "chair" needs 4 wood then 8 screws)
- **Multi-step task assembly** — tasks progress step-by-step, consuming resources at each step, only completing once every step is done
- **Robust error handling** — custom exception hierarchy (`WarehouseError` and subclasses) gives specific, meaningful errors for invalid actions: insufficient stock, double-booking a busy robot, advancing a task with no stock left, etc.
- **Text-based UI (TUI)** — simple numbered menu
- **Fully unit tested** — 28 tests covering inventory, robots, workers, recipes, and the full multi-step task lifecycle including failure cases

## Design overview

This is deliberately **procedural**, not object-oriented, to match the module's learning outcomes:

- All warehouse state lives in one plain dictionary (`new_warehouse_state()`), built entirely from built-in data types (`dict`, `list`, `tuple`) — there are no classes with behaviour
- Every function takes `state` explicitly and operates on it — no hidden global state
- Logic (`warehouse.py`) is fully separated from user interaction (`main.py`), so the core functions can be tested and reused independently of the TUI

### File structure

| File | Responsibility |
|---|---|
| `warehouse.py` | Core logic — inventory, robots, workers, products, tasks |
| `warehouse_exceptions.py` | Custom exception hierarchy for specific, meaningful errors |
| `main.py` | Text-based user interface, delegates all logic to `warehouse.py` |
| `test_warehouse.py` | 28 unit tests covering normal and edge/error cases |

### How multi-step assembly works

A product recipe is an ordered list of `(resource, quantity)` steps, e.g.:

```python
define_product(state, "chair", [("wood", 4), ("screws", 8)])
```

Creating a task for that product starts it at step 0. Each call to `advance_task()` consumes the resource for the *current* step and moves to the next one. If stock runs out partway through, the step is **not** consumed and the task's progress does not move on — so you can restock and safely retry. Once the final step is consumed, the task is marked `completed` and its assigned robot/worker are automatically freed up.

## Getting started

### Requirements
- Python 3.8+

### Run the program

```bash
python3 main.py
```

### Run the tests

```bash
python3 -m unittest test_warehouse.py -v
```

## Example usage

```
=== Automated Warehouse Management System ===
--- Warehouse Menu ---
 1. Add resource to inventory
 2. View inventory
 3. Add robot
 4. Remove robot
 5. Add worker
 6. Remove worker
 7. Define product recipe
 8. Create assembly task
 9. Assign task to robot/worker
10. Advance task by one step
11. Cancel task
12. View all tasks
 0. Exit
```

## Possible future improvements

- Task priority/scheduling queue when multiple tasks compete for the same robot
- Persist warehouse state to disk between runs
- Reporting on average task completion time per robot/worker
