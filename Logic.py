from RequestManager import RequestManager
import definitions
from requests import Response
import re
import math
from lxml import html
import time


class PostingLinkParser:
    def __init__(self, request_manager: RequestManager):
        self.request_Manager: RequestManager = request_manager
        self.number_of_job_postings = None
        self.links = list()

    def run(self, search_term: str):
        # Initial Request
        response: Response = self.request_Manager.unauthenticated_request(self.build_url(search_term, 1, 1))
        self.number_of_job_postings = self.parse_number_of_jobs_found(response.text)

        for i in self.calculate_request_arguments(self.number_of_job_postings):
            response: Response = self.request_Manager.unauthenticated_request(self.build_url(search_term, 1, i))
            dom_tree: html = self.parse_html(response.content)
            links = self.get_job_posting_links_from_dom(dom_tree)
            self.__merge_links(links)

            time.sleep(1)  # Politeness
        return self.links

    def __merge_links(self, links):
        for link in links:
            if link not in self.links:
                self.links.append(link)

    @staticmethod
    def get_job_posting_links_from_dom(dom_tree: html):
        links = list()
        postings = dom_tree.xpath(r"//section[@data-jobid][not(./p[@class='entry'])]")
        for posting in postings:
            links.append(posting.find('.//*[@href]').attrib.get("href"))
        return links

    @staticmethod
    def parse_html(page: bytes) -> html:
        return html.fromstring(page)

    @staticmethod
    def build_url(search_term: str, start_page: int, current_page: int) -> str:
        base_url = definitions.BASE_URL
        return base_url+r"q={0}&stpage={1}&page={2}".format(search_term, start_page, current_page)

    @staticmethod
    def convert_str_to_search_token(input_string: str) -> str:
        return input_string.lower().replace(" ", "-")

    @staticmethod
    def parse_number_of_jobs_found(input_html: str) -> int:
        return int(re.search(r"(?<=\()[][0-9]{2,4}(?= Jobs gefunden\))", input_html).group())

    @staticmethod
    def calculate_request_arguments(number_of_job_postings: int) -> list:
        arguments = list()
        x = 1
        while math.ceil(number_of_job_postings / 20) - x > 0:
            arguments.append(x)
            x += 1
        return arguments


class PostingParser:
    def __init__(self):
        pass

    def parse(self, request_manager: RequestManager, url):
        pass
