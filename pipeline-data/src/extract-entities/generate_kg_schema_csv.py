import pandas as pd
import json
import os
from pathlib import Path

def generate_schema_csv():
    # Define the output path
    output_dir = Path(r"d:\NCKH_2026\src\pipeline-data\src\extract-entities")
    output_path = output_dir / "updated_kg_schema.csv"
    
    # 1. NODES
    nodes = [
        {"Type": "NODE", "Name (Label)": "ChuongTrinhDaoTao", "Description": "Chương trình đào tạo", "Properties": "ma_ctdt, ten_ctdt, bac_dao_tao, phien_ban", "Source": "GĐ1 — Trích xuất & chuẩn hóa"},
        {"Type": "NODE", "Name (Label)": "NhomHocPhan", "Description": "Nhóm học phần bắt buộc / tự chọn", "Properties": "group_id, ten_nhom, loai_nhom, so_tin_chi_yeu_cau", "Source": "GĐ1 — Trích xuất & chuẩn hóa"},
        {"Type": "NODE", "Name (Label)": "HocPhan", "Description": "Một môn học", "Properties": "ma_hoc_phan, ten_vi, ten_en, so_tin_chi_tong, tin_chi_ly_thuyet, tin_chi_thuc_hanh_thi_nghiem, tin_chi_tieu_luan, tin_chi_bai_tap_lon, tin_chi_do_an_mon_hoc, tin_chi_thuc_tap, mo_ta_tom_tat, hoc_ky_goi_y, loai_hoc_phan, source_file, source_pages", "Source": "GĐ1 — Trích xuất & chuẩn hóa"},
        {"Type": "NODE", "Name (Label)": "MucTieuHocPhan", "Description": "Mục tiêu học phần (kiến thức/kỹ năng/tự chủ)", "Properties": "mucTieu_id, loai_muc_tieu, ma_muc_tieu, noi_dung, so_ctdt[], source_page", "Source": "GĐ1 — Trích xuất & chuẩn hóa"},
        {"Type": "NODE", "Name (Label)": "CLO", "Description": "Chuẩn đầu ra của học phần", "Properties": "clo_id, ma_cdr_goc, noi_dung, pi_so[], muc_do[], source_page", "Source": "GĐ1 — Trích xuất & chuẩn hóa"},
        {"Type": "NODE", "Name (Label)": "Bai", "Description": "Bài học / nội dung dạy-học chi tiết", "Properties": "lesson_id, so_thu_tu, ten_bai, noi_dung_tom_tat, gio_truc_tiep, gio_truc_tuyen, gio_tu_hoc, hinh_thuc_day_hoc[], source_page", "Source": "GĐ1 — Trích xuất & chuẩn hóa"},
        {"Type": "NODE", "Name (Label)": "KyNangESCO", "Description": "Kỹ năng chuẩn ESCO", "Properties": "skill_uri (khóa), preferred_label, alternative_labels[], description, skill_type, broader_skill_uri, status", "Source": "GĐ2 — Dữ liệu ESCO"},
        {"Type": "NODE", "Name (Label)": "NgheNghiepESCO", "Description": "Nghề nghiệp chuẩn ESCO", "Properties": "occupation_uri (khóa), preferred_label, alternative_labels[], description", "Source": "GĐ2 — Dữ liệu ESCO"},
        # NEW NODE
        {"Type": "NODE", "Name (Label)": "ConceptTag", "Description": "Các cụm từ khóa, khái niệm kỹ thuật hoặc kỹ năng mềm rút trích từ đề cương", "Properties": "normalized (khóa), text, loai", "Source": "GĐ3 — Nhánh M4 & M5"},
    ]
    
    # 2. RELATIONSHIPS
    relationships = [
        {"Type": "RELATIONSHIP", "Name (Label)": "(ChuongTrinhDaoTao)-[:CO_HOC_PHAN]->(HocPhan)", "Description": "CTĐT có học phần", "Properties": "", "Source": "GĐ1"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:THUOC_NHOM]->(NhomHocPhan)", "Description": "Học phần thuộc nhóm", "Properties": "", "Source": "GĐ1"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:CO_CLO]->(CLO)", "Description": "Học phần có CLO", "Properties": "", "Source": "GĐ1"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:CO_MUC_TIEU]->(MucTieuHocPhan)", "Description": "Học phần có mục tiêu", "Properties": "", "Source": "GĐ1"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:CO_BAI]->(Bai)", "Description": "Học phần có bài học", "Properties": "", "Source": "GĐ1"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(Bai)-[:HO_TRO_CLO]->(CLO)", "Description": "Bài học góp phần đạt CLO", "Properties": "", "Source": "GĐ1"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:TIEN_QUYET]->(HocPhan)", "Description": "Học phần tiên quyết", "Properties": "is_explicitly_empty, source", "Source": "GĐ1"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:HOC_TRUOC]->(HocPhan)", "Description": "Học phần học trước", "Properties": "is_explicitly_empty, source", "Source": "GĐ1"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:SONG_HANH]->(HocPhan)", "Description": "Học phần song hành", "Properties": "confidence, method", "Source": "BƯỚC HOÀN THIỆN KG"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:TUONG_DUONG]->(HocPhan)", "Description": "Học phần tương đương", "Properties": "confidence, method", "Source": "BƯỚC HOÀN THIỆN KG"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:BO_TRO]->(HocPhan)", "Description": "Học phần bổ trợ", "Properties": "confidence, method", "Source": "BƯỚC HOÀN THIỆN KG"},
        # UPDATED RELATIONSHIPS
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:TEACHES_SKILL]->(KyNangESCO)", "Description": "Học phần dạy kỹ năng", "Properties": "retrieval_score, rerank_score, validation_confidence, evidence_sources[], matched_mentions[], llm_reasoning", "Source": "GĐ3 — Nhánh M4"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:TEACHES_KNOWLEDGE]->(KyNangESCO)", "Description": "Học phần dạy kiến thức", "Properties": "retrieval_score, rerank_score, validation_confidence, evidence_sources[], matched_mentions[], llm_reasoning", "Source": "GĐ3 — Nhánh M4"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:SUPPORTS_SKILL]->(KyNangESCO)", "Description": "Học phần hỗ trợ kỹ năng", "Properties": "evidence_sources[], matched_mentions[], llm_reasoning, validation_confidence", "Source": "GĐ3 — Nhánh M5"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:SUPPORTS_KNOWLEDGE]->(KyNangESCO)", "Description": "Học phần hỗ trợ kiến thức", "Properties": "evidence_sources[], matched_mentions[], llm_reasoning, validation_confidence", "Source": "GĐ3 — Nhánh M5"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(NgheNghiepESCO)-[:REQUIRES_SKILL]->(KyNangESCO)", "Description": "Nghề nghiệp yêu cầu kỹ năng", "Properties": "importance_type", "Source": "GĐ2"},
        # NEW RELATIONSHIPS
        {"Type": "RELATIONSHIP", "Name (Label)": "(HocPhan)-[:HAS_CONCEPT]->(ConceptTag)", "Description": "Học phần bao hàm từ khóa/khái niệm", "Properties": "role (teach / support)", "Source": "GĐ3 — Nhánh M4 & M5"},
        {"Type": "RELATIONSHIP", "Name (Label)": "(ConceptTag)-[:EVIDENCE_FOR]->(KyNangESCO)", "Description": "Từ khóa làm bằng chứng cho ESCO skill", "Properties": "confidence, pipeline_source", "Source": "GĐ3 — Nhánh M4 & M5"},
    ]
    
    df = pd.DataFrame(nodes + relationships)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Successfully generated updated schema at: {output_path}")

if __name__ == "__main__":
    generate_schema_csv()
