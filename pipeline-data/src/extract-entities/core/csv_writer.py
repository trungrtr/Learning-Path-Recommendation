import csv
from pathlib import Path
from typing import List, Dict, Any
from .config import ARRAY_SEP

def format_value(val: Any) -> str:
    """Định dạng giá trị chuẩn Neo4j CSV: xử lý mảng, boolean, None."""
    if val is None:
        return ""
    if isinstance(val, list):
        # Nối list bằng dấu phân cách (thường là ;)
        return ARRAY_SEP.join([str(v).replace(ARRAY_SEP, ",") for v in val if v is not None])
    if isinstance(val, bool):
        return "true" if val else "false"
    return str(val).replace("\n", " ").replace("\r", " ").strip()

def write_nodes_csv(file_path: Path, nodes: List[Any]):
    """Ghi danh sách Dataclass Nodes ra CSV."""
    if not nodes:
        return
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Lấy keys từ phần tử đầu tiên
    fieldnames = list(nodes[0].__dict__.keys())
    
    # Tạo header đặc biệt cho neo4j-admin import nếu cần, tạm thời dùng raw fields
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        
        for node in nodes:
            row = {k: format_value(v) for k, v in node.__dict__.items()}
            writer.writerow(row)

def write_relationships_csv(file_path: Path, relationships: List['Relationship']):
    """Ghi danh sách Quan hệ ra CSV."""
    if not relationships:
        return
        
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Gom tất cả các keys từ properties để tạo dynamic header
    all_props_keys = set()
    for r in relationships:
        all_props_keys.update(r.properties.keys())
    
    # Default columns
    fieldnames = ["source_id", "target_id", "type"] + sorted(list(all_props_keys))
    
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        
        for r in relationships:
            row = {
                "source_id": format_value(r.source_id),
                "target_id": format_value(r.target_id),
                "type": format_value(r.type)
            }
            for pk in all_props_keys:
                row[pk] = format_value(r.properties.get(pk, ""))
            writer.writerow(row)
