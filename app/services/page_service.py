import logging
from random import shuffle

from sqlalchemy.orm import Session, joinedload, selectin_polymorphic

from app.auth.dependencies import TokenData
from app.constants import PageTypes, ActivitySettings, PageSubTypes
from app.database import models
from app.helpers import get_descendants, find_branch_conflict
from app.render.renderer import PageRenderer
from app.services.models.page_dto import PageForm, PagedResult, PageDTO
from app.services.taxonomy_service import TaxonomyService

logger = logging.getLogger(__name__)


class TaxonomyBranchConflictError(ValueError):
    pass


class CompareResult:
    def __init__(self, added, removed) -> None:
        self.added = added
        self.removed = removed
        super().__init__()

    def __repr__(self) -> str:
        return f"CompareResult(Added=[{self.added}], Removed=[{self.removed}])"


def compare_sets(old: set, new: set):
    new_set = set(new)
    old_set = set(old)
    inter = new_set & old_set
    return CompareResult(new_set - inter, old_set - inter)


def _strip_correct_answers(dto: PageDTO) -> None:
    """Quiz answers must not reveal is_correct outside admin (po-admin) requests."""
    for answer in dto.answers:
        answer.is_correct = None


class PageService:

    def __init__(self, db: Session, limit: int = 20, current_user: TokenData | None = None) -> None:
        self.db = db
        self.pagination_limit = limit
        self.current_user = current_user

        self.filter_taxonomies: list[int] = []
        self.filter_sub_types: list[int] = []
        self.filter_page_types: list[int] = []
        self.filter_name: str = ""
        self.render_enabled = True

    def _raise_if_branch_conflict(self, taxonomy_ids: list[int]):
        conflict = find_branch_conflict(self.db, taxonomy_ids)
        if conflict is None:
            return
        id_a, id_b = conflict
        names = dict(self.db.query(models.Taxonomy.id, models.Taxonomy.name)
                     .filter(models.Taxonomy.id.in_([id_a, id_b])).all())
        raise TaxonomyBranchConflictError(
            f"Strona jest już przypisana w tej samej gałęzi taksonomii: "
            f"\"{names.get(id_a, id_a)}\" i \"{names.get(id_b, id_b)}\"")

    def set_from_form(self, item: models.Page | models.QuizPage | models.CalendarPage, form: PageForm):
        item.title = form.title
        item.document = form.document
        item.note = form.note
        item.description = form.description
        item.id_type = form.id_type
        item.id_sub_type = form.id_sub_type
        # item.order_no = form.order_no

        current_taxonomy_ids = [tax.id_taxonomy for tax in item.taxonomies]
        form_taxonomy_ids = [tax.id_taxonomy for tax in form.taxonomies]

        self._raise_if_branch_conflict(form_taxonomy_ids)

        difference = compare_sets(set(current_taxonomy_ids), set(form_taxonomy_ids))

        for tax in [taxonomy for taxonomy in item.taxonomies if taxonomy.id_taxonomy in difference.removed]:
            self.db.delete(tax)

        for taxonomy_id in difference.added:
            item.taxonomies.append(models.MapPageTaxonomy(id_taxonomy=taxonomy_id))

        if item.id_type == PageTypes.QuizPage:
            current_answers = {(answer.answer.answer, answer.is_correct) for answer in item.map_answers}
            form_answers = {(answer.answer, answer.is_correct) for answer in form.answers}

            difference = compare_sets(current_answers, form_answers)

            for map_answer_to_remove in [map_answer for map_answer in item.map_answers
                                         if (map_answer.answer.answer, map_answer.is_correct) in difference.removed]:
                self.db.delete(map_answer_to_remove)

            for new_answer in difference.added:
                text, is_correct = new_answer
                answer_entry = models.Answer(answer=text)
                map_answer_entry = models.MapPageAnswer(answer=answer_entry, is_correct=is_correct)
                self.db.add(answer_entry)
                self.db.add(map_answer_entry)
                item.map_answers.append(map_answer_entry)

        if item.id_type == PageTypes.CalendarPage:
            if item.date is not None:
                item.date.date_number = form.date.date_number
                item.date.date_text = form.date.date_text
            else:
                new_date = models.Date(date_text=form.date.date_text, date_number=form.date.date_number)
                item.date = new_date
                self.db.add(new_date)

        return item

    def post_item(self, form):
        if form.id_type == PageTypes.QuizPage:
            item = models.QuizPage()
        elif form.id_type == PageTypes.CalendarPage:
            item = models.CalendarPage()
        else:
            item = models.Page()
        self.db.add(item)
        item = self.set_from_form(item, form)
        self.db.commit()
        return PageDTO.model_validate(item)

    def put_item(self, page_id: int, form):
        item = self._get_item(page_id)
        item = self.set_from_form(item, form)
        self.db.commit()
        return PageDTO.model_validate(item)

    def move_page_taxonomy(self, page_id: int, id_taxonomy_to: int, id_taxonomy_from: int | None) -> PageDTO:
        item = self._get_item(page_id)

        current_ids = [tax.id_taxonomy for tax in item.taxonomies]
        resulting_ids = [tid for tid in current_ids if tid != id_taxonomy_from]
        if id_taxonomy_to not in resulting_ids:
            resulting_ids.append(id_taxonomy_to)

        self._raise_if_branch_conflict(resulting_ids)

        if id_taxonomy_from is not None:
            for tax in [t for t in item.taxonomies if t.id_taxonomy == id_taxonomy_from]:
                self.db.delete(tax)

        if id_taxonomy_to not in current_ids:
            item.taxonomies.append(models.MapPageTaxonomy(id_taxonomy=id_taxonomy_to))

        self.db.commit()
        return PageDTO.model_validate(item)

    def delete_item(self, page_id: int):
        try:
            item = self._get_item(page_id)
            self.db.delete(item)
            self.db.commit()
            return True
        except Exception:
            logger.exception(f"Error deleting item {page_id}")
            return False

    def _get_item(self, page_id: int) -> models.Page:
        item = (self.db.query(models.Page)
                .options(
            selectin_polymorphic(models.Page, [models.QuizPage, models.DocumentPage, models.CalendarPage]),
            joinedload(models.QuizPage.answers)
            .load_only(models.PageAnswer.id, models.PageAnswer.id_answer, models.PageAnswer.answer,
                       models.PageAnswer.is_correct),
            joinedload(models.DocumentPage.media),
            joinedload(models.CalendarPage.date),
            joinedload(models.Page.taxonomies).joinedload(models.MapPageTaxonomy.taxonomy))
                .filter(models.Page.id == page_id).first())

        if not item:
            raise ValueError("Page not found")
        return item

    def get_item(self, page_id: int, include_correct_answers: bool = False) -> PageDTO:
        renderer = PageRenderer()

        item = self._get_item(page_id)

        if self.render_enabled:
            if self.current_user is not None:
                user_activity = models.UserActivity()
                user_activity.id_user = self.current_user.id
                user_activity.id_page = item.id
                user_activity.knowledge = ActivitySettings.page_read
                self.db.add(user_activity)
                self.db.commit()
            if item.document:
                item.document = renderer.render(item.document)

        dto = PageDTO.model_validate(item)
        if not include_correct_answers:
            _strip_correct_answers(dto)
        return dto

    def get_items(self, pagination_no: int = 1, include_correct_answers: bool = False) -> PagedResult[PageDTO]:
        if not pagination_no > 0:
            raise ValueError("Page cannot be less than 1")
        offset = pagination_no - 1

        query = (self.db.query(models.Page)  # noqa
        .join(models.Page.taxonomies)
        .join(models.CalendarPage.date, isouter=True)
        .join(models.QuizPage.answers, isouter=True)
        .options(
            selectin_polymorphic(models.Page, [models.QuizPage, models.DocumentPage, models.CalendarPage]),
            joinedload(models.QuizPage.answers)
            .load_only(models.PageAnswer.id, models.PageAnswer.id_answer, models.PageAnswer.answer),
            joinedload(models.DocumentPage.media),
            joinedload(models.CalendarPage.date),
            joinedload(models.Page.taxonomies)))

        filtered_taxonomy_ids: set[int] | None = None
        if len(self.filter_taxonomies) > 0:
            filtered_taxonomy_ids = set(get_descendants(self.db, [self.filter_taxonomies[0]]))
            query = query.filter(
                models.MapPageTaxonomy.id_taxonomy.in_(filtered_taxonomy_ids),
            )

        if len(self.filter_page_types) > 0:
            query = query.filter(models.Page.id_type.in_(self.filter_page_types))

        if len(self.filter_sub_types) > 0:
            query = query.filter(models.Page.id_sub_type.in_(self.filter_sub_types))

        if len(self.filter_name) > 0:
            query = query.filter(
                # or_(
                # models.Page.title.match(self.filter_name),
                models.Page.title.like(f'%{self.filter_name}%')
                # )
            )

        if len(self.filter_sub_types) == 1:
            page_type = self.filter_sub_types[0]
            if page_type == PageSubTypes.Date:
                query = query.order_by(models.Date.date_number)
            elif page_type == PageSubTypes.Character or page_type == PageSubTypes.Dictionary:
                query = query.order_by(models.Page.title)
            else:
                query = query.order_by(models.MapPageTaxonomy.order_no, models.Page.title)
        else:
            query = query.order_by(models.Page.title)

        query = query.distinct(models.Page.id).from_self()

        total_number = query.count()

        results = query.offset(self.pagination_limit * offset).limit(self.pagination_limit).all()
        for page in results:
            if page.id_type == PageTypes.QuizPage:
                shuffle(page.answers)

        tax_lister = TaxonomyService(self.db)
        for page in results:
            for tax_map in page.taxonomies:
                tax_map.taxonomy.path = tax_lister.get_taxonomy_tree(tax_map.taxonomy)[1:]

        dtos = [PageDTO.model_validate(page) for page in results]
        if not include_correct_answers:
            for dto in dtos:
                _strip_correct_answers(dto)
        if filtered_taxonomy_ids is not None:
            for dto in dtos:
                dto.taxonomies = [t for t in dto.taxonomies if t.id_taxonomy in filtered_taxonomy_ids]

        return PagedResult(items=dtos, total_number=total_number)
