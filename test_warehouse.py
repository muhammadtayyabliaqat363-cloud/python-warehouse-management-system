"""
test_warehouse.py
-------------------
Unit tests for the warehouse management system, covering inventory,
robots, workers, product recipes, multi-step task assembly, and error
handling for invalid operations.

Run with:  python -m unittest test_warehouse.py -v
"""

import unittest

import warehouse as wh
from warehouse_exceptions import (
    ResourceNotFoundError,
    InsufficientStockError,
    RobotError,
    WorkerError,
    TaskError,
    ProductError,
)


class TestInventory(unittest.TestCase):

    def setUp(self):
        self.state = wh.new_warehouse_state()

    def test_add_resource_creates_entry(self):
        wh.add_resource(self.state, "wood", 10)
        self.assertEqual(self.state["inventory"]["wood"], 10)

    def test_add_resource_accumulates(self):
        wh.add_resource(self.state, "wood", 10)
        wh.add_resource(self.state, "wood", 5)
        self.assertEqual(self.state["inventory"]["wood"], 15)

    def test_add_resource_blank_name_raises(self):
        with self.assertRaises(ResourceNotFoundError):
            wh.add_resource(self.state, "", 5)

    def test_add_resource_zero_quantity_raises(self):
        with self.assertRaises(ValueError):
            wh.add_resource(self.state, "wood", 0)

    def test_remove_resource_reduces_stock(self):
        wh.add_resource(self.state, "wood", 10)
        wh.remove_resource(self.state, "wood", 4)
        self.assertEqual(self.state["inventory"]["wood"], 6)

    def test_remove_unknown_resource_raises(self):
        with self.assertRaises(ResourceNotFoundError):
            wh.remove_resource(self.state, "steel", 1)

    def test_remove_more_than_available_raises(self):
        wh.add_resource(self.state, "wood", 3)
        with self.assertRaises(InsufficientStockError):
            wh.remove_resource(self.state, "wood", 10)

    def test_inventory_report_sorted(self):
        wh.add_resource(self.state, "wood", 5)
        wh.add_resource(self.state, "bolts", 20)
        report = wh.get_inventory_report(self.state)
        self.assertEqual(report, [("bolts", 20), ("wood", 5)])


class TestRobots(unittest.TestCase):

    def setUp(self):
        self.state = wh.new_warehouse_state()

    def test_add_robot(self):
        wh.add_robot(self.state, "R1")
        self.assertEqual(self.state["robots"]["R1"]["status"], "idle")

    def test_add_duplicate_robot_raises(self):
        wh.add_robot(self.state, "R1")
        with self.assertRaises(RobotError):
            wh.add_robot(self.state, "R1")

    def test_remove_robot(self):
        wh.add_robot(self.state, "R1")
        wh.remove_robot(self.state, "R1")
        self.assertNotIn("R1", self.state["robots"])

    def test_remove_unknown_robot_raises(self):
        with self.assertRaises(RobotError):
            wh.remove_robot(self.state, "R99")

    def test_remove_busy_robot_raises(self):
        wh.add_robot(self.state, "R1")
        wh.define_product(self.state, "chair", [("wood", 4)])
        wh.add_resource(self.state, "wood", 10)
        task_id = wh.create_task(self.state, "chair")
        wh.assign_task(self.state, task_id, robot_id="R1")
        with self.assertRaises(RobotError):
            wh.remove_robot(self.state, "R1")


class TestWorkers(unittest.TestCase):

    def setUp(self):
        self.state = wh.new_warehouse_state()

    def test_add_worker(self):
        wh.add_worker(self.state, "W1", "Alice")
        self.assertEqual(self.state["workers"]["W1"]["name"], "Alice")

    def test_add_worker_blank_name_raises(self):
        with self.assertRaises(WorkerError):
            wh.add_worker(self.state, "W1", "")

    def test_remove_busy_worker_raises(self):
        wh.add_worker(self.state, "W1", "Alice")
        wh.define_product(self.state, "chair", [("wood", 4)])
        wh.add_resource(self.state, "wood", 10)
        task_id = wh.create_task(self.state, "chair")
        wh.assign_task(self.state, task_id, worker_id="W1")
        with self.assertRaises(WorkerError):
            wh.remove_worker(self.state, "W1")


