"""M3 normalization, translation, canonical assembly, and data contract export."""

from .assemble import assemble_batch, assemble_course
from .normalize import normalize_batch, normalize_record
from .translate import translate_batch, translate_entity
from .translate_ctdt import (
    apply_translations,
    collect_unique_strings,
    translate_ctdt_batch,
)
from .export_for_skill_mapping import export_single_course, export_batch

__all__ = [
    "assemble_batch",
    "assemble_course",
    "normalize_batch",
    "normalize_record",
    "translate_batch",
    "translate_entity",
    # CTDT translation (Luồng B)
    "translate_ctdt_batch",
    "collect_unique_strings",
    "apply_translations",
    # Data contract export (cho esco-skill-mapping)
    "export_single_course",
    "export_batch",
]
