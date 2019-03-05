from Util.RequestManager import RequestManager
import definitions
from requests import Response
from regex import regex as re
from lxml.etree import tostring as etree_tostring
import math
from lxml import html
from lxml.html import HtmlElement
import time
import json
from datetime import datetime
from bs4 import BeautifulSoup as Bs
from urllib.parse import unquote
import hashlib


class PostingLinkParser:
    """
    Suche nach Links zu Job-Anzeigen
    """

    def __init__(self):
        self.number_of_job_postings = None
        self.links = list()
        self.job_ids = set()

    def run(self, search_term: str) -> list:
        """
        Iteriert über alle Ergebnisseiten für einen Suchbegriff

        Limitation: Monster.de gibt nicht mehr als 1000 Suchergebnisse zurück. Für Anfragen, die mehr als 1000
                    Ergebnisse liefern, können nur die ersten 1000 Links abgerufen werden. Alle Anfragen jenseits der
                    40sten Ergebnisseite resultieren in einem Serverfehler.

        :param search_term: Suchbegriff
        :return: Eine Liste der gefundenen Links zu Job-Postings
        """
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
        """
        Fügt links nur dann der Objekt-liste hinzu, wenn ihre Job-Id noch nicht im job_id set vorhanden ist.
        :param links: Liste an URLs als Strings
        """
        for link in links:
            try:
                job_id = re.search(r"[[:xdigit:]-]{9,}", link).group()
                if job_id not in self.job_ids:
                    self.links.append(link)
                    self.job_ids.add(job_id)
            except TypeError:
                pass

    @staticmethod
    def parse_html(page: Response) -> HtmlElement:
        """
        Parst den HTML-Text einer Seite
        :param page: HTMl einer Seite in Bytes
        :return: lxml HtmlElement
        """
        return html.fromstring(page.content)

    @staticmethod
    def get_job_posting_links_from_dom(dom_tree: HtmlElement) -> list:
        """
        Extrahiert Links für Job Postings aus Ergebnisseite
        :param dom_tree: Ergebnisseite als lxml Element
        :return: Liste aus Links
        """
        links = list()
        postings = dom_tree.xpath(r"//section[@data-jobid][not(./p[@class='entry'])]")
        for posting in postings:
            links.append(posting.find('.//*[@href]').attrib.get("href"))
        return links

    @staticmethod
    def build_url(search_term: str, start_page: int, current_page: int) -> str:
        """
        URL-Builder für Ergebnisseiten
        :param search_term: Suchterm
        :param start_page: Ergebnisseitenindex, von der an die Angebote angezeigt werden sollen
        :param current_page: Ergebnisseitenindex der aktuellen Seite
        :return: URL String
        """
        base_url = definitions.BASE_URL
        return base_url + r"q={0}&stpage={1}&page={2}".format(search_term, start_page, current_page)

    @staticmethod
    def parse_number_of_jobs_found(input_html: str) -> int:
        """
        Im oberen Teil der Ergebnisseite wird angegeben, wie viele Postings für die Suchanfrage gefunden wurden.
        Diese Information wird durch diese Funktion geparst.
        :param input_html: HTML String der Ergebnisseite
        :return: Anzahl der gefundenen Job Postings
        """
        return int(re.search(r"(?<=\()[][0-9]{2,4}(?= Jobs gefunden\))", input_html).group())

    @staticmethod
    def calculate_request_arguments(number_of_job_postings: int) -> list:
        """
        Berechnet, wie viele Ergebnisseiten es auf Basis der gefundenen Jobs für die Anfrage gibt.
        Pro Seite werden 25 Ergebnisse angezeigt. Der Seitenaufbau lässt es dabei zu die ersten 250 Ergebnisse auf
        einer Seite anzuzeigen. Der initiale Index 'x' wird daher so gesetzt, dass möglichst viele Angebote im ersten
        Request erreicht werden können. Ab Ergebnis 250 (Seite 10) werden nur noch 25 Ergebnisse pro Seite dargestellt,
        weshalb spätestens von x=10 aus iterativ weiter gegeangen werden muss.

        Requests, die eine Ergebnisseite > 40 aufrufen resultieren in einer 404 response. Auch wenn mehr Ergebnisse
        verfügbar wären.

        :param number_of_job_postings: Anzahl der Job Postings für die Suchanfrage
        :return: Liste von Argumenten, mit denen die Requests durchgeführt werden sollen.
        """
        arguments = list()
        x = math.floor(number_of_job_postings / 25)
        if x > 10:
            x = 10

        while math.ceil(number_of_job_postings / 25) - x > 0:
            arguments.append(x)
            x += 1

            if x == 40:
                break
        arguments.append(x)
        return arguments


