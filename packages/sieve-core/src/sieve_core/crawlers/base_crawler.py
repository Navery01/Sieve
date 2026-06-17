from abc import ABC, abstractmethod

class BaseCrawler(ABC):
    """
    Root base class for all crawlers.

    Crawlers are responsible for orchestrating the entire data crawling process:
    connecting to the data source, enumerating structure, fetching raw data rows,
    and performing PII detection and analysis.  They leverage connectors for
    data access and may also utilize other components (e.g., PII detectors).
    """

    @abstractmethod
    async def crawl(self) -> None:
        """Execute the full crawling process."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Tear down any connections and release resources."""
        ...