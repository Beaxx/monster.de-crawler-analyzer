import definitions
import os
from whoosh.analysis import tokenizers
from whoosh.analysis import LowercaseFilter, StopFilter
from whoosh.searching import Results
from whoosh import qparser
from whoosh.index import Index
from Indexing.Indexer import Indexer
import regex as re


# Builds a joined stop word list from english and german words
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
    """
    Basiert auf dem whoosh RegexTokenizer. Dies ist nur ein Wrapper um die Funktionalität des Tokenizers
    """
    chain = RegexTokenizer() | LowercaseFilter() | StopFilter(stoplist=STOP_WORDS, minsize=2)
    return chain


class Analyzer:
    """
    Der Analyzer hält einen Index sowie das Indexschema und ist für die Informationretrieval Operationen auf dem Index
    verantwortlich
    """
    def __init__(self, search_term: str, indexer: Indexer):
        self.search_term = search_term
        self.ix: Index = indexer.ix
        self.schema = indexer.schema

    def skill_frquency_in_index(self) -> list:
        """
        Ermittelt die 50 häufigsten Skills in allen Dokumenten des Index
        :return: Eine Liste von Strings
        """
        try:
            reader = self.ix.reader()
            skills = reader.most_frequent_terms("skills", 100)
            return ["{0},{1}".format(x[1].decode(), int(x[0])) for x in skills]
        finally:
            reader.close()

    @staticmethod
    def text_term_frequency(docs: Results) -> list:
        """
        Ermittelt für eine gegebene Liste an Dokumenten (Results Objekt) die häufigsten Terme. Zurückgegeben werden
        (in Abhängigkeit der länge der Liste der gefunden Terme) die top 20%, wobei die 1% der häufigsten Terme
        herausgefiltert werden.
        :param docs: Zu durchsuchende Dokumente als Results Objekt
        :return: Liste aus Strings
        """

        # Filters stopwords and words shorter then 5 chars
        def word_filter(word: str) -> str:
            if word != "None" and word not in STOP_WORDS and len(word) > 5:
                return word

        terms = dict()
        for doc in docs:
            ranking_treshold = docs.score(int(len(docs)*0.50))
            if doc.score < ranking_treshold:
                break
            content = doc["paragraph_content"]
            for word in content.split(" "):
                word_filtered = word_filter(word)
                if word_filtered in terms:
                    terms[word_filtered] += 1
                else:
                    terms[word_filtered] = 1
        sorted_by_value = sorted(terms.items(), key=lambda kv: kv[1], reverse=True)
        return [(x[0], x[1]) for x in sorted_by_value[int(len(sorted_by_value)*0.01):int(len(sorted_by_value)*0.20)]]

    def rate_paragraphs(self):
        pass  # todo rate paragraphs

    def task_frequency_in_index(self) -> list:
        task_search_string = \
             "alltag arbeitsgebiet~ are bringen^(-0.5) (aufgabe~ aufgabenbereich~ aufgabenbeschreibung aufgabenfeld " \
             "aufgabengebiet~ aufgabenschwerpunkt~ aufgabenspektrum)^2 bietest challenge chance dein~ dich" \
             "einsatz engagement^0.75 erwartet field (hauptaufgaben~2/12 haupttätigkeit~2/14)^2" \
             "herausforderung ihr~ machst meine (responsibilitie~2/15)^1.5 schwerpunkt~ sie " \
             "(task~/4)^3 themengebiet~2/12 tun umfasst unterstützen (verantwortlichkeit~2/18 verantwortung~2/13)^2" \
             "wirkungsfeld work workspace you~2/3"

        or_group = qparser.OrGroup.factory(1)
        parser = qparser.QueryParser("paragraph_heading", schema=self.schema, group=or_group)
        parser.add_plugin(qparser.FuzzyTermPlugin())

        try:
            heading_searcher = self.ix.searcher()
            result_docs = heading_searcher.search(parser.parse(task_search_string), limit=None)
            return self.text_term_frequency(result_docs)
        except ZeroDivisionError:
            return str("Für diese Anfrage waren zu wenig Dokumente vorhanden")
        finally:
            self.ix.searcher().close()

    def benefits_frequency_in_index(self) -> list:
        benefits_search_string = \
            "angebot are attraktiv (bekommen bekommst benefit~ bieten)^2 dein~ dich dir^1.5 freuen" \
            "geboten^1.5 ihnen ihr~ erwarten kannst konditionen leistungen mehrwert mein mitarbeitervorteile^3 " \
            "offer our^1.5 perks^2 salary sie ticken uns unser~/4 unternehmensprofil (vorteil~/7)^2 wir worauf freuen" \
            "you~2/3 zusatzleistungen^2 zusätzliche perspective~2/6"

        or_group = qparser.OrGroup.factory(1)
        parser = qparser.QueryParser("paragraph_heading", schema=self.schema, group=or_group)
        parser.add_plugin(qparser.FuzzyTermPlugin())

        try:
            heading_searcher = self.ix.searcher()
            result_docs = heading_searcher.search(parser.parse(benefits_search_string), limit=None)
            return self.text_term_frequency(result_docs)
        except ZeroDivisionError:
            return str("Für diese Anfrage waren zu wenig Dokumente vorhanden")
        finally:
            self.ix.searcher().close()

    def requirements_frequency_in_index(self) -> list:
        requirements_search_string = \
            "(anforderung~2/5 anforderungsprofil)^2 anwenderkenntnisse~ are ausmacht auszeichnet background " \
            "bedingungen berufserfahrung~2 bietest bist (bringen~2/5)^2 dein du (einstellungsvoraussetzungen~2/25)^3 " \
            "(erfahrungen~2/9)^1.5 erforderlich~ erwarten (erwartungen~/5)^1.25 essential~ experiences~/7 fachgebiet" \
            "fachliche~/8 fachrichtung fähigkeiten^2 hast have ich ihr~ kannst kenntnisse~/8 (kompetenz~2/9)^2 " \
            "kompetenzprofil meine mitbringen mitbringst optimal~3/7 (pluspunkt~)^1.25 profil~2/4 punkten " \
            "(qualifications~2/13 qualifikation~2/13)^2 reference required requirements^2 sich skills^3 sollten" \
            "solltest steckbrief (stellenanforderung~2/18)^2 talent ticken (voraussetzung~2/13 vorkenntniss~2/12)^2" \
            "wonach worauf you~2/3 zusätzliche"

        or_group = qparser.OrGroup.factory(1)
        parser = qparser.QueryParser("paragraph_heading", schema=self.schema, group=or_group)
        parser.add_plugin(qparser.FuzzyTermPlugin())

        try:
            heading_searcher = self.ix.searcher()
            result_docs = heading_searcher.search(parser.parse(requirements_search_string), limit=None)
            return self.text_term_frequency(result_docs)
        except ZeroDivisionError:
            return str("Für diese Anfrage waren zu wenig Dokumente vorhanden")
        finally:
            self.ix.searcher().close()