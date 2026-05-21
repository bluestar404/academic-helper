"""
Immutable exam-paper domain models (single source of truth).

Models are frozen after construction; use model_copy(update={...}) to revise data.
All user-facing text fields are sanitized before validation via SanitizedStr.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)

from core.sanitizer import sanitize_optional, sanitize_text

PositiveMarks = Annotated[int, Field(gt=0)]


def _sanitize_str(value: str) -> str:
    return sanitize_text(value)


def _sanitize_optional_str(value: str | None) -> str | None:
    return sanitize_optional(value)


SanitizedStr = Annotated[str, BeforeValidator(_sanitize_str)]
OptionalSanitizedStr = Annotated[str | None, BeforeValidator(_sanitize_optional_str)]

_FROZEN_CONFIG = ConfigDict(
    frozen=True,
    str_strip_whitespace=True,
    extra="forbid",
)


class SubQuestion(BaseModel):
    model_config = _FROZEN_CONFIG

    label: str = Field(min_length=1)
    text: SanitizedStr
    marks: PositiveMarks


class Question(BaseModel):
    model_config = _FROZEN_CONFIG

    number: int = Field(ge=1)
    text: SanitizedStr
    marks: PositiveMarks
    sub_questions: list[SubQuestion] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_sub_question_marks(self) -> Question:
        if not self.sub_questions:
            return self
        sub_total = sum(sq.marks for sq in self.sub_questions)
        if self.marks != sub_total:
            raise ValueError(
                f"Question {self.number}: marks={self.marks} but "
                f"sub-questions sum to {sub_total}"
            )
        return self


class Section(BaseModel):
    model_config = _FROZEN_CONFIG

    code: str = Field(min_length=1)
    title: SanitizedStr
    instructions: OptionalSanitizedStr = None
    questions: list[Question] = Field(min_length=1)
    section_marks: PositiveMarks | None = None

    @model_validator(mode="after")
    def validate_section(self) -> Section:
        numbers = [q.number for q in self.questions]
        if len(numbers) != len(set(numbers)):
            raise ValueError(
                f"Section {self.code!r}: question numbers must be unique"
            )
        calculated = sum(q.marks for q in self.questions)
        if self.section_marks is not None and self.section_marks != calculated:
            raise ValueError(
                f"Section {self.code!r}: section_marks={self.section_marks} "
                f"but questions sum to {calculated}"
            )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def calculated_marks(self) -> int:
        return sum(q.marks for q in self.questions)


class ExamPaper(BaseModel):
    model_config = _FROZEN_CONFIG

    title: SanitizedStr
    subtitle: OptionalSanitizedStr = None
    institution: OptionalSanitizedStr = None
    sections: list[Section] = Field(min_length=1)
    duration_minutes: PositiveMarks | None = None
    total_marks: PositiveMarks
    paper_code: OptionalSanitizedStr = None
    exam_code: OptionalSanitizedStr = None
    time_display: OptionalSanitizedStr = None

    @model_validator(mode="after")
    def validate_exam_paper(self) -> ExamPaper:
        codes = [s.code for s in self.sections]
        if len(codes) != len(set(codes)):
            raise ValueError("Section codes must be unique")
        calculated = sum(s.calculated_marks for s in self.sections)
        if self.total_marks != calculated:
            raise ValueError(
                f"total_marks={self.total_marks} but sections sum to {calculated}"
            )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def calculated_total_marks(self) -> int:
        return sum(s.calculated_marks for s in self.sections)
