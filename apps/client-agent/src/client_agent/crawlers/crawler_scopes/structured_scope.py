# structured_scope.py
from dataclasses import dataclass
from .base_scope import BaseScope

@dataclass
class StructuredScope(BaseScope):
    """
    Scope definition for structured data crawlers.

    This class extends the BaseScope to include parameters specific to structured data sources, such as relational databases. It can be used to specify
    which tables, columns, or schemas to include or exclude during the crawling process, as well as other relevant parameters for structured data crawling.
    
    defaults:
    - include_patterns: None (include all)
    - exclude_patterns: None (exclude none)
    - max_depth: None (no limit)
    - max_rows: None (no limit)
    - timeout: None (no limit)
    - linked_servers: None (do not include linked servers)
    """

    include_patterns: list[str] | None
    exclude_patterns: list[str] | None
    max_depth: int | None 
    max_rows: int | None 
    timeout: int | None
    linked_servers: list[str] | None


    def _validate(self) -> bool:
        """Validate the scope parameters to ensure they are well-defined and actionable."""
       
        if self.max_depth is None or self.max_depth > 0:
            return True
        if self.max_rows is None or self.max_rows > 0:
            return True
        if self.timeout is None or self.timeout > 0:
            return True
        if self.include_patterns is None or len(self.include_patterns) > 0:
            return True
        if self.exclude_patterns is None or len(self.exclude_patterns) > 0:
            return True
        if self.linked_servers is None or len(self.linked_servers) > 0:
            return True
        return False