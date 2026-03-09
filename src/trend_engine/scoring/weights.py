"""
Scoring weights — configurable weights for trend features
"""

DEFAULT_WEIGHTS: dict[str, float] = {
    "volume": 0.30,
    "diversity": 0.25,
    "mentions": 0.25,
    "recency": 0.20,
}


def get_weights(custom: dict[str, float] | None = None) -> dict[str, float]:
    """Return scoring weights, optionally overridden by custom values."""
    if custom:
        weights = DEFAULT_WEIGHTS.copy()
        weights.update(custom)
        return weights
    return DEFAULT_WEIGHTS.copy()
