from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED, NUMERIC
from whoosh.index import create_in, Index, EmptyIndexError
from whoosh.writing import IndexWriter
from whoosh.index import open_dir
from whoosh.query import Every
from whoosh import index
import definitions
import os.path
from Util.FileHandler import FileHandler
from Indexing import Analyzing
import logging


class Indexer:
    """
    Der Indexer legt das Indexing Schema (die Felder des Index) fest und befüllt diese mit den Werten aus den Postings
    """
    def __init__(self, search_term: str):

        self.schema = Schema(
            educational_requirements=TEXT(),
            employment_type=ID(),
            experience_requirements=TEXT(),
            industry=KEYWORD(),
            organization=ID(stored=True),
            title=TEXT(stored=True),
            url=STORED(),
            parent_identifier=NUMERIC(stored=True),

            # Paragraph Data Children
            type=ID(stored=True),
            parent=NUMERIC(),
            paragraph_number=NUMERIC(stored=True),
            paragraph_heading=TEXT(analyzer=Analyzing.ImprovedTokenizer(), stored=True),
            paragraph_content=TEXT(analyzer=Analyzing.ImprovedTokenizer(), stored=True)
        )

        self.index_path: str = os.path.join(definitions.MAIN_PATH, "Storage", "Indexe", search_term)
        FileHandler.if_folder_not_existent_create(self.index_path)

        self.ix: Index = None
        self.writer: IndexWriter = None

    def build_index(self, job_postings: list):
        """
        Der builder iteriert über alle Job-Postings und indexiert die jeweiligen Werte. Die Paare aus
        {Absatzsüberschrift : Absatztext} werden dabei als Paare gespeichert und erhalten eine Referenz auf
        das jeweilige Dokument, zu dem sie gehören.

        :param job_postings: Liste von Posting Objekten
        """
        self.ix = create_in(self.index_path, self.schema)  # Overwrites index if existent
        length = len(job_postings)
        for i, posting in enumerate(job_postings):
            writer = self.ix.writer()
            writer.add_document(
                educational_requirements=posting.educational_requirements,
                employment_type=posting.empolyment_type,
                experience_requirements=posting.experience_requirements,
                industry=posting.industry,
                organization=posting.organization,
                title=posting.title,
                url=posting.url,
                parent_identifier=i
            )

            for j, paragraph in enumerate(posting.posting_text.keys()):
                writer.add_document(parent=i,
                                    paragraph_number=j,
                                    paragraph_heading=paragraph,
                                    paragraph_content=posting.posting_text.get(paragraph))
            writer.commit()
            logging.info("Indexing Fortschritt {0}%".format((round(i / length * 100, 2))))
        self.ix.writer().commit(optimize=True)

    def open_index(self):
        try:
            self.ix = open_dir(self.index_path)
        except EmptyIndexError:
            logging.warning("Index wurde nicht gefunden, neuer Index wird generiert")
            raise FileNotFoundError

    def print_paragraph_headings_for_all_docs(self):
        """
        DEBUGGING
        Gibt die Überschriften aller Absätze aller Dokumente des Index aus.
        """
        self.ix = index.open_dir(self.index_path)
        with self.ix.searcher() as s:
            for hit in s.search(Every("parent_identifier"), limit=None):
                print("Title: " + hit["title"])
                for child in s.documents(parent=hit["parent_identifier"]):
                    print("\t" + str(child["paragraph_heading"]))

    def index_info(self) -> str:
        """
        Baut einen String, der Informationen über den Index enthält. Anzahl der Dokumente und durchschnittliche
        Anzahl an Absätzen pro Dokument.
        :return: Index Informationen als String
        """
        self.ix = index.open_dir(self.index_path)
        doc_count = 0
        searcher = self.ix.searcher()
        for hit in searcher.search(Every("parent_identifier"), limit=None):
            doc_count += 1
        searcher.close()
        out_string = ("The Index contains {0} Documents\n".format(doc_count))

        paragraph_count = 0
        searcher = self.ix.searcher()
        for hit in searcher.search(Every("parent"), limit=None):
            paragraph_count += 1
        searcher.close()

        out_string += (
            "On Average every Document contains {0} Paragraphs".format(round(paragraph_count / doc_count, 2)))
        return out_string
