from typing import List

from pydantic import BaseModel


class TaxonomyMapForm(BaseModel):
    id_taxonomy: int


class AnswerMapForm(BaseModel):
    answer: str
    is_correct: bool


class DateForm(BaseModel):
    date_number: int
    date_text: str


class PageForm(BaseModel):
    class Config:
        orm_mode = True

    id_type: int
    id_sub_type: int
    title: str
    document: str | None
    description: str | None
    note: str | None

    taxonomies: List[TaxonomyMapForm] | None
    answers: List[AnswerMapForm] | None
    date: DateForm | None
