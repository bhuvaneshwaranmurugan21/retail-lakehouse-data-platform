from __future__ import annotations

import pytest

from retail_lakehouse.metrics import BatchMetrics, build_batch_metrics


def test_batch_metrics_reconcile_published_quarantine_and_duplicates() -> None:
    metrics = build_batch_metrics(
        input_rows=100,
        valid_rows_before_deduplication=96,
        published_rows=94,
        quarantined_rows=4,
    )

    assert metrics.duplicate_rows == 2
    assert metrics.reconciled is True


def test_invalid_reconciliation_is_visible() -> None:
    metrics = BatchMetrics(
        input_rows=100,
        valid_rows_before_deduplication=95,
        published_rows=94,
        quarantined_rows=4,
        duplicate_rows=1,
    )

    assert metrics.reconciled is False


def test_negative_duplicate_count_fails_reconciliation() -> None:
    with pytest.raises(RuntimeError, match="failed reconciliation"):
        build_batch_metrics(
            input_rows=100,
            valid_rows_before_deduplication=90,
            published_rows=91,
            quarantined_rows=9,
        )

