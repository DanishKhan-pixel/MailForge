"""Unit tests for list partitioning batch processing utility."""

from __future__ import annotations

import pytest

from app.utils.batch_utils import chunk_list


def test_chunk_list_standard() -> None:
    items = [1, 2, 3, 4, 5]
    chunks = chunk_list(items, chunk_size=2)
    assert chunks == [[1, 2], [3, 4], [5]]


def test_chunk_list_exact_multiple() -> None:
    items = ["a", "b", "c", "d"]
    chunks = chunk_list(items, chunk_size=2)
    assert chunks == [["a", "b"], ["c", "d"]]


def test_chunk_list_empty() -> None:
    assert chunk_list([], chunk_size=3) == []


def test_chunk_list_invalid_size() -> None:
    with pytest.raises(ValueError):
        chunk_list([1, 2, 3], chunk_size=0)


def test_calculate_batch_count_standard() -> None:
    from app.utils.batch_utils import calculate_batch_count

    assert calculate_batch_count(10, 5) == 2
    assert calculate_batch_count(11, 5) == 3
    assert calculate_batch_count(0, 10) == 0
    assert calculate_batch_count(3, 10) == 1


def test_calculate_batch_count_errors() -> None:
    from app.utils.batch_utils import calculate_batch_count

    with pytest.raises(ValueError):
        calculate_batch_count(10, 0)

    with pytest.raises(ValueError):
        calculate_batch_count(-5, 10)

