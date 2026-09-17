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
