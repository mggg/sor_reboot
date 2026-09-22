from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelFeature:
    """A declared feature of the dataset.

    Generic features (the default) are built by the generic loop: sum of the
    numerator columns over sum of the denominator columns (no denominator: the
    summed count passes through as-is).

    `custom=True` marks a feature the generic loop cannot express (a
    subtraction, a log ratio, a cross-source combination). The derive stage
    computes it with a dedicated function registered under `var_name`. Custom
    features declare no codes: their inputs are other declared columns of the
    merged frame, and any fetching those inputs need is declared where the
    inputs are.
    """

    source_table: str
    table_code: str | None
    var_name: str
    description: str
    numerator_codes: tuple[str, ...] = ()
    denominator_codes: tuple[str, ...] = ()
    custom: bool = False

    def __post_init__(self) -> None:
        if self.custom and (self.numerator_codes or self.denominator_codes):
            raise ValueError(
                f"{self.var_name}: a custom feature declares no codes -- its "
                "inputs are other declared columns"
            )
        if not self.custom and not self.numerator_codes:
            raise ValueError(
                f"{self.var_name}: a generic feature needs numerator codes "
                "(set custom=True if a dedicated function builds it)"
            )


def feature_codes(features: Iterable[ModelFeature]) -> list[str]:
    """Every distinct code the features touch, sorted for a stable fetch order.

    Deduplicates -- aggregate features share codes with per-code features, and
    denominators repeat across features of one table.
    """
    codes: set[str] = set()
    for feature in features:
        codes.update(feature.numerator_codes)
        codes.update(feature.denominator_codes)
    return sorted(codes)
