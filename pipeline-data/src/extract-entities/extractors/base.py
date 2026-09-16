import abc
from typing import Dict, List, Any
from core.models import Relationship

class BaseExtractor(abc.ABC):
    @abc.abstractmethod
    def extract_nodes(self) -> Dict[str, List[Any]]:
        """
        Trích xuất và trả về dictionary:
        key: Tên loại Node (dùng làm tên file CSV, VD: 'HocPhan')
        value: List các object (VD: list[HocPhanNode])
        """
        pass

    @abc.abstractmethod
    def extract_relationships(self) -> Dict[str, List[Relationship]]:
        """
        Trích xuất và trả về dictionary:
        key: Tên loại Relationship (dùng làm tên file CSV, VD: 'CO_HOC_PHAN')
        value: List[Relationship]
        """
        pass
