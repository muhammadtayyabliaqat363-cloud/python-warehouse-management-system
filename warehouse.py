"""
warehouse.py
-------------
Core logic for the Automated Warehouse Management System.

Written in a procedural style (functions operating on plain dictionaries
and lists) as required by the Introduction to Procedural Programming
module. State is held in a single `WarehouseState` container of built-in
data types (dict/list) which every function receives explicitly and
operates on - there is no hidden global state and no classes with
behaviour, keeping the design procedural rather than object-oriented.

Multi-step product assembly:
    Each product has a "recipe" - an ordered list of steps, where each
    step consumes a quantity of a raw resource. A task assembling a
    product must complete each step in order, consuming resources as
    it goes, before the task is marked complete.
"""

from warehouse_exceptions import (
    ResourceNotFoundError,
    InsufficientStockError,
    RobotError,
    WorkerError,
    TaskError,
    ProductError,
)


def new_warehouse_state():
    """Creates a fresh, empty warehouse state as a dictionary of built-in
    data structures. This is the single container of state that every
    other function in this module operates on."""
    return {
        "inventory": {},   # resource_name -> quantity (int)
        "robots": {},      # robot_id -> {"status": "idle"/"busy", "task_id": str or None}
        "workers": {},     # worker_id -> {"name": str, "status": "available"/"busy", "task_id": str or None}
        "products": {},    # product_name -> list of (resource_name, qty) steps
        "tasks": {},       # task_id -> task dict (see create_task)
        "next_task_id": 1,
    }


# ---------------------------------------------------------------------
# Inventory management
# ---------------------------------------------------------------------

def add_resource(state, resource_name, quantity):
    """Adds `quantity` units of `resource_name` to inventory (creates the
    entry if it doesn't already exist)."""
    if not resource_name or not resource_name.strip():
        raise ResourceNotFoundError("Resource name cannot be empty.")
    if quantity <= 0:
        raise ValueError("Quantity to add must be a positive number.")

    inventory = state["inventory"]
    inventory[resource_name] = inventory.get(resource_name, 0) + quantity


def remove_resource(state, resource_name, quantity):
    """Removes `quantity` units of `resource_name` from inventory.
    Raises ResourceNotFoundError if the resource doesn't exist, or
    InsufficientStockError if there isn't enough stock."""
    inventory = state["inventory"]
    if resource_name not in inventory:
        raise ResourceNotFoundError(f"Resource '{resource_name}' not found in inventory.")
    if quantity <= 0:
        raise ValueError("Quantity to remove must be a positive number.")
    if inventory[resource_name] < quantity:
        raise InsufficientStockError(
            f"Insufficient stock of '{resource_name}': have {inventory[resource_name]}, need {quantity}."
        )
    inventory[resource_name] -= quantity


def get_inventory_report(state):
    """Returns a sorted list of (resource_name, quantity) tuples."""
    return sorted(state["inventory"].items())


# ---------------------------------------------------------------------
# Robot management
# ---------------------------------------------------------------------

def add_robot(state, robot_id):
    if robot_id in state["robots"]:
        raise RobotError(f"Robot '{robot_id}' already exists.")
    state["robots"][robot_id] = {"status": "idle", "task_id": None}


def remove_robot(state, robot_id):
    robot = _get_robot(state, robot_id)
    if robot["status"] == "busy":
        raise RobotError(f"Cannot remove robot '{robot_id}' - it is currently busy on a task.")
    del state["robots"][robot_id]


def _get_robot(state, robot_id):
    if robot_id not in state["robots"]:
        raise RobotError(f"Robot '{robot_id}' not found.")
    return state["robots"][robot_id]


# ---------------------------------------------------------------------
# Worker management
# ---------------------------------------------------------------------

def add_worker(state, worker_id, name):
    if worker_id in state["workers"]:
        raise WorkerError(f"Worker '{worker_id}' already exists.")
    if not name or not name.strip():
        raise WorkerError("Worker name cannot be empty.")
    state["workers"][worker_id] = {"name": name, "status": "available", "task_id": None}


def remove_worker(state, worker_id):
    worker = _get_worker(state, worker_id)
    if worker["status"] == "busy":
        raise WorkerError(f"Cannot remove worker '{worker_id}' - they are currently busy on a task.")
    del state["workers"][worker_id]


def _get_worker(state, worker_id):
    if worker_id not in state["workers"]:
        raise WorkerError(f"Worker '{worker_id}' not found.")
    return state["workers"][worker_id]


# ---------------------------------------------------------------------
# Product recipes (define what resources + steps a product needs)
# ---------------------------------------------------------------------

