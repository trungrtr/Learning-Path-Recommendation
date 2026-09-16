"""M2 extraction modules."""

from .m2a_syllabus_extraction import extract_single, process_batch
from .m2b_ctdt_extraction import ctdt_extract, parse_ctdt_markdown
from .m2c_mhtml_extract import mhtml_extract

__all__ = [
    "ctdt_extract",
    "extract_single",
    "mhtml_extract",
    "parse_ctdt_markdown",
    "process_batch",
]