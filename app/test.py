import collections
import html
import re
from multiprocessing import Pool
from random import shuffle
from typing import List

import morfeusz2
import tqdm
from fuzzysearch import find_near_matches
from sqlalchemy.orm import Session

from app.constants import PageTypes
from app.database import models
from app.database.database import get_db


def cleaner(text):
    if text is None:
        return ''

    if not isinstance(text, str):
        return ''

    text = html.unescape(text).upper()

    tags = re.compile(r'(\[.*?])', flags=re.MULTILINE | re.IGNORECASE)
    html_tags = re.compile(r'(<.*?>)', flags=re.MULTILINE | re.IGNORECASE)
    non_letters = re.compile(r'[\s\.\,\!\@\#\$\%\^\&\*\(\)\-\=\_\+\[\]\;\'\:\"\<\> \\\/]+',
                             flags=re.MULTILINE | re.IGNORECASE)

    compiles = [tags, html_tags]
    for comp in compiles:
        text = comp.sub(' ', text)

    words = non_letters.split(text)

    return ' '.join(words).lower()


def multi_run_wrapper(args):
    return process(*args)


def process(page: models.Page, tags: List[str]):
    finds_in_page = []
    if page.document is not None:
        clean = cleaner(' '.join([page.document, page.title]))
        for tag in tags:
            max_distance = round(len(tag) / 5 - 1.0)
            max_distance = 0 if max_distance < 0 else max_distance
            finds = find_near_matches(tag, clean, max_l_dist=max_distance, max_deletions=0)
            if len(finds) > 0:
                finds_in_page.append(tag)
    return finds_in_page


class TextAnalyzer:

    def __init__(self):
        self.tags = []
        self.session: Session = next(get_db())
        self.morf = morfeusz2.Morfeusz()

        # with open('stopwords.txt', encoding='utf8') as file:
        #     self.stop_words = [word.strip() for word in file.readlines()]

    def run(self):
        pages = self.session.query(models.Page).all()

        tags = []
        for page in pages:
            if page.id_type in [PageTypes.CharacterPage, PageTypes.DictionaryPage]:
                tags.append(cleaner(page.title))

        shuffle(tags)
        self.tags = tags

        pool = Pool(12)

        items = []
        for page in pages:
            items.append((page, self.tags.copy()))
            # multi_run_wrapper((page, self.tags))
        results = []
        for res in tqdm.tqdm(pool.imap(multi_run_wrapper, items), total=len(items)):
            results.extend(set(res))

        pool.close()
        pool.join()
        print('done')
        length_count = collections.Counter(results)

        for word, count in length_count.most_common(200):
            print(f'{count}: {word}')


if __name__ == '__main__':
    analyzer = TextAnalyzer()
    analyzer.run()
