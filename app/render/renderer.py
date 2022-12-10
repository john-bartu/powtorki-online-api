import io
import re

import html
import matplotlib.pyplot as plt
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import DictionaryPage, CharacterPage, DocumentPage, CalendarPage, Media, ChapterTaxonomy, Page

tables_mapping = {
    'word': DictionaryPage,
    'character': CharacterPage,
    'document': DocumentPage,
    'date': CalendarPage,
    'img': Media,
    'module': ChapterTaxonomy
}


class PageRenderer:

    def __init__(self):
        self.session: Session = next(get_db())

    def find_image_slug(self, media_slug):
        return self.session.query(Media).filter(Media.slug == media_slug).all()

    def find_page_id(self, page_id):
        return self.session.query(Page).filter(Page.id == page_id).all()

    def find_page_title(self, page_name):
        return self.session.query(Page).filter(Page.title == page_name).all()

    def func(self, item):
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
                res = self.find_image_slug(value)
            elif knowledge_type == 'date':
                # TODO: Support [date id=222]
                res = self.find_page_id(value)
                res = []
            elif knowledge_type == 'character':
                # TODO: Support [character name="Ludwik"]
                res = self.find_page_title(value)
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

    def image_parser(self, something):
        return f"[ img id=\"{something}\" ]"

    def symbol_parser(self, content):
        print(content)
        return content.replace("&rdquo;", '"')

    def symbol_converter(self, content):
        return re.sub(r'(\[.*?\])', lambda m: self.symbol_parser(m.group(1)), content)

    def image_converter(self, content):
        pattern = r'<img src="media-upload\/(.*?).png".*?>'
        result = re.sub(pattern, lambda m: self.image_parser(m.group(1)), content)
        return result

    def math_converter(self, formula):
        formula = html.unescape(formula)
        fontsize = 16
        dpi = 150

        fig = plt.figure()
        fig.text(0, 0, r'{}'.format(formula), fontsize=fontsize)

        output = io.StringIO()
        fig.savefig(output, dpi=dpi, transparent=True, format='svg', bbox_inches='tight', pad_inches=0.1)
        plt.close()

        data = "".join(output.getvalue().split("\n")[3::])
        return data

    def math_renderer(self, content):
        content = re.sub(r'\[math\](.*?)\[\/math\]', lambda m: self.math_converter(m.group(1)), content)
        content = re.sub(r'\[m\](.*?)\[\/m\]', lambda m: self.math_converter(m.group(1)), content)
        return content

    def render(self, content):
        pattern = r'\[(.*?)\]'
        resp = self.math_renderer(content)
        resp = re.sub(pattern, lambda m: self.func(m.group(1)), resp)
        return resp.strip()

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
