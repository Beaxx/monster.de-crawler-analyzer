from RequestManager import RequestManager
from Parsing import PostingLinkParser, PostingParser
from FileHandler import FileHandler
import time
import logging


class MainController:
    def __init__(self):
        self.file_handler = FileHandler()
        self.link_parser = PostingLinkParser()
        self.posting_parser = PostingParser()
        self.deep_links: list = None
        self.job_postings: list = list()
        self.search_term: str = None

    def set_job_postings(self):
        count = 0
        for url in self.deep_links:
            time.sleep(0.1)  # politeness
            posting = self.posting_parser.build(RequestManager.unauthenticated_request(url))
            # Posting with empty text are discarded
            if posting.posting_text is not None and len(posting.posting_text) > 0:
                self.job_postings.append(posting)

            count += 1
            logging.info(self.parsing_progress(count))
        logging.info(self.parsing_coverage())

    def parsing_progress(self, count: int) -> str:
        return "Fortschritt: {0}%".format(round(count / len(self.deep_links) * 100, 2))

    def parsing_coverage(self) -> str:
        return "Parsing coverage: {0}%".format(round(len(self.job_postings) / len(self.deep_links) * 100, 2))

    def run_wih_flags(self, search_term: str, options: list, use_stored_links=False, use_stored_postings=False):
        self.search_term = search_term

        if use_stored_links:
            self.deep_links = self.file_handler.read_job_posting_deep_links_from_file(self.search_term)
        else:
            self.deep_links = self.link_parser.run(self.search_term)
            self.file_handler.print_links_to_file(self.search_term, self.deep_links)

        if 1 in options and use_stored_postings:
            self.job_postings = self.file_handler.unpickle_postings(self.search_term)
            self.file_handler.print_postings_to_file(self.job_postings)
        elif 1 in options and not use_stored_postings:
            self.set_job_postings()
            self.file_handler.pickle_postings_to_file(self.search_term, self.job_postings)
            self.file_handler.print_postings_to_file(self.job_postings)
            # print((self.posting_parser.parsing_coverage(len(self.job_postings), len(self.deep_links))))

        # if 1 in options and 2 in options:
        #     pass # Analyse to implement

# controller = MainController()
# controller.run_wih_flags("digital change management", [0, 1], use_stored_links=False, use_stored_postings=False)
