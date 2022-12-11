import collections
import html
import math
import re
from multiprocessing import Pool
from random import shuffle
from typing import List

import pandas as pd
import tqdm
from fuzzysearch import find_near_matches
from sqlalchemy.orm import Session, joinedload, selectin_polymorphic

from app.constants import PageTypes, ActivitySettings
from app.database import models
from app.database.database import get_db
from app.helpers import get_descendants


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
        text = comp.sub('', text)

    text = non_letters.split(text)

    return ' '.join(text)


def multi_run_wrapper(args):
    return process(*args)


def process(page: models.Page, tags: List[str]):
    finds_in_page = []
    if page.document is not None:
        clean = cleaner(' '.join([page.document, page.title]))
        print(clean)
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


def sum_and_clip(x, min, max):
    value = sum(x)
    if value < min:
        return min
    elif value > max:
        return max
    else:
        return value


class ActivityAnalyser:
    def __init__(self):
        self.tags = []
        self.session: Session = next(get_db())
        self.taxonomy_branch_cache = {}
        self.taxonomies = self.load_taxonomy_dict()

    def load_taxonomy_dict(self):
        taxonomies = self.session.query(models.Taxonomy).all()
        res = {tax.id: tax for tax in taxonomies}
        return res

    def get_tax_branch(self, taxonomy_id):
        if taxonomy_id not in self.taxonomy_branch_cache:
            branch = get_descendants(self.session, [taxonomy_id])
            self.taxonomy_branch_cache[taxonomy_id] = branch
            return branch
        else:
            return self.taxonomy_branch_cache[taxonomy_id]

    def get_tax_pages(self, taxonomy_id, exclude_ids: List[int]):
        taxonomies = get_descendants(self.session, [taxonomy_id])
        query = (self.session.query(models.Page)  # noqa
        .join(models.Page.taxonomies)
        .options(
            selectin_polymorphic(models.Page, [models.DocumentPage, models.CalendarPage]),
            joinedload(models.Page.taxonomies))
        .filter(
            models.MapPageTaxonomy.id_taxonomy.in_(taxonomies),
            models.Page.id.notin_(exclude_ids)
        ))

        return query.all()

    def run(self, user_id, taxonomy_id=4):
        # query  activities for user
        activities = (self.session.query(models.UserActivity)
                      .options(joinedload(models.UserActivity.page).options(joinedload(models.Page.taxonomies)))
                      .filter(models.UserActivity.id_user == user_id)
                      .all())

        data = []
        for activity in activities:
            data.append([activity.id, activity.knowledge, activity.id_page, [tax.id_taxonomy for tax in activity.page.taxonomies]])

        df = pd.DataFrame(data, columns=['id', 'knowledge', 'page_id', 'taxonomy_ids'])
        print(df)

        # get whole branch for each page
        for index, line in df.iterrows():
            branch = []
            for tax in line['taxonomy_ids']:
                branch.extend(self.get_tax_branch(tax))
            df.at[index, 'taxonomy_ids'] = {*branch}
        print(df)

        # filter only considered tax

        min_value = ActivitySettings.incorrect_answer * 3
        max_value = 2
        # sum knowledge value of pages
        # clip values
        dfg = df.groupby('page_id').agg({'knowledge': lambda x: sum_and_clip(x, min_value, max_value), 'taxonomy_ids': 'first'})
        df_pages = dfg.loc[[(taxonomy_id in x) for x in dfg['taxonomy_ids']]]

        print(dfg)

        taxonomy_knowledge = []
        for index, line in dfg.iterrows():
            for tax_id in line['taxonomy_ids']:
                taxonomy_knowledge.append([tax_id, line['knowledge'], 1])

        df_taxonomy = pd.DataFrame(taxonomy_knowledge, columns=['taxonomy_id', 'knowledge', 'count'])
        dfg_taxonomy = df_taxonomy.groupby('taxonomy_id').agg({'knowledge': 'sum', 'count': 'count'})
        dfg_taxonomy['knowledge'] = dfg_taxonomy['knowledge'].apply(lambda x: math.log(math.fabs(x), 0.5) if x < 0 else x)
        dfg_taxonomy = dfg_taxonomy.sort_values(by=['knowledge'])

        # dfg_taxonomy.plot(x='taxonomy_id', y='knowledge')

        print(dfg_taxonomy)

        print('Worst knowledge by taxonomy:')
        for index, row in dfg_taxonomy.head(1).iterrows():
            worst_tax_id = index
            print(self.taxonomies[index].name, '\nknowledge:', row['knowledge'], f'\nhttp://192.168.0.45/1/{index}/pages\n')

        df_pages = df.loc[[(worst_tax_id in x) for x in df['taxonomy_ids']]]
        df_pages = df_pages.sort_values(by=['knowledge'])
        print('Worst knowledge by page:', df_pages)
        viewed_pages = df_pages['page_id'].tolist()
        tax_pages = list(self.get_tax_pages(worst_tax_id, viewed_pages))
        print('PageIds not viewed:\n', [page.id for page in tax_pages])


if __name__ == '__main__':
    # analyzer = TextAnalyzer()
    # analyzer.run()
    analyzer = ActivityAnalyser()
    analyzer.run(1)
