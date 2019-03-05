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
             "alltag arbeitsgebiet~ are (aufgabe~ aufgabenbereich~ aufgabenbeschreibung aufgabenfeld " \
             "aufgabengebiet~ aufgabenschwerpunkt~ aufgabenspektrum)^2 bietest bist challenge chance dein~ dich" \
             "einsatz engagement^0.75 erwartet fachrichtung field (hauptaufgaben~2/12 haupttätigkeit~2/14)^2" \
             "herausforderung ihr~ machst meine perspective~2/6 (responsibilitie~2/15)^1.5 schwerpunkt~ sie " \
             "(task~/4)^3 themengebiet~2/12 tun umfasst unterstützen (verantwortlichkeit~2/18 verantwortung~2/13)^2" \
             "wirkungsfeld work workspace you~2/3"

        or_group = qparser.OrGroup.factory(0.9)
        parser = qparser.QueryParser("paragraph_heading", schema=self.schema, group=or_group)
        parser.add_plugin(qparser.FuzzyTermPlugin())

        with self.ix.searcher() as r:
            for hit in r.search(parser.parse(task_search_string), limit=None):
                print(hit["paragraph_heading"])

            # headings_query = qparser.QueryParser()

            # frequenz von termen in den dazugehörigen content blocks

        benefits_search_string = \
            "angebot are attraktiv (bekommen bekommst benefit~ bieten)^2 bringen~2/5 dein~ dich dir^1.5 freuen" \
            "geboten^1.5 ihnen ihr~ erwarten kannst konditionen leistungen mehrwert mein mitarbeitervorteile^3 " \
            "offer our^1.5 perks^2 salary sie ticken uns unser~/4 unternehmensprofil (vorteil~/7)^2 wir worauf freuen" \
            "you~2/3 zusatzleistungen^2 zusätzliche"

        requirements_search_string = \
            "(anforderung~2/5 anforderungsprofil)^2 anwenderkenntnisse~ are ausmacht auszeichnet background " \
            "bedingungen berufserfahrung~2 bietest bist bringen~2/5 dein du (einstellungsvoraussetzungen~2/25)^3 " \
            "(erfahrungen~2/9)^1.5 erforderlich~ erwarten (erwartungen~/5)^1.25 essential~ experiences~/7 fachgebiet" \
            "fachliche~/8 fachrichtung fähigkeiten^2 hast have ich ihr~ kannst kenntnisse~/8 (kompetenz~2/9)^2 " \
            "kompetenzprofil meine mitbringen mitbringst optimal~3/7 (pluspunkt~)^1.25 profil~2/4 punkten " \
            "(qualifications~2/13 qualifikation~2/13)^2 reference required requirements^2 sich skills^3 sollten" \
            "solltest steckbrief (stellenanforderung~2/18)^2 talent ticken (voraussetzung~2/13 vorkenntniss~2/12)^2" \
            "wonach worauf you~2/3 zusätzliche"