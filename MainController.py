from Util.RequestManager import RequestManager
from Parsing import PostingLinkParser, PostingParser
from Indexing.Analyzing import Analyzer
from Util.FileHandler import FileHandler
from Indexing.Indexer import Indexer
from whoosh.index import Index
import time
import logging
import pprint

class MainController:
    def __init__(self):
        self.file_handler = FileHandler()
        self.link_parser = PostingLinkParser()
        self.posting_parser = PostingParser()
        self.deep_links: list = None
        self.job_postings: list = list()
        self.search_term: str = None
        self.indexer: Indexer = None

    def set_job_postings(self):
        count = 0
        controll_hashset = set()
        for url in self.deep_links:
            time.sleep(0.1)  # politeness
            posting = self.posting_parser.build(RequestManager.unauthenticated_request(url))
            posting_hash = hash(posting)
            # Duplicates and Postings without inusfficient description are discarded
            if posting.posting_text:
                if len(posting.posting_text) > 1 and posting_hash not in controll_hashset:
                    self.job_postings.append(posting)
                    controll_hashset.add(posting_hash)
            count += 1
            logging.info(self.parsing_progress(count))
        logging.info(self.parsing_coverage())

    def parsing_progress(self, count: int) -> str:
        return "Fortschritt: {0}%".format(round(count / len(self.deep_links) * 100, 2))

    def parsing_coverage(self) -> str:
        return "Parsing coverage: {0}%".format(round(len(self.job_postings) / len(self.deep_links) * 100, 2))

    def run_wih_flags(self, search_term: str, options: list, use_stored_links=False, use_stored_postings=False,
                      re_index=True):
        self.search_term = search_term

        if use_stored_links:
            self.deep_links = self.file_handler.read_job_posting_deep_links_from_file(self.search_term)
        else:
            self.deep_links = self.link_parser.run(self.search_term)
            self.file_handler.print_links_to_file(self.search_term, self.deep_links)

        if 1 in options and use_stored_postings:
            self.job_postings = self.file_handler.unpickle_postings(self.search_term)
            self.file_handler.print_postings_to_file(self.search_term, self.job_postings)
        elif 1 in options and not use_stored_postings:
            self.set_job_postings()
            self.file_handler.pickle_postings_to_file(self.search_term, self.job_postings)
            self.file_handler.print_postings_to_file(self.search_term, self.job_postings)

        if 1 in options and 2 in options:
            self.indexer: Indexer = Indexer(self.search_term)
            if re_index:
                self.indexer.build_index(self.job_postings)
            else:
                try:
                    self.indexer.open_index()
                except FileNotFoundError:
                    self.indexer.build_index(self.job_postings)

            self.analyzer = Analyzer(self.search_term, self.indexer)
            # print(self.analyzer.skill_frquency_in_index())
            # pprint.pprint(self.analyzer.task_frequency_in_index())
            # pprint.pprint(self.analyzer.benefits_frequency_in_index())
            pprint.pprint(self.analyzer.requirements_frequency_in_index())

            # self.indexer.print_all_tokens()  # Debug
            # self.indexer.print_paragraph_headings_for_all_docs()  # Debug
            # self.indexer.print_index_info()  # Debug


controller = MainController()
controller.run_wih_flags("digital", [0, 1, 2],
                         use_stored_links=True,
                         use_stored_postings=True,
                         re_index=False)
