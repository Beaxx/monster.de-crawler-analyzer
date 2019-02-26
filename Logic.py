from RequestManager import RequestManager
import definitions
from requests import Response
import re
import math
from lxml import html
from lxml.html import HtmlElement
import time
import json
from datetime import datetime
from bs4 import BeautifulSoup as Bs


class PostingLinkParser:
    def __init__(self):
        self.number_of_job_postings = None
        self.links = list()

    def run(self, search_term: str) -> list:
        # Initial Request
        response: Response = RequestManager.unauthenticated_request(self.build_url(search_term, 1, 1))
        self.number_of_job_postings = self.parse_number_of_jobs_found(response.text)

        for i in self.calculate_request_arguments(self.number_of_job_postings):
            response: Response = RequestManager.unauthenticated_request(self.build_url(search_term, 1, i))
            dom_tree: html = self.parse_html(response)
            links = self.get_job_posting_links_from_dom(dom_tree)
            self.__merge_links(links)

            time.sleep(0.1)  # Politeness
        return self.links

    def __merge_links(self, links):
        for link in links:
            if link not in self.links:
                self.links.append(link)

    @staticmethod
    def parse_html(page: Response) -> HtmlElement:
        return html.fromstring(page.content)

    @staticmethod
    def get_job_posting_links_from_dom(dom_tree: HtmlElement) -> list:
        links = list()
        postings = dom_tree.xpath(r"//section[@data-jobid][not(./p[@class='entry'])]")
        for posting in postings:
            links.append(posting.find('.//*[@href]').attrib.get("href"))
        return links

    @staticmethod
    def build_url(search_term: str, start_page: int, current_page: int) -> str:
        base_url = definitions.BASE_URL
        return base_url + r"q={0}&stpage={1}&page={2}".format(search_term, start_page, current_page)

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


class Posting:
    def __init__(self):
        self.url: str = None
        self.title: str = None
        self.organization: str = None
        self.date_posted: datetime.date = None
        self.educational_requirements: str = None
        self.industry: list = list()
        self.empolyment_type: str = None
        self.location: list = [0, 0]
        self.experience_requirements: str = None
        self.skills: list = None
        self.posting_text: dict = None

    def __str__(self):
        def posting_text_strngbuilder():
            s_parts = list()
            for content_block_key in self.posting_text:
                s_parts.append("{0}\n{1}".format(content_block_key, self.posting_text.get(content_block_key)))
            return '\n\n'.join(s_parts)

        return "URL: {0}\n" \
               "Titel: {1}\n" \
               "Unternehmen: {2}\n" \
               "Veröffentlichung: {3}\n" \
               "Bildungs-Voraussetzungen: {4}\n" \
               "Branche: {5}\n" \
               "Beschäftigungsverhältnis: {6}\n" \
               "Berufserhfarung: {7}\n" \
               "Skills: {8}\n" \
               "Anzeigentext:\n {9}\n".format(
                self.url,
                self.title,
                self.organization,
                self.date_posted,
                self.educational_requirements,
                self.industry,
                self.empolyment_type,
                self.experience_requirements,
                self.skills,
                posting_text_strngbuilder())


class PostingParser:
    def build(self, response: Response) -> Posting:
        posting = Posting()
        posting_data: dict = self.parsing_controller(response.text)

        if len(posting_data) > 0:
            if posting_data.get("url") is not None:
                posting.url = posting_data.get("url")

            if posting_data.get("title") is not None:
                posting.title = posting_data.get("title")

            if posting_data.get("datePosted") is not None:
                posting.date_posted = datetime.strptime(posting_data.get("datePosted"), "%Y-%M-%d").date()

            if posting_data.get("educationRequirements") is not None:
                posting.educational_requirements = posting_data.get("educationRequirements")

            if posting_data.get("industry") is not None:
                posting.industry = [x for x in posting_data.get("industry")]

            if posting_data.get("employmentType") is not None:
                posting.empolyment_type = [x for x in posting_data.get("employmentType")]

            if posting_data.get("jobLocation") is not None and posting_data.get("jobLocation")[0].get("geo") is not None:
                posting.location = [posting_data.get("jobLocation")[0].get("geo").get("latitude"),
                                    posting_data.get("jobLocation")[0].get("geo").get("longitude")]

            if posting_data.get("hiringOrganization") is not None and posting_data.get(
                    "hiringOrganization").get("name") is not None:
                posting.organization = posting_data.get("hiringOrganization").get("name")

            if posting_data.get("experienceRequirements") is not None:
                posting.experience_requirements = posting_data.get("experienceRequirements")

            if posting_data.get("skills") is not None:
                posting.skills = self.__parse_skills(posting_data.get("skills"))

            if posting_data.get("description") is not None:
                posting.posting_text = self.__parse_description(posting_data.get("description"))

        return posting

    def parsing_controller(self, html_txt: str):
        soup: Bs = Bs(html_txt, 'lxml')
        match_json = soup.findAll("script", {"type": 'application/ld+json'})
        if len(match_json) == 1 and len(match_json[0].text) > 2000:
            return self.parse_posting_from_json(match_json[0].text)
        elif len(match_json) > 1 and len(match_json[0].text) > 2000:
            for i in match_json:
                if "GeoCoordinates" in i.text:
                    return self.parse_posting_from_json(i.text)
        elif len(match_json) == 0 or (len(match_json) == 1 and len(match_json[0].text) < 2000):
            return self.parse_posting_from_html(soup)

    @staticmethod
    def parsing_coverage(job_listing_count: int, link_count: int) -> str:
        return "Parsing coverage: {0}%".format(round(job_listing_count/link_count * 100, 2))

    @staticmethod
    def parse_posting_from_json(json_string: str) -> dict:
        try:
            return json.loads(json_string)
        except json.decoder.JSONDecodeError:
            return dict()

    @staticmethod
    def parse_posting_from_html(soup: Bs) -> dict:
        try:
            match_html = soup.find('div', {'class' : re.compile(r'\Wmaincontent\W')})
            return {"description": match_html.text.replace(r'\r', "").replace(r'\n', "").replace(r'\t', "")}
        except AttributeError:
            return dict()

    @staticmethod
    def __parse_skills(skills: str) -> list:
        skill_list = skills.split(",")
        out = list()
        for x in skill_list:
            out.append(x.strip())
        return out

    @staticmethod
    def __parse_description(description: str) -> dict:
        description_partially_stripped = re.sub(
            r'<[^h1-9].*?[^1-9]>', '', description).replace('\n', '').replace(r"<p>", "")  # Strips all Tags except h1-h6
        description_reduced_returns = re.sub(
            r'[\r\n\0\s]*(?=[\r\n\0])|(?<=>)[\r\n\0\s]|(?=\s)[\r\n\0\s]{2,}', '',  # Strip carriage returns and new lines
            description_partially_stripped)  # Strips /r and /n

        headings: Bs = Bs(description_reduced_returns, "lxml").find_all(['h{0}'.format(int(x)) for x in range(1, 7)])

        output = dict()
        for block in headings:
            block_content = str(block.nextSibling).strip().replace("\n", "").replace("\r", "")
            if block_content != "":
                output[block.text.strip()] = block_content
        return output

