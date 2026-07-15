"""
main.py
--------
Text-based user interface (TUI) for the Automated Warehouse Management
System. Handles all user input/output and delegates all logic to the
functions in warehouse.py, catching and reporting warehouse_exceptions
with meaningful messages.
"""

import warehouse as wh
from warehouse_exceptions import WarehouseError


def print_menu():
    print("\n--- Warehouse Menu ---")
    print(" 1. Add resource to inventory")
    print(" 2. View inventory")
    print(" 3. Add robot")
    print(" 4. Remove robot")
    print(" 5. Add worker")
    print(" 6. Remove worker")
    print(" 7. Define product recipe")
    print(" 8. Create assembly task")
    print(" 9. Assign task to robot/worker")
    print("10. Advance task by one step")
    print("11. Cancel task")
    print("12. View all tasks")
    print(" 0. Exit")


def read_int(prompt):
    while True:
        value = input(prompt).strip()
        try:
            n = int(value)
            if n <= 0:
                print("Please enter a positive whole number.")
                continue
            return n
        except ValueError:
            print("Please enter a valid whole number.")


def add_resource_flow(state):
    name = input("Resource name: ").strip()
    qty = read_int("Quantity to add: ")
    wh.add_resource(state, name, qty)
    print(f"Added {qty} of '{name}' to inventory.")


def view_inventory_flow(state):
    report = wh.get_inventory_report(state)
    if not report:
        print("Inventory is empty.")
        return
    for name, qty in report:
        print(f"  {name}: {qty}")


def add_robot_flow(state):
    robot_id = input("New robot ID: ").strip()
    wh.add_robot(state, robot_id)
    print(f"Robot '{robot_id}' added.")


def remove_robot_flow(state):
    robot_id = input("Robot ID to remove: ").strip()
    wh.remove_robot(state, robot_id)
    print(f"Robot '{robot_id}' removed.")


def add_worker_flow(state):
    worker_id = input("New worker ID: ").strip()
    name = input("Worker name: ").strip()
    wh.add_worker(state, worker_id, name)
    print(f"Worker '{worker_id}' ({name}) added.")


def remove_worker_flow(state):
    worker_id = input("Worker ID to remove: ").strip()
    wh.remove_worker(state, worker_id)
    print(f"Worker '{worker_id}' removed.")


def define_product_flow(state):
    product_name = input("Product name: ").strip()
    steps = []
    print("Enter assembly steps (resource + quantity). Leave resource blank to finish.")
    while True:
        resource = input("  Step resource (blank to finish): ").strip()
        if not resource:
            break
        qty = read_int(f"  Quantity of '{resource}' needed for this step: ")
        steps.append((resource, qty))
    wh.define_product(state, product_name, steps)
    print(f"Product '{product_name}' defined with {len(steps)} step(s).")


def create_task_flow(state):
    product_name = input("Product to assemble: ").strip()
    task_id = wh.create_task(state, product_name)
    print(f"Task '{task_id}' created for product '{product_name}'.")


def assign_task_flow(state):
    task_id = input("Task ID to assign: ").strip()
    robot_id = input("Robot ID (blank for none): ").strip() or None
    worker_id = input("Worker ID (blank for none): ").strip() or None
    wh.assign_task(state, task_id, robot_id, worker_id)
    print(f"Task '{task_id}' assigned and now in progress.")


def advance_task_flow(state):
    task_id = input("Task ID to advance: ").strip()
    status = wh.advance_task(state, task_id)
    progress = wh.get_task_progress(state, task_id)
    print(f"Task '{task_id}' advanced. Progress: {progress}. Status: {status}")


def cancel_task_flow(state):
    task_id = input("Task ID to cancel: ").strip()
    wh.cancel_task(state, task_id)
    print(f"Task '{task_id}' cancelled.")


def view_tasks_flow(state):
    tasks = state["tasks"]
    if not tasks:
        print("No tasks yet.")
        return
    for task_id, task in tasks.items():
        progress = wh.get_task_progress(state, task_id)
        print(f"  {task_id}: {task['product']} | Status: {task['status']} | "
              f"Progress: {progress} | Robot: {task['robot_id']} | Worker: {task['worker_id']}")


def main():
    state = wh.new_warehouse_state()
    print("=== Automated Warehouse Management System ===")

    actions = {
        "1": add_resource_flow,
        "2": view_inventory_flow,
        "3": add_robot_flow,
        "4": remove_robot_flow,
        "5": add_worker_flow,
        "6": remove_worker_flow,
        "7": define_product_flow,
        "8": create_task_flow,
        "9": assign_task_flow,
        "10": advance_task_flow,
        "11": cancel_task_flow,
        "12": view_tasks_flow,
    }

    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        if choice == "0":
            print("Goodbye!")
            break

        action = actions.get(choice)
        if action is None:
            print("Invalid option, try again.")
            continue

        try:
            action(state)
        except WarehouseError as e:
            print(f"Error: {e}")
        except ValueError as e:
            print(f"Invalid input: {e}")


if __name__ == "__main__":
    main()
