"""
Base storage interface
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseStore(ABC):

    @abstractmethod
    def save(self, data: Any, path: str):
        raise NotImplementedError

    @abstractmethod
    def load(self, path: str) -> Any:
        raise NotImplementedError
