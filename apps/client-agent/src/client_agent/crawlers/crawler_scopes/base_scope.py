
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class BaseScope(ABC):
    """
    Base class for defining the scope of a crawler.

    The scope defines what data sources, tables, or other entities the crawler should target during its execution.
    It serves as a blueprint for specifying the boundaries of the crawling process and can be extended to include
    specific parameters relevant to different types of crawlers (e.g., structured, unstructured, semi-structured).
    """
    include_patterns: list[str] | None
    exclude_patterns: list[str] | None
    max_depth: int | None
    timeout: int | None


    @abstractmethod
    def _validate(self) -> bool:
        """Validate the scope parameters to ensure they are well-defined and actionable."""
        ...

    def __post_init__(self):
        """Post-initialization processing to validate the scope."""
        if not self._validate():
            raise ValueError("Invalid scope parameters provided.")