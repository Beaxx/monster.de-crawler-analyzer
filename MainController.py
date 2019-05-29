from Util.RequestManager import RequestManager
from Parsing import PostingLinkParser, PostingParser
from Indexing.Analyzing import Analyzer
from Util.FileHandler import FileHandler
from Indexing.Indexer import Indexer
import time
import logging
import os
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
        self.analyzer = None

    def set_job_postings(self):
        """
        Entscheidet darüber, ob eine Stellenanzeige für die Verarbeitung geeignet ist oder nicht.
        """
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

    def parsing_progress(self, count: int) -> str:
        """
        Formatiert die Fortschrittsanzeige des Parsingprozesses
        :param count: Anzahl der verarbeiteten Postings
        :return: Ein String der den Fortschritt des Parsings widergibt
        """
        return "Posting Parsing Fortschritt: {0}%".format(round(count / len(self.deep_links) * 100, 2))

    def run_wih_flags(self, search_term: str, options: list, use_stored_links=False, use_stored_postings=False,
                      re_index=True):
        """
        Entscheided darüber, welche Programmodule gestartet werden
        :param search_term: Der Suchbegriff der Anfrage
        :param options: Die im Benutzerinterface gewählten Optionen
        :param use_stored_links: Sollen gespeicherte Links verwendet werden?
        :param use_stored_postings: Sollen gespeicherte Postings verwendet werden?
        :param re_index: Soll re-indexiert werden?
        """
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

    def present_results(self, options: list):
        """
        Koordiniert die Dateierstellung und erstellung der Ergebnisausgabe
        :param options: Die vom Benutzer gewählten Optionen zur Ergebnisdarstellung
        """
        self.analyzer = Analyzer(self.search_term, self.indexer)
        handler = FileHandler()

        def format_list(input_list: list) -> list:
            """
            Hilfsmethode, die die Ausgabedaten in eine Liste (Array) formatiert
            :param input_list: die zu bearbeitende Liste
            :return: Eine formatierte Liste
            """
            out = list()
            for i in input_list:
                if len(input_list) > 2:
                    out.append("{0},{1}".format(i[0], i[1]))
                else:
                    out.append("{0},{1}".format(i, "0"))
                    return out
            return out

        if 0 in options:
            path = handler.write_output_to_file(self.search_term, self.indexer.index_info(), "index_info")
            os.startfile(path)

        if 1 in options:
            path = handler.write_output_to_file(self.search_term,
                                                pprint.pformat(
                                                    format_list(self.analyzer.task_frequency_in_index())),
                                                "task_frequency")
            os.startfile(path)

        if 2 in options:
            path = handler.write_output_to_file(self.search_term,
                                                pprint.pformat(
                                                    format_list(self.analyzer.requirements_frequency_in_index())),
                                                "requirements_frequency")
            os.startfile(path)

        if 3 in options:
            path = handler.write_output_to_file(self.search_term,
                                                pprint.pformat(
                                                    format_list(self.analyzer.benefits_frequency_in_index())),
                                                "benefits_frequency")
            os.startfile(path)


"""
Dieser Teil erlaubt die Umgehung des Userinterfaces und ist für Debugging und Entwicklungszwecke vorgesehen.
"""
# controller = MainController()
# controller.run_wih_flags("digital change management", [0, 1, 2],
#                          use_stored_links=True,
#                          use_stored_postings=True,
#                          re_index=False)
# controller.present_results([0])
# controller.present_results([1])
# controller.present_results([2])
# controller.present_results([3])
