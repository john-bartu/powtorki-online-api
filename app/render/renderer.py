import io
import re

import matplotlib.pyplot as plt
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import DictionaryPage, CharacterPage, DocumentPage, CalendarPage, Media, ChapterTaxonomy, Page

session: Session = next(get_db())

tables_mapping = {
    'word': DictionaryPage,
    'character': CharacterPage,
    'document': DocumentPage,
    'date': CalendarPage,
    'img': Media,
    'module': ChapterTaxonomy
}


def find_image_slug(media_slug):
    return session.query(Media).filter(Media.slug == media_slug).all()


def find_page_id(page_id):
    return session.query(Page).filter(Page.id == page_id).all()


def find_page_title(page_name):
    return session.query(Page).filter(Page.title == page_name).all()


def func(item):
    try:
        key, value = item.split('=')
        regex = re.findall(r'\"(.*?)\"', value)
        regex2 = re.findall(r'([\da-zA-Z]+)', value)

        if len(regex) >= 0:
            regex = regex2

        if len(regex) <= 0:
            regex = value

        value = regex[0]
        _, knowledge_type, column = key.split(' ')

        print(f"Find: {knowledge_type}, with {column}={value}")

        if knowledge_type == 'img':
            res = find_image_slug(value)
        elif knowledge_type == 'date':
            # TODO: Support [date id=222]
            res = find_page_id(value)
            res = []
        elif knowledge_type == 'character':
            # TODO: Support [character name="Ludwik"]
            res = find_page_title(value)
            res = []
        else:
            res = []

        if len(res) > 0:
            try:
                return res[0].format()
            except:
                return None
        else:
            return None

    except ValueError:
        print(f"Err: {item}")
    except IndexError:
        print(f"Err: {item}")


def image_parser(something):
    return f"[ img id=\"{something}\" ]"


def symbol_parser(content):
    print(content)
    return content.replace("&rdquo;", '"')


def symbol_converter(content):
    return re.sub(r'(\[.*?\])', lambda m: symbol_parser(m.group(1)), content)


def image_converter(content):
    pattern = r'<img src="media-upload\/(.*?).png".*?>'
    result = re.sub(pattern, lambda m: image_parser(m.group(1)), content)
    return result


from matplotlib import numpy as np


def math_converter(formula):
    fontsize = 16
    dpi = 300

    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, r'${}$'.format(formula), fontsize=fontsize)


    output = io.StringIO()
    fig.savefig(output, dpi=dpi, transparent=True, format='svg', bbox_inches='tight', pad_inches=0.1)

    data = "".join(output.getvalue().split("\n")[3::])
    print(data)
    return data


def math_renderer(content):
    print("math check")
    resp = re.sub(r'\[m(.*?)\]', lambda m: math_converter(m.group(1)), content)
    return resp


def page_renderer(content):
    pattern = r'\[(.*?)\]'
    resp = math_renderer(content)
    resp = re.sub(pattern, lambda m: func(m.group(1)), resp)
    return resp

# if __name__ == "__main__":
#
#     # for image in session.query(HisImage).all():
#     #     image.source = f"https://historia.powtorkionline.pl/media-upload/{image.id_str}.png"
#     #     session.commit()
#     # session.flush()
#
#     first_time = True
#     while 1:
#         pages = session.query(HisPage).all()
#
#         count = len(pages)
#         i = 0
#
#         with alive_bar(count, enrich_print=False) as bar:
#
#             for page in pages:
#
#                 if (page.time_edited > page.time_rendered or first_time):
#                     doc_generated = page.document
#                     # doc_generated = image_converter(doc_generated)
#                     # doc_generated = symbol_parser(doc_generated)
#
#                     # page.document = doc_generated
#                     page.document_rendered = document_converter(
#                         doc_generated).rstrip()
#
#                     page.time_rendered = datetime.now()
#
#                     # print(page.document_rendered)
#                     i = i + 1
#                     print(f"PAGE [{page.id}] has been generated.")
#                     session.commit()
#                     session.flush()
#
#                 # else:
#                 # print(f'PAGE [{page.id}] was already rendered skipping...')
#                 bar()
#
#         session.commit()
#         session.flush()
#         print("Done")
#         first_time = False
#         time.sleep(5)
