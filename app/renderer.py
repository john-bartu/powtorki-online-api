import re

from jinja2 import Template
from sqlalchemy.orm import Session

from app.database import models
from app.database.database import get_db

session: Session = next(get_db())

tables_mapping = {
    'word': models.DictionaryPage,
    'character': models.CharacterPage,
    'document': models.DocumentPage,
    'date': models.CalendarPage,
    'img': models.Media,
    'module': models.ChapterTaxonomy
}


def render_template(template, **context):
    jinja2_template_string = open("templates/" + template, 'r').read()
    template = Template(jinja2_template_string)
    html_template_string = template.render(context)
    return html_template_string


def filter_database(table_name, column_name, value):
    # print(table_name, column_name, value)

    if table_name == "img" and column_name == "id":
        column_name = "slug"

    filters = {column_name: value}

    table_class = tables_mapping.get(table_name, None)

    if table_class:
        query = session.query(table_class).filter_by(**filters).all()
        return query
    else:
        return []


def func(item):
    try:
        key, value = item.split('=')
        regex = re.findall(r'\"(.*?)\"', value)
        if len(regex) <= 0:
            regex = value

        value = regex[0]
        nothing, table, column = key.split(' ')
        res = filter_database(table, column, value)

        # print(res[0].format())
        if len(res) > 0:
            return res[0].format()
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


def page_renderer(content):
    pattern = r'\[(.*?)\]'
    resp = re.sub(pattern, lambda m: func(m.group(1)), content)
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
