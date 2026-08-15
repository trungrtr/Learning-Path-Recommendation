from pydantic import BaseModel, Field


class DescriptionBlock(BaseModel):
    """Mô tả học phần giữ nguyên ID để audit truy vết nguồn."""
    description_id: str | None = None
    course_ref_id: str | None = None
    text: str | None = None


class Layer3SkillDocument(BaseModel):
    course_id: str
    course_code: str | None = None
    internal_course_code: str | None = None
    name_vi: str | None = None
    name_en: str | None = None
    description: DescriptionBlock | None = Field(default=None, description="Mô tả học phần")
    clos: list[str] = Field(default_factory=list, description="Danh sách nội dung chuẩn đầu ra")
    chapters: list[str] = Field(default_factory=list, description="Danh sách tên các chương")
    lessons: list[str] = Field(default_factory=list, description="Danh sách tên các bài học")
    keyword_skills: list[str] = Field(default_factory=list, description="Skill phrase LLM tạo có bằng chứng trong đề cương")
