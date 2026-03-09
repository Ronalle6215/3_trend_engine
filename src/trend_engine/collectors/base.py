"""
Base interface for all signal collectors
"""

from abc import ABC, abstractmethod
from trend_engine.core.models import RawSignal


class BaseCollector(ABC):

    @abstractmethod
    def collect(self, window: str) -> RawSignal:
        """Collect raw signals for a given time window"""
        raise NotImplementedError
