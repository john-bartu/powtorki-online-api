import io
import os
import random
from concurrent.futures import ThreadPoolExecutor
from typing import Type

import mammoth as mammoth
import pandas as pd
from PIL import Image
from fastapi import UploadFile
from pdf2image import convert_from_bytes
from sqlalchemy.orm import Session

from app.database import models

IMAGES_PATH = './images-to-upload/'


def get_random_string(length):
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"
    return ''.join(random.choice(letters) for _ in range(length))


def convert_image(image):
    if not os.path.isdir(IMAGES_PATH):
        os.makedirs(IMAGES_PATH)

    with image.open() as image_bytes:

        name = get_random_string(10)

        im = Image.open(image_bytes)
        if im.mode == 'CMYK':
            im = image.convert('RGB')
        im.save(f"./{IMAGES_PATH}/{name}.png", "PNG")

        encoded_src = f"https://media.powtorkionline.pl/media-upload/{name}.png"

    return {
        "src": encoded_src
    }


def process_documents(model: Type[models.Page], files: list[UploadFile]) -> list[models.Page]:
    pages = []
    for file in files:
        filename = os.path.splitext(file.filename)[0]
        print(f"Processing {filename}")
        if not (file.filename.endswith('.docx')):
            raise TypeError(f"Unsupported document type of file: {file.filename}")

        file_bytes = io.BytesIO(file.file.read())
        conversion = mammoth.convert_to_html(file_bytes, convert_image=mammoth.images.img_element(convert_image))

        new_page = model()
        new_page.title = filename
        new_page.document = conversion.value
        pages.append(new_page)

    return pages


def process_single_pdf(model: Type[models.Page], file: UploadFile) -> models.Page:
    filename = os.path.splitext(file.filename)[0]
    print(f"Processing {filename}")
    if not (file.filename.endswith('.pdf')):
        raise TypeError(f"Unsupported document type of file: {file.filename}")

    pdf_pages = convert_from_bytes(file.file.read(), dpi=300)  # to trwa 10 sek
    document = ""
    for pdf_page in pdf_pages:
        image_name = get_random_string(10)
        document += f"<img src='https://media.powtorkionline.pl/media-upload/{image_name}.png' />\n"
        pdf_page.save(os.path.join(IMAGES_PATH, f"{image_name}.png"), "PNG")

    new_page = model()
    new_page.title = filename
    new_page.document = document
    return new_page


def process_pdf(model: Type[models.Page], files: list[UploadFile]) -> list[models.Page]:
    results = []
    with ThreadPoolExecutor() as executor:
        futures = []
        for file in files:
            futures.append(executor.submit(process_single_pdf, model, file))

        for future in futures:
            results.append(future.result())
    return results


def process_qa(file: UploadFile):
    pages = []
    data = pd.read_excel(file.file.read(), header=None, names=["question", "answer"])
    for date, answer in data.iterrows():
        question = answer['question']
        answer = answer['answer']
        if not question or not answer:
            raise TypeError(f"Row bad format of file: {question} - {answer}")

        new_page = models.QAPage()
        new_page.title = question
        new_page.document = answer
        pages.append(new_page)
    return pages


def process_dictionary(file: UploadFile):
    pages = []
    data = pd.read_excel(file.file.read(), header=None, names=["name", "description"])
    for date, answer in data.iterrows():
        name = answer['name']
        description = answer['description']

        new_page = models.DictionaryPage()
        new_page.title = name
        new_page.document = description
        pages.append(new_page)
    return pages


def process_characters(file: UploadFile):
    pages = []
    data = pd.read_excel(file.file.read(), header=None, names=["name", "description"])
    for date, answer in data.iterrows():
        name = answer['name']
        description = answer['description']

        new_page = models.CharacterPage()
        new_page.title = name
        new_page.document = description
        pages.append(new_page)
    return pages


def process_dates(file: UploadFile, db: Session):
    pages = []
    data = pd.read_excel(file.file.read(), header=None, names=["date", "name"])
    for date, answer in data.iterrows():
        date = answer['date']
        name = answer['name']

        new_page = models.CalendarPage()
        new_page.title = name

        calendar = models.Date(date_text=date)
        new_page.date = calendar

        db.add(calendar)
        pages.append(new_page)
    return pages


def process_quiz(file: UploadFile, db: Session, taxonomy_parent: models.Taxonomy):
    pages = []
    data = pd.read_excel(file.file.read(), header=None,
                         names=["question", "answer_correct", "answer_1", "answer_2", "answer_3"])

    quiz_taxonomy = models.QuizTaxonomy(id_parent=taxonomy_parent.id, name=file.filename)
    db.add(quiz_taxonomy)

    for date, row in data.iterrows():
        question = row['question']
        text_answers = []

        if row['answer_correct']:
            text_answers.append(str(row['answer_correct']))
        if row['answer_1']:
            text_answers.append(str(row['answer_1']))
        if row['answer_2']:
            text_answers.append(str(row['answer_2']))

        if not question or len(text_answers) < 2:
            raise TypeError(f"Row bad format of file: {question} -  {text_answers}")

        new_page = models.QuizPage()
        new_page.title = question

        for index, text_answer in enumerate(text_answers):
            answer = models.Answer(answer=text_answer)
            map_answer = models.MapPageAnswer(answer=answer, is_correct=(index == 0))
            new_page.map_answers.append(map_answer)

            db.add(answer)
            db.add(map_answer)

        map_page_tax = models.MapPageTaxonomy()
        map_page_tax.taxonomy = quiz_taxonomy
        new_page.taxonomies.append(map_page_tax)
        db.add(new_page)
        db.add(map_page_tax)

    return pages