class Posting:
    """
    Ein Posting ist die geparste Repräsentation einer Job-Anzeige
    """

    def __init__(self):
        self.url: str = None
        self.title: str = None
        self.organization: str = None
        self.date_posted: datetime.date = None
        self.educational_requirements: str = None
        self.industry: str = None
        self.empolyment_type: str = None
        self.location: list = [0, 0]
        self.experience_requirements: str = None
        self.skills: str = None
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

    def __hash__(self):
        return int(hashlib.md5(self.__repr__().encode('utf-8')).hexdigest(), 16)


class PostingParser:
    """
    Ähnlich dem LinkParser ist der PostingParser für den Aufbau von Posting Repräsentationen aus den Jobanzeigen
    verantwortlich.
    """

    def build(self, response: Response) -> Posting:
        """
        Erstellt und befüllt ein Posting Objekt mit Informationen aus der Entsprechenden Seite
        :param response: HTML code des postings in Bytes
        :return: Ein Posting
        """

        posting = Posting()
        posting_data: dict = self.parsing_controller(response.text)

        if len(posting_data) > 0:
            if posting_data.get("url") is not None:
                posting.url = posting_data.get("url").lower()

            if posting_data.get("title") is not None:
                posting.title = posting_data.get("title").lower()

            if posting_data.get("datePosted") is not None:
                posting.date_posted = datetime.strptime(posting_data.get("datePosted"), "%Y-%M-%d").date()

            if posting_data.get("educationRequirements") is not None:
                posting.educational_requirements = posting_data.get("educationRequirements").lower()

            if posting_data.get("industry") is not None:
                posting.industry = ",".join(posting_data.get("industry")).replace("/", " ").lower()

            if posting_data.get("employmentType") is not None:
                posting.empolyment_type = ",".join(posting_data.get("employmentType")).lower()

            if posting_data.get("jobLocation") is not None and posting_data.get("jobLocation")[0].get(
                    "geo") is not None:
                posting.location = [posting_data.get("jobLocation")[0].get("geo").get("latitude"),
                                    posting_data.get("jobLocation")[0].get("geo").get("longitude")]

            if posting_data.get("hiringOrganization") is not None and posting_data.get(
                    "hiringOrganization").get("name") is not None:
                posting.organization = posting_data.get("hiringOrganization").get("name").lower()

            if posting_data.get("experienceRequirements") is not None:
                posting.experience_requirements = posting_data.get("experienceRequirements").lower()

            if posting_data.get("skills") is not None:
                posting.skills = posting_data.get("skills").lower()

            if posting_data.get("description") is not None:
                posting.posting_text = self.__parse_description(posting_data.get("description"))

        return posting

    def parsing_controller(self, html_txt: str):
        """
        Kontrollfunktion, die auf Basis der Form des HTMLs festlegt, wie die gegebene Job-Anzeige geparst werden soll.
        :param html_txt: HTML der Seite als String
        """

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
    def parse_posting_from_json(json_string: str) -> dict:
        """
        Parst JSON strings in Dictionarys
        :param json_string: Eingabestring
        :return: Diktionary
        """
        try:
            return json.loads(json_string)
        except json.decoder.JSONDecodeError:
            return dict()

    @staticmethod
    def parse_posting_from_html(soup: Bs) -> dict:
        """
        Versucht Posting Text aus HTML zu gewinnen
        :param soup: BS4 HTML Objekt
        :return: Dictionary
        """
        try:
            match_html = soup.find('div', {'class': re.compile(r'\Wmaincontent\W')})
            return {"description": match_html.text.replace(r'\r', "").replace(r'\n', "").replace(r'\t', "")}
        except AttributeError:
            return dict()

    def __parse_description(self, description: str) -> dict:
        """
        Interpretiert HTML Text und versucht dabei Absätze und Überschriften zu identifizieren.
        :param description: Job Description als HTML
        :return: Dictionary der Form {Absatzüberschrift: Absatztext}
        """

        description_parsed: HtmlElement = html.fromstring(description.strip().replace("\r", "").replace("\n", ""))

        ###Search for all heading indicating tags ###
        # Search heading by HTML
        headings: HtmlElement = description_parsed.xpath(
            r"//*[self::strong or self::b or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]"
            r"[string-length(text()) > 3]")

        # Search Heading by css
        if len(headings) == 0:
            headings: HtmlElement = description_parsed.xpath(
                r"//*[contains(@style, 'font-weight') or contains(@style, 'font-size: 14')][string-length(text()) > 3]")

        # If there are no headings, parsing cant continue
        if len(headings) == 0:
            return dict()

        # Search content by HTML
        contents = headings[0].xpath(r"//*[string-length(text()) > 3]")

        # Search content by CSS
        if len(contents) == 0:
            contents = headings[0].xpath(r"//*[contains(@style, 'font-weight')][string-length(text()) > 4]")

        # If there is not content, parsing cant continue
        if len(contents) == 0:
            return dict()

        paragraphs = list()
        for i, heading in enumerate(headings):
            paragraphs.append(list())

            content_begins_flag = False
            is_last_heading = False
            for line in contents:
                try:
                    if not is_last_heading:
                        if line.text == headings[i + 1].text:  # Current line matching next heading
                            break  # indicates end of content block

                except IndexError:
                    is_last_heading = True  # If headings[i +1] throws an index error this is the last heading
                except TypeError:
                    continue

                if is_last_heading and len(paragraphs[i]) > 10:  # For the last heading only parse 10 rows
                    break  # this is needed because last heading matches to EOF

                try:
                    if line.text == heading.text and 5 < len(line.text) < 40:  # When current heading is matched begin
                        paragraphs[i].append(heading.text)  # content parsing
                        content_begins_flag = True
                        continue
                except TypeError:
                    continue

                if content_begins_flag:
                    paragraphs[i].append(line.text)  # as long as flag is True parse content

        paragraphs.sort(key=len, reverse=True)  # Puts lists that are empty to the end

        output = dict()
        for i, paragraph in enumerate(paragraphs):
            try:
                p_sanatized = self.sanatize_paragraph(paragraph)

                if len(paragraph) > 0:
                    if len(max(p_sanatized, key=len)) > 20:
                        paragraph_content = " ".join(p_sanatized[1:])
                        output[p_sanatized[0].lower()] = paragraph_content.lower()
                    else:
                        continue
            except (IndexError, TypeError, ValueError):
                continue
        return output

    @staticmethod
    def sanatize_paragraph(paragraph) -> list:
        """
        Entfernung von zeichen, zahlen, überzähligen Leerzeichen
        :param paragraph: Liste von Strings
        :return: Bereinigte Liste von Strings
        """
        sanatized = list()
        for ind, itm in enumerate(paragraph):
            if itm:
                itm = re.sub(r"\.", " ", itm)  # Replace dots with whitespaces
                itm = re.sub(r"(?=[^ ])\P{L}", " ", itm)  # Replace all non-word chars with whitespaces
                itm = re.sub(r" {2,}", " ", itm)  # Strip excess whitespaces

                if not itm or len(itm.strip()) <= 3:
                    continue
                sanatized.append(itm.strip().lower())

            if not itm and ind == 0:
                return list()
        if len(sanatized) == 1:
            return list()

        return sanatized
