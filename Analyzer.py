from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
from whoosh.analysis import StemmingAnalyzer
from whoosh.index import create_in, Index
from whoosh.writing import IndexWriter
from whoosh import writing
from whoosh.query import *
from whoosh.qparser import QueryParser
from whoosh.index import open_dir
from whoosh.query import Every
import definitions
import os.path
from FileHandler import FileHandler
from Parsing import Posting


class Analyzer:
    def __init__(self):
        self.schema = Schema(
            # todo add Boosters to fields?
            educational_requirements=TEXT(),
            employment_type=ID(stored=True),
            experience_requirements=TEXT(),
            industry=KEYWORD(),  # String is seperated by /, todo: change in parser
            organization=ID(),
            paragraph_heading=TEXT(),
            paragraph_content=TEXT(),
            skills=KEYWORD(commas=True),
            title=TEXT(),
            url=STORED())

        self.index_path: str = os.path.join(definitions.SKRIPT_PATH, "Storage", "Index")
        FileHandler.if_folder_not_existent_create(self.index_path)

    def build_index(self, job_postings: list):
        self.ix: Index = create_in(self.index_path, self.schema)
        self.writer: IndexWriter = self.ix.writer()

        for posting in job_postings:
            self.writer.add_document(
                educational_requirements=posting.educational_requirements,
                employment_type=posting.empolyment_type,
                experience_requirements=posting.experience_requirements,
                industry=posting.industry,
                organization=posting.organization,
                title=posting.title,
                url=posting.url,
                skills=",".join(posting.skills) if posting.skills else ""
            )

            for j, paragraph in enumerate(posting.posting_text.keys()):
                self.writer.add_document(paragraph_heading=paragraph)
                self.writer.add_document(paragraph_content=posting.posting_text.get(paragraph))
        self.writer.commit(optimize=True)

    def print_index(self):
        self.ix: Index = open_dir(os.path.join(definitions.SKRIPT_PATH, "Storage", "Index"))
        results = self.ix.searcher().documents()
        for result in results:
            print(result)
            # print("Rank: {0} Title: {1}".format(result.rank, result['title']))
            # print("Content:")
            # print(result['paragraph_heading'])
