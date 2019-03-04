from abc import ABC
import definitions
import os
from whoosh.analysis import tokenizers, analyzers
from whoosh.analysis import LowercaseFilter, StopFilter, StemFilter
from whoosh.query import Query
from whoosh.query import Every
from whoosh import qparser
from whoosh.index import Index
from Indexing.Indexer import Indexer
import regex as re

STOP_WORDS = list()
with open(os.path.join(definitions.MAIN_PATH, "Indexing", "STOP_WORDS_DE.txt"), encoding="utf-8") as f:
    for line in f.readlines():
        STOP_WORDS.append(line.strip())

with open(os.path.join(definitions.MAIN_PATH, "Indexing", "STOP_WORDS_EN.txt"), encoding="utf-8") as f:
    for line in f.readlines():
        STOP_WORDS.append(line.strip())


# Tokenization
class RegexTokenizer(tokenizers.RegexTokenizer):
    def __init__(self):
        super(RegexTokenizer, self).__init__()
        self.expression = re.compile(r"\p{L}{2,}", re.UNICODE)


def ImprovedTokenizer():
    chain = RegexTokenizer() | LowercaseFilter() | \
            StopFilter(stoplist=STOP_WORDS, minsize=2)
    return chain


class Analyzer:
    def __init__(self, search_term: str, indexer: Indexer):
        self.search_term = search_term
        self.ix: Index = indexer.ix
        self.schema = indexer.schema

    def skill_frquency_in_index(self) -> list:
        with self.ix.reader() as r:
            return (r.most_frequent_terms("skills", 20))

    def task_frequency_in_index(self) -> list:
        task_search_string = \
             "abwechslungsreich~2 ambitious~ anforderunge~ anforderungsprofil~/7 arbeitsbeginn~ arbeitsklima~/5 " \
             "arbeitsumfeld~/5 arbeitsumgebung~/5 assume aufgabenbereich~ aufgabenfeld~/5 aufgabengebiet~/5 " \
             "aufgabenschwerpunkte~/5 ausmacht~ begeister~2 beinhaltet~ bereich~3/5 beweist~2/5"

        or_group = qparser.OrGroup.factory(0.9)
        parser = qparser.QueryParser("paragraph_heading", schema=self.schema, group=or_group)
        parser.add_plugin(qparser.FuzzyTermPlugin())

        with self.ix.searcher() as r:
            for hit in r.search(parser.parse(task_search_string), limit=None):
                print(hit["paragraph_heading"])

            # headings_query = qparser.QueryParser()

            # frequenz von termen in den dazugehörigen content blocks

        benefits_search_string = "ambitious~ angebot~ ausmacht~ beinhaltet~ bekomm~2 benefit~ bereich~2/5"