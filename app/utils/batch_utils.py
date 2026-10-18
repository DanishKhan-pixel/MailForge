"""Batch processing helper utilities."""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def chunk_list(items: list[T], chunk_size: int) -> list[list[T]]:
    """Partition a list into smaller chunks of specified maximum size.

    Args:
        items: List of elements to partition.
        chunk_size: Maximum size of each chunk. Must be at least 1.

    Returns:
        List of sub-lists (chunks).

    Raises:
        ValueError: If chunk_size is less than 1.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be greater than or equal to 1")

    if not items:
        return []

    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def calculate_batch_count(total_items: int, batch_size: int) -> int:
    """Calculate the total number of batches required for processing items.

    Args:
        total_items: Total count of items to partition. Must be non-negative.
        batch_size: Number of items per batch. Must be at least 1.

    Returns:
        Number of batches required (at least 0).

    Raises:
        ValueError: If batch_size is less than 1 or total_items is negative.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be greater than or equal to 1")
    if total_items < 0:
        raise ValueError("total_items cannot be negative")
    if total_items == 0:
        return 0

    import math

    return math.ceil(total_items / batch_size)