def define_product(state, product_name, steps):
    """Defines a product recipe. `steps` is a list of (resource_name, qty)
    tuples, each representing one assembly step that consumes that many
    units of that resource, in order."""
    if not product_name or not product_name.strip():
        raise ProductError("Product name cannot be empty.")
    if not steps:
        raise ProductError("A product must have at least one assembly step.")
    for resource_name, qty in steps:
        if qty <= 0:
            raise ProductError(f"Step quantity for '{resource_name}' must be positive.")
    state["products"][product_name] = list(steps)


def _get_product_steps(state, product_name):
    if product_name not in state["products"]:
        raise ProductError(f"Product '{product_name}' has no defined recipe.")
    return state["products"][product_name]


# ---------------------------------------------------------------------
# Task management (multi-step assembly, assignment, progress)
# ---------------------------------------------------------------------

def create_task(state, product_name):
    """Creates a new assembly task for `product_name` and returns its
    task_id. The task starts in "pending" status, unassigned, with
    progress at step 0."""
    steps = _get_product_steps(state, product_name)

    task_id = f"T{state['next_task_id']:03d}"
    state["next_task_id"] += 1

    state["tasks"][task_id] = {
        "product": product_name,
        "steps": steps,
        "current_step": 0,
        "status": "pending",       # pending -> in_progress -> completed / cancelled
        "robot_id": None,
        "worker_id": None,
    }
    return task_id


def _get_task(state, task_id):
    if task_id not in state["tasks"]:
        raise TaskError(f"Task '{task_id}' not found.")
    return state["tasks"][task_id]


def assign_task(state, task_id, robot_id=None, worker_id=None):
    """Assigns a pending task to a robot and/or worker. At least one of
    robot_id or worker_id must be provided."""
    task = _get_task(state, task_id)
    if task["status"] != "pending":
        raise TaskError(f"Task '{task_id}' cannot be assigned - it is already '{task['status']}'.")
    if robot_id is None and worker_id is None:
        raise TaskError("A task must be assigned to at least a robot or a worker.")

    if robot_id is not None:
        robot = _get_robot(state, robot_id)
        if robot["status"] == "busy":
            raise RobotError(f"Robot '{robot_id}' is already busy on another task.")
        robot["status"] = "busy"
        robot["task_id"] = task_id
        task["robot_id"] = robot_id

    if worker_id is not None:
        worker = _get_worker(state, worker_id)
        if worker["status"] == "busy":
            raise WorkerError(f"Worker '{worker_id}' is already busy on another task.")
        worker["status"] = "busy"
        worker["task_id"] = task_id
        task["worker_id"] = worker_id

    task["status"] = "in_progress"


def advance_task(state, task_id):
    """Advances an in-progress task by one assembly step, consuming the
    resource required for that step from inventory. If this was the
    final step, the task is marked completed and the assigned robot /
    worker are freed up. Returns the task's status after advancing."""
    task = _get_task(state, task_id)
    if task["status"] != "in_progress":
        raise TaskError(f"Task '{task_id}' cannot be advanced - it is '{task['status']}', not 'in_progress'.")

    step_index = task["current_step"]
    resource_name, qty = task["steps"][step_index]

    # Consume the resource for this step. If stock is insufficient this
    # raises InsufficientStockError and the task's progress is NOT advanced,
    # so the caller can restock and retry safely.
    remove_resource(state, resource_name, qty)

    task["current_step"] += 1

    if task["current_step"] >= len(task["steps"]):
        task["status"] = "completed"
        _free_assignees(state, task)

    return task["status"]


def cancel_task(state, task_id):
    """Cancels a pending or in-progress task and frees any assigned
    robot/worker. Does not refund any resources already consumed."""
    task = _get_task(state, task_id)
    if task["status"] in ("completed", "cancelled"):
        raise TaskError(f"Task '{task_id}' is already '{task['status']}' and cannot be cancelled.")
    task["status"] = "cancelled"
    _free_assignees(state, task)


def _free_assignees(state, task):
    if task["robot_id"] is not None:
        state["robots"][task["robot_id"]]["status"] = "idle"
        state["robots"][task["robot_id"]]["task_id"] = None
    if task["worker_id"] is not None:
        state["workers"][task["worker_id"]]["status"] = "available"
        state["workers"][task["worker_id"]]["task_id"] = None


def get_task_progress(state, task_id):
    """Returns a human-readable "current_step/total_steps" progress string."""
    task = _get_task(state, task_id)
    return f"{task['current_step']}/{len(task['steps'])}"
