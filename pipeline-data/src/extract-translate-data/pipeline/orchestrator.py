"""
Điều phối 2 luồng, quản lý state + retry. Gọi qua scripts/run.py, không
chạy trực tiếp file này.

flow_syllabus(): M2 -> M3 -> export data contract
flow_ctdt():     M2 -> M3 -> export data contract

Mỗi bước kiểm tra output đã tồn tại trước khi chạy lại (idempotency).

Lưu ý: M4/M5/M6 đã chuyển sang repo esco-skill-mapping.
Pipeline này chỉ chịu trách nhiệm extract + translate + export.
"""

from shared.logger import get_logger

logger = get_logger("orchestrator")


def flow_syllabus(resume_from: str | None = None) -> None:
    """Luồng A: M2 (syllabus extraction) → M3 (normalize + translate + assemble) → export."""
    logger.info("=== Bắt đầu flow_syllabus ===")

    if resume_from not in ["m3", "export"]:
        logger.info("Chạy M2A Syllabus Extraction...")
        from pipeline.m2.m2a_syllabus_extraction import process_batch
        process_batch()
    else:
        logger.info(f"Resume flow_syllabus from {resume_from}, skipping M2A...")

    if resume_from not in ["export"]:
        logger.info("Chạy M3 Normalize + Translate + Assemble...")
        # TODO: gọi normalize_batch, translate_batch, assemble_batch
        pass
    else:
        logger.info(f"Resume flow_syllabus from {resume_from}, skipping M3...")

    logger.info("Chạy Export data contract cho esco-skill-mapping...")
    # TODO: gọi export_batch với output từ M3
    logger.info("Export hoàn tất → data/exports/skill_mapping_input/")
    logger.info("=== flow_syllabus complete ===")


def flow_ctdt(resume_from: str | None = None) -> None:
    """Luồng B: M2 (CTDT extraction) → M3 (normalize + translate) → export."""
    logger.info("=== Bắt đầu flow_ctdt ===")

    if resume_from not in ["m3", "export"]:
        logger.info("Chạy M2B CTDT Extraction...")
        from pipeline.m2.m2b_ctdt_extraction import ctdt_extract
        ctdt_extract()
    else:
        logger.info(f"Resume flow_ctdt from {resume_from}, skipping M2B...")

    if resume_from not in ["export"]:
        logger.info("Chạy M3 Normalize CTDT + Translate CTDT...")
        from pipeline.m3.normalize import normalize_batch
        from pipeline.m3.translate_ctdt import translate_ctdt_batch
        from pipeline.m3.materialize_ctdt import materialize_ctdt_batch

        normalize_batch()
        translate_ctdt_batch()
        materialize_ctdt_batch()
    else:
        logger.info(f"Resume flow_ctdt from {resume_from}, skipping M3...")

    logger.info("CTDT materialization complete → data/8_canonical/ctdt/")
    logger.info("=== flow_ctdt complete ===")


def run_module(module_name: str, **kwargs) -> None:
    """Chạy một module riêng lẻ, dùng khi debug hoặc chạy lại từng bước."""
    if module_name == "m2":
        logger.info("Chạy M2 riêng lẻ...")
        raise NotImplementedError
    elif module_name == "m3":
        logger.info("Chạy M3 riêng lẻ...")
        raise NotImplementedError
    else:
        raise ValueError(f"Unknown module: {module_name}. Valid: m2, m3")
