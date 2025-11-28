
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable
from .schemas import ModelInfo

class BaseProvider(ABC):
    """
    Abstract base class for providers that expose a "list models" API.
    """

    id: str  # short provider id, e.g. "openai"
    name: str  # human readable name

    def __init__(self, config) -> None:
        self.config = config

    @abstractmethod
    def list_models(self) -> Iterable[ModelInfo]:
        """
        Return an iterable of ModelInfo entries. Implementations should:
          - call the provider's list-models endpoint
          - map provider payload -> ModelInfo
        """
        raise NotImplementedError
