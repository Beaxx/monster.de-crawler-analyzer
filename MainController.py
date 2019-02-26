from RequestManager import RequestManager
from Logic import PostingLinkParser, PostingParser, Posting
from FileHandler import FileHandler
import definitions
import sys
import math
import time
from MenuText import menutext


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
            if count % 20 == 0:
                self.print_parsing_progress(count)

    def print_parsing_progress(self, count: int):
        print("Fortschritt: {0}%".format(round(count / len(self.deep_links) * 100, 2)))

    def user_dialog_link_gathering(self):
        print(menutext.get("disclaimer"))
        self.search_term = input(menutext.get("insert_searchterm")).lower()
        if self.file_handler.deep_link_file_is_available(self.search_term):
            while True:
                print(menutext.get("downloaded_content_available"))
                user_input = input(menutext.get("old_new")).lower()
                if user_input == "alt":
                    self.deep_links = self.file_handler.read_job_posting_deep_links_from_file(self.search_term)
                    break
                elif user_input == "neu":
                    self.deep_links = self.link_parser.run(self.search_term)
                    self.file_handler.print_links_to_file(self.search_term, self.deep_links)
                    break
                else:
                    print(menutext.get("invalid_input"))
                    continue
        else:
            print(menutext.get("link_collection_in_progress"))
            self.deep_links = self.link_parser.run(self.search_term)
            self.file_handler.print_links_to_file(self.search_term, self.deep_links)
        print(menutext.get("links_saved").format(definitions.SKRIPT_PATH + "\\Links"))

    def user_dialog_posting_gathering(self):
        if self.file_handler.pickled_posting_file_is_availabe(self.search_term):
            print(menutext.get("posting_intro"))
            print(menutext.get("downloaded_content_available"))
            while True:
                user_input = input(menutext.get("old_new")).lower()
                if user_input == "alt":
                    self.job_postings = self.file_handler.unpickle_postings(self.search_term)
                    # self.file_handler.print_postings_to_file(self.job_postings)  # todo: entfernen
                    return
                elif user_input == "neu":
                    print(menutext.get("download_postings?").format(
                        len(self.deep_links), math.ceil(len(self.deep_links) / 60)))
                    if input(menutext.get("yes_no")).lower() == "y":
                        print(menutext.get("posting_collection_in_progress").format(
                            math.ceil(len(self.deep_links) / 60)))
                        self.set_job_postings()
                        self.file_handler.pickle_postings_to_file(self.search_term, self.job_postings)
                        print(menutext.get("postin_collection_completed"))

                        self.file_handler.print_postings_to_file(self.job_postings)
                        print(menutext.get("postings_saved").format(definitions.SKRIPT_PATH + "\\Postings"))
                        return
                    else:
                        sys.exit(menutext.get("termination_no_entry"))
                else:
                    menutext.get("invalid_input")
                    continue
        else:
            print(menutext.get("download_postings?").format(
                len(self.deep_links), math.ceil(len(self.deep_links) / 60)))
            if input(menutext.get("yes_no")).lower() == "y":
                print(menutext.get("posting_collection_in_progress").format(
                    math.ceil(len(self.deep_links) / 60)))
                self.set_job_postings()
                self.file_handler.pickle_postings_to_file(self.search_term, self.job_postings)
                print(menutext.get("postin_collection_completed"))
                print((self.posting_parser.parsing_coverage(len(self.job_postings), len(self.deep_links))))

                self.file_handler.print_postings_to_file(self.job_postings)
                print(menutext.get("postings_saved").format(definitions.SKRIPT_PATH + "\\Postings"))
            else:
                sys.exit(menutext.get("termination_no_entry"))

    def user_dialog_posting_analysis(self):
        pass


controller = MainController()
controller.user_dialog_link_gathering()
controller.user_dialog_posting_gathering()
controller.user_dialog_posting_analysis()