class TestProductsAndTasks(unittest.TestCase):

    def setUp(self):
        self.state = wh.new_warehouse_state()
        wh.add_resource(self.state, "wood", 20)
        wh.add_resource(self.state, "screws", 40)
        wh.add_robot(self.state, "R1")
        wh.add_worker(self.state, "W1", "Alice")
        # A 2-step product: uses wood, then screws
        wh.define_product(self.state, "chair", [("wood", 4), ("screws", 8)])

    def test_define_product_empty_steps_raises(self):
        with self.assertRaises(ProductError):
            wh.define_product(self.state, "table", [])

    def test_create_task_unknown_product_raises(self):
        with self.assertRaises(ProductError):
            wh.create_task(self.state, "sofa")

    def test_create_task_generates_unique_ids(self):
        t1 = wh.create_task(self.state, "chair")
        t2 = wh.create_task(self.state, "chair")
        self.assertNotEqual(t1, t2)

    def test_assign_task_requires_robot_or_worker(self):
        task_id = wh.create_task(self.state, "chair")
        with self.assertRaises(TaskError):
            wh.assign_task(self.state, task_id)

    def test_assign_task_marks_robot_busy(self):
        task_id = wh.create_task(self.state, "chair")
        wh.assign_task(self.state, task_id, robot_id="R1")
        self.assertEqual(self.state["robots"]["R1"]["status"], "busy")

    def test_assign_already_busy_robot_raises(self):
        t1 = wh.create_task(self.state, "chair")
        wh.assign_task(self.state, t1, robot_id="R1")
        t2 = wh.create_task(self.state, "chair")
        with self.assertRaises(RobotError):
            wh.assign_task(self.state, t2, robot_id="R1")

    def test_full_multi_step_assembly_completes_task(self):
        task_id = wh.create_task(self.state, "chair")
        wh.assign_task(self.state, task_id, robot_id="R1", worker_id="W1")

        status = wh.advance_task(self.state, task_id)  # step 1: consume wood
        self.assertEqual(status, "in_progress")
        self.assertEqual(self.state["inventory"]["wood"], 16)

        status = wh.advance_task(self.state, task_id)  # step 2: consume screws
        self.assertEqual(status, "completed")
        self.assertEqual(self.state["inventory"]["screws"], 32)

        # Robot and worker should be freed after completion
        self.assertEqual(self.state["robots"]["R1"]["status"], "idle")
        self.assertEqual(self.state["workers"]["W1"]["status"], "available")

    def test_advance_task_insufficient_stock_raises_and_does_not_advance(self):
        wh.remove_resource(self.state, "wood", 18)  # leave only 2, need 4
        task_id = wh.create_task(self.state, "chair")
        wh.assign_task(self.state, task_id, robot_id="R1")
        with self.assertRaises(InsufficientStockError):
            wh.advance_task(self.state, task_id)
        # current_step should NOT have advanced
        self.assertEqual(self.state["tasks"][task_id]["current_step"], 0)

    def test_advance_pending_task_raises(self):
        task_id = wh.create_task(self.state, "chair")  # never assigned
        with self.assertRaises(TaskError):
            wh.advance_task(self.state, task_id)

    def test_cancel_task_frees_assignees(self):
        task_id = wh.create_task(self.state, "chair")
        wh.assign_task(self.state, task_id, robot_id="R1", worker_id="W1")
        wh.cancel_task(self.state, task_id)
        self.assertEqual(self.state["robots"]["R1"]["status"], "idle")
        self.assertEqual(self.state["workers"]["W1"]["status"], "available")
        self.assertEqual(self.state["tasks"][task_id]["status"], "cancelled")

    def test_cancel_completed_task_raises(self):
        task_id = wh.create_task(self.state, "chair")
        wh.assign_task(self.state, task_id, robot_id="R1")
        wh.advance_task(self.state, task_id)
        wh.advance_task(self.state, task_id)  # now completed
        with self.assertRaises(TaskError):
            wh.cancel_task(self.state, task_id)

    def test_get_task_progress_format(self):
        task_id = wh.create_task(self.state, "chair")
        wh.assign_task(self.state, task_id, robot_id="R1")
        self.assertEqual(wh.get_task_progress(self.state, task_id), "0/2")
        wh.advance_task(self.state, task_id)
        self.assertEqual(wh.get_task_progress(self.state, task_id), "1/2")


if __name__ == "__main__":
    unittest.main()
