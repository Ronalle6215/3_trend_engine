"""
Custom exceptions
"""


class TrendEngineError(Exception):
    pass


class CollectorError(TrendEngineError):
    pass


class ProcessingError(TrendEngineError):
    pass


class StorageError(TrendEngineError):
    pass


class ConfigError(TrendEngineError):
    pass
