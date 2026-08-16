from typing import Generic, TypeVar, List, Optional

from pydantic import BaseModel, ConfigDict

from app.services.models.taxonomy_dto import TaxonomyOut


class TaxonomyMapForm(BaseModel):
    id_taxonomy: int


class PageTaxonomyMoveForm(BaseModel):
    id_taxonomy_from: int | None = None


class AnswerMapForm(BaseModel):
    answer: str
    is_correct: bool


class DateForm(BaseModel):
    date_number: int
    date_text: str


class PageForm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_type: int
    id_sub_type: int
    title: str
    document: str | None
    document_json: dict | None = None
    description: str | None
    note: str | None

    taxonomies: list[TaxonomyMapForm] | None
    answers: list[AnswerMapForm] | None
    map_answers: list[AnswerMapForm] | None
    date: DateForm | None


class PageAnswerDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    id_answer: int
    answer: str
    is_correct: bool | None = None


class MapPageTaxonomyDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_taxonomy: int
    order_no: int | None = None
    taxonomy: TaxonomyOut


class PageMediaDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    id_page: int
    id_media: int
    name: str
    path: str
    mime_type: str


class DateDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date_number: int
    date_text: str


class PageDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    id_author: int | None = None
    id_type: int
    id_sub_type: int
    order_no: int | None = None
    title: str
    document: str | None = None
    document_json: dict | None = None
    description: str | None = None
    note: str | None = None
    taxonomies: List[MapPageTaxonomyDTO] = []
    answers: List[PageAnswerDTO] = []
    media: List[PageMediaDTO] = []
    date: Optional[DateDTO] = None


T = TypeVar('T')


class PagedResult(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total_number: int
