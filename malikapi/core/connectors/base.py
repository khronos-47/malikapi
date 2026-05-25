from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

class BaseConnector(ABC):
    @abstractmethod
    def fetch_delta(self, table: str, columns: List[str], delta_column: str,
                    since_timestamp: Optional[datetime], schema: Optional[str] = None) -> List[dict]:
        pass

    @abstractmethod
    def upsert_rows(self, table: str, rows: List[dict], key_columns: List[str],
                    schema: Optional[str] = None) -> int:
        pass

    @abstractmethod
    def close(self):
        pass
