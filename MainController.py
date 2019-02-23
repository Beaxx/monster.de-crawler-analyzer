from RequestManager import RequestManager
from Logic import PostingLinkParser, PostingParser
import definitions
import os


class MainController:
    def __init__(self):
        self.deep_links = None
        self.request_manager = RequestManager()

    def get_job_posting_deep_links_for_search_term(self, search_term):
        link_parser = PostingLinkParser(self.request_manager)
        self.deep_links = link_parser.run(search_term)

    def save_links_to_file(self, file_name):
        folder_path = definitions.SKRIPT_PATH + "\\Links"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        with open(folder_path + "\\" + file_name + ".txt", "w+") as f:
            for link in self.deep_links:
                f.write(link + "\n")

    def get_jon_posting_plain_texts(self):
        posting_parser = PostingParser
        for url in self.deep_links:
            posting_parser.parse(self.request_manager, url)


    @staticmethod
    def user_dialog():
        term = input("Bitte Suchterm eingeben. (Beispiel: 'Digital Innovation'):\n")
        print("Bearbeitung Läuft...")
        controller.get_job_posting_deep_links_for_search_term(term)
        controller.save_links_to_file(term)
        print("Prozess abegeschlossen. Die Links wurden in das Verzeichnis {0} gelegt.".format(
            definitions.SKRIPT_PATH + "\\Links"))
        print("Soll eine Analyse der gefundenen Angebote durchgeführt werden?")
        if input("[Y/any]: ").lower() == "y":
            pass # todo



controller = MainController()
controller.user_dialog()
