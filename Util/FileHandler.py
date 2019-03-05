import os
import definitions as defi
import pickle
import re
import hashlib
from Parsing import Posting
import shutil
import whoosh.index


class FileHandler:

    # Util
    @staticmethod
    def if_folder_not_existent_create(folder_path):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    # Links
    @staticmethod
    def deep_link_file_is_available(search_term) -> bool:
        try:
            folder_path = os.path.join(defi.MAIN_PATH, "Links")
            f = open(os.path.join(folder_path, search_term + ".txt"), "r")
            f.close()
            return True
        except FileNotFoundError:
            return False

    def print_links_to_file(self, file_name: str, links: list):
        folder_path = os.path.join(defi.MAIN_PATH, "Links")
        self.if_folder_not_existent_create(folder_path)

        with open(os.path.join(folder_path, file_name + ".txt"), "w+", encoding='utf-8') as f:
            for link in links:
                f.write(link + "\n")

    def read_job_posting_deep_links_from_file(self, search_term: str) -> list:
        folder_path = os.path.join(defi.MAIN_PATH, "Links")
        self.if_folder_not_existent_create(folder_path)

        with open(os.path.join(folder_path, search_term + ".txt"), 'r', encoding='utf-8') as f:
            content = f.readlines()
            return [x.strip() for x in content]

    # Postings
    @staticmethod
    def pickled_posting_file_is_availabe(search_term) -> bool:
        try:
            folder_path = os.path.join(defi.MAIN_PATH, "Storage")
            f = open(os.path.join(folder_path, search_term + ".pcl"), "r")
            f.close()
            return True
        except FileNotFoundError:
            return False

    def pickle_postings_to_file(self, search_term: str, job_postings: list):
        folder_path = os.path.join(defi.MAIN_PATH, "Storage")
        self.if_folder_not_existent_create(folder_path)

        with open(os.path.join(folder_path, search_term + ".pcl"), "wb+") as f:
            pickle.dump(job_postings, f)

    def unpickle_postings(self, search_term: str) -> list:
        folder_path = os.path.join(defi.MAIN_PATH, "Storage")
        self.if_folder_not_existent_create(folder_path)

        with open(os.path.join(folder_path, search_term + ".pcl"), "rb") as f:
            return pickle.load(f)

    def print_postings_to_file(self, search_term: str, job_postings: list):
        def strip_file_name(job_posting: Posting):
            try:
                return re.sub(r'\W', "", job_posting.title)[:20] + str(hash(job_posting))
            except TypeError:
                md5 = hash(job_posting)
                return "unknown" + str(md5)  # Adding part of hash to avoid name collision

        folder_path = os.path.join(defi.MAIN_PATH, "Postings", search_term)
        shutil.rmtree(folder_path, ignore_errors=True)

        self.if_folder_not_existent_create(folder_path)
        for posting in job_postings:
            with open(os.path.join(folder_path, strip_file_name(posting) + ".txt"),
                      "w+", encoding='utf-8') as f:
                f.write(posting.__str__())
        pass

    # Index
    @staticmethod
    def index_available(search_term: str) -> bool:
        folder_path = os.path.join(defi.MAIN_PATH, "Storage", "Indexe", search_term)
        return whoosh.index.exists_in(folder_path)

    # Output
    def write_output_to_file(self, search_term:str, output: str, file_name: str) -> str:
        folder_path = os.path.join(defi.MAIN_PATH, "Output", search_term)
        self.if_folder_not_existent_create(folder_path)

        file_path = os.path.join(folder_path, file_name + ".txt")
        with open(file_path, "w+", encoding='utf-8') as f:
            f.write(output)

        return file_path
