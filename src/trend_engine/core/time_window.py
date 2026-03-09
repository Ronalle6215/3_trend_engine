"""
Time window helpers
"""

SUPPORTED_WINDOWS = {"6h", "24h", "72h"}


def validate_time_window(window: str) -> str:
    if window not in SUPPORTED_WINDOWS:
        raise ValueError(f"Unsupported time window: {window}")
    return window
