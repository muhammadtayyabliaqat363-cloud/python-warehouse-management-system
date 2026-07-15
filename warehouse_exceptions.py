"""
warehouse_exceptions.py
------------------------
Custom exceptions used throughout the warehouse management system to
give meaningful, specific error messages rather than generic ones.
"""


class WarehouseError(Exception):
    """Base exception for all warehouse-related errors."""
    pass


class ResourceNotFoundError(WarehouseError):
    """Raised when a requested inventory resource does not exist."""
    pass


class InsufficientStockError(WarehouseError):
    """Raised when there isn't enough stock of a resource to complete an action."""
    pass


class RobotError(WarehouseError):
    """Raised for invalid robot operations (not found, already busy, etc.)."""
    pass


class WorkerError(WarehouseError):
    """Raised for invalid worker operations (not found, already busy, etc.)."""
    pass


class TaskError(WarehouseError):
    """Raised for invalid task operations (not found, wrong status, etc.)."""
    pass


class ProductError(WarehouseError):
    """Raised when a product recipe is invalid or not found."""
    pass
