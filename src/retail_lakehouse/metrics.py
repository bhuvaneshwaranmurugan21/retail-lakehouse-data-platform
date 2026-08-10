"""Pipeline batch metrics and reconciliation checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class BatchMetrics:
    input_rows: int
    valid_rows_before_deduplication: int
    published_rows: int
    quarantined_rows: int
    duplicate_rows: int

    @property
    def reconciled(self) -> bool:
        return self.input_rows == (
            self.published_rows + self.quarantined_rows + self.duplicate_rows
        )

    def as_dict(self) -> dict[str, int | bool]:
        return {**asdict(self), "reconciled": self.reconciled}


def build_batch_metrics(
    input_rows: int,
    valid_rows_before_deduplication: int,
    published_rows: int,
    quarantined_rows: int,
) -> BatchMetrics:
    metrics = BatchMetrics(
        input_rows=input_rows,
        valid_rows_before_deduplication=valid_rows_before_deduplication,
        published_rows=published_rows,
        quarantined_rows=quarantined_rows,
        duplicate_rows=valid_rows_before_deduplication - published_rows,
    )
    if not metrics.reconciled:
        raise RuntimeError(f"batch failed reconciliation: {metrics.as_dict()}")
    return metrics

