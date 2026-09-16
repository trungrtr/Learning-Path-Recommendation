from pipeline.m4_teaches_pipeline.course_type import classify_course_type


def test_course_type_uses_ctdt_sections():
    assert classify_course_type([{"nhom_id": "I_2_TCKHTN", "ma_phan": "I.2"}]) == "FOUNDATIONAL"
    assert classify_course_type([{"nhom_id": "II_2", "ma_phan": "II.2"}]) == "CORE"
    assert classify_course_type([{"nhom_id": "II_3_TCCSN", "ma_phan": "II.3"}]) == "SPECIALIZED"