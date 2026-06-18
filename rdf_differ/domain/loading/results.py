"""Result value objects returned by the loader (pure domain)."""

from pydantic import BaseModel, ConfigDict


class DeltaCounts(BaseModel):
    model_config = ConfigDict(frozen=True)

    insertions: int
    deletions: int


class LoadResult(BaseModel):
    """The machine-readable outcome of a load/diff run."""

    model_config = ConfigDict(frozen=True)

    dataset_id: str
    current_version: str
    delta_pairs: list[tuple[str, str]]
    counts: dict[str, DeltaCounts]
    validation: str = "passed"

    @staticmethod
    def pair_key(old: str, new: str) -> str:
        return f"{old}->{new}"
