from io import StringIO
import npyscreen as np
from MainController import MainController
import definitions
import logging.handlers
import time
import threading

# Texts for menus in user interface
menutext = {
    "title": "Monster.de Crawler V0.3",
    "disclaimer1": "### Bei jeder Ausführung des Programs gilt zu bedenken, ",
    "disclaimer2": "dass mehrere hundert Anfragen an den Server gestellt werde können. ###",
    "saved_links_avail": "Der eingegebene Suchbegriff wurde schon einmal eingegeben. Es liegen daher bereits "
                         "gespeicherte Links zu dieser Anfrage vor. Sollen diese verwendet werden[YES], oder sollen "
                         "aktuelle Links abgefragt werden[NO]?\n Das verwenden abgespeicherter Links ist "
                         "zeit- und bandbreitesparend, die Links sind jedoch nicht aktuell.",
    "saved_postings_avail": "Der eingegebene Suchbegriff wurde schon einmal eingegeben. Es liegen bereits "
                         "geparste Postings zu dieser Anfrage vor. Sollen diese verwendet werden[YES], oder sollen "
                         "die Postings neu geparst werden[NO]?\n Das verwenden abgespeicherter Postings ist "
                         "(sehr) zeit- und bandbreitesparend. Das Programm springt bei [YES] direkt in die Analyse.",
    "index_avail": "Für den eingegebenen Suchbegriff existiert bereits ein Dokument-Index. Soll dieser verwendet werden"
                   "[NO]? oder soll reindexiert werden [YES]?"
}


class App(np.NPSAppManaged):
    """
    Wrapper um die Programfenster. Schafft einen high-level Rahmen um die ganze Anwendung und stellt für die daran
    angeschlossenen Subklassen einen globalen variablen Scope bereit.
    """
    use_stored_links = False
    use_stored_postings = False
    re_index = False
    picked_options = None
    search_term = None
    output_selection = None

    def onStart(self):
        """
        Legt die Forms fest, die zum Start generiert werden sollen (werden jedoch noch nicht angezeigt)
        """
        self.controller: MainController = MainController()
        self.addForm('MAIN', MainForm, name=menutext.get("title"))
        self.addForm('Progress', ProgressForm, name=menutext.get("title"))
        self.addForm('OutputSelection', Outputform, name=menutext.get("title"))
        self.init_logger()

    def init_logger(self):
        """
        Debugging
        Umleitung des logging Outputs auf einen listener. Dieser muss über die Datei log_listener.py separat gestartet
        werden
        """
        self.rootLogger = logging.getLogger('')
        self.rootLogger.setLevel(logging.DEBUG)
        socketHandler = logging.handlers.SocketHandler('localhost', logging.handlers.DEFAULT_TCP_LOGGING_PORT, )
        self.rootLogger.addHandler(socketHandler)
        logging.info('-' * 20)


class MainForm(np.SplitForm):
    """
    Start Screen der Anwendung
    """

    def create(self):
        """
        Generiert  die Elemente des MainForm
        """

        self.search_term: np.TitleText = self.add(np.TitleText, name='Suchbegriff', color='DANGER', editable=True,
                                                  value='digital change management')

        self.options: np.TitleMultiSelect = self.add(np.TitleMultiSelect, scroll_exit=True, editable=True,
                                                     max_height=4, name='Optionen',
                                                     values=['Links Abrufen', 'Postings Abrufen', 'Analyse'],
                                                     value=[0, 1, 2])

        self.nextrely += 4
        self.disclaimer1: np.FixedText = self.add(np.FixedText, value=menutext.get("disclaimer1"), color="STANDOUT",
                                                  name='disclaimer1')
        self.disclaimer2: np.FixedText = self.add(np.FixedText, value=menutext.get("disclaimer2"), color="STANDOUT",
                                                  name='disclaimer2')

    def afterEditing(self):
        """
        Legt Aktionen fest, die ausgeführt werden, sobald der OK-Button des Main Forms betätigt wird.
        """

        self.parentApp.search_term = self.search_term.value
        self.parentApp.picked_options = self.options.value

        if self.check_inputs("links"):
            self.parentApp.use_stored_links: bool = np.notify_yes_no(menutext.get("saved_links_avail"),
                                                                     "Achtung!", editw=1)

        if self.check_inputs("postings"):
            self.parentApp.use_stored_postings: bool = np.notify_yes_no(menutext.get("saved_postings_avail"),
                                                                        "Achtung!", editw=1)

        if self.check_inputs("index"):
            self.parentApp.re_index: bool = np.notify_yes_no(menutext.get("index_avail"), "Achtung!", editw=1)

        self.parentApp.setNextForm('Progress')

    def check_inputs(self, identifier):
        """
        Eingabeüberprüfung
        :param identifier: Identifiziert den zu überprüfenden Input
        """

        def search_term_ok() -> bool:
            if self.search_term.value is None or len(self.search_term.value) < 5:
                return False
            else:
                return True

        def options__input_ok() -> bool:
            if len(self.options.value) == 0:
                return False
            else:
                return True

        def options_order_ok() -> bool:
            if sorted(self.options.value) != [0, 1, 2] and sorted(self.options.value) != [0, 1]:
                return False
            else:
                return True

        def saved_links_available() -> bool:
            if self.parentApp.controller.file_handler.deep_link_file_is_available(
                    self.search_term.value.lower()):
                return True

        def saved_postings_available() -> bool:
            if len(self.options.value) > 0:
                if sorted(self.options.value)[1] == 1 and \
                        self.parentApp.controller.file_handler.pickled_posting_file_is_availabe(
                            self.search_term.value.lower()):
                    return True

        def index_available() -> bool:
            if self.parentApp.controller.file_handler.index_available(
                    self.search_term.value.lower()):
                return True

        switcher = {
            "term": search_term_ok,
            "options": options__input_ok,
            "options_order": options_order_ok,
            "links": saved_links_available,
            "postings": saved_postings_available,
            "index": index_available
        }

        return switcher[identifier]()


class ProgressForm(np.Form):
    """
    Progress Screen der Anwendung
    """

    def create(self):
        """
        Generiert  die Elemente des Progress Form
        """

        self.keypress_timeout = 1
        self.fixed_text: np.FixedText = self.add(np.FixedText, relx=55, value="PROGRESS")

        self.links_text: np.TitleText = self.add(np.TitleText, name="Speicherort Links:",
                                                 value=definitions.MAIN_PATH + "\\Links")
        self.nextrely += 2
        self.links_text: np.TitleText = self.add(np.TitleText, name="Speicherort Postings:",
                                                 value=definitions.MAIN_PATH + "\\Postings")

    def beforeEditing(self):
        """
        Legt Aktionen fest, die nach der Generierung der Elemente des Progress Forms und vor ihrer Editierung
        stattfinden
        """

        # Starts algorithm thread
        self.main_thread: threading.Thread = threading.Thread(target=self.parentApp.controller.run_wih_flags,
                                                              args=(self.parentApp.search_term,
                                                                        sorted(self.parentApp.picked_options),
                                                                        self.parentApp.use_stored_links,
                                                                        self.parentApp.use_stored_postings,
                                                                        self.parentApp.re_index))
        self.main_thread.setDaemon(True)
        self.main_thread.start()
        self.nextrely += 5
        self.progress_notify = self.add(np.FixedText, relx=50, color='DANGER', value="Vorgang läuft...")

        # Starts progress notification thread
        self.blink_kill_flag = False
        self.blink_thread: threading.Thread = threading.Thread(target=self.blink)
        self.blink_thread.setDaemon(True)
        self.blink_thread.start()

        # Starts progress-done notification thread
        finished_thread = threading.Thread(target=self.finished_message)
        finished_thread.start()

        # Starts %-progress notification thread
        self.progrss_kill_flag = False
        self.progress_stream_thread: threading.Thread = threading.Thread(target=self.progress_stream)
        self.progress_stream_thread.setDaemon(True)
        self.progress_stream_thread.start()

        # Manage thread termination
        managing_thread: threading.Thread = threading.Thread(target=self.manage_threads)
        managing_thread.setDaemon(True)
        managing_thread.start()

    def afterEditing(self):
        """
        Legt Aktionen fest, die ausgeführt werden, sobald der OK-Button des Progress Forms betätigt wird.
        """

        if 2 in self.parentApp.picked_options:
            self.parentApp.setNextForm('OutputSelection')
        else:
            self.parentApp.setNextForm(None)

    def progress_stream(self):
        """
        Generiert einen Output Stream, die den prozentualen Forschritt der Anwendung protokolliert und ausgibt
        """
        progress_stream = StringIO()
        request_stream = StringIO()

        root = logging.getLogger()
        progress_handler = logging.StreamHandler(progress_stream)
        request_handler = logging.StreamHandler(request_stream)

        progress_handler.setLevel(logging.INFO)
        request_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(message)s')
        progress_handler.setFormatter(formatter)
        request_handler.setFormatter(formatter)

        root.addHandler(progress_handler)
        root.addHandler(request_handler)

        self.progress_line = self.add(np.FixedText, color="CONTROL", value="")
        self.requests_line = self.add(np.Textfield, color="CONTROL", value="")
        while not self.progrss_kill_flag:
            time.sleep(0.2)
            self.progress_line.value = progress_stream.getvalue()[:37]  # Capture end of stream
            self.requests_line.value = request_stream.getvalue()

            self.progress_line.update()
            self.requests_line.update()

            progress_stream.seek(0)
            request_stream.seek(0)
        progress_stream.close()
        request_stream.close()
        progress_handler.close()
        request_handler.close()

    def finished_message(self):
        """
        Generiert die "Prozess abgeschlossen"-Nachricht
        """
        while not self.blink_kill_flag:
            time.sleep(1)
        self.progress_notify.color = 'GOOD'
        self.progress_notify.relx = 40
        self.progress_notify.value = 'Prozess erfolgreich abgeschlossen!'
        self.progress_notify.update()

    def manage_threads(self):
        """
        Setzt die kill-Flags der Subthreads auf True, wenn der Algorithmus seine Arbeit abgeschlossen hat.
        """

        while self.main_thread.isAlive():
            time.sleep(1)
        self.blink_kill_flag = True
        self.progrss_kill_flag = True

    def blink(self):
        """
        Generiert die blinkende Animation der "Vorgang läuft..." Nachricht
        """
        while not self.blink_kill_flag:
            self.progress_notify.color = 'CAUTION'
            self.progress_notify.update()
            time.sleep(0.7)
            self.progress_notify.color = 'DANGER'
            self.progress_notify.update()
            time.sleep(0.7)


class Outputform(np.Form):
    """
    Output Screen der Anwendung
    """
    def create(self):
        """
        Generiert die Elemente des Output Form
        """
        self.keypress_timeout = 1
        self.fixed_text: np.FixedText = self.add(np.FixedText, relx=55, value="Ergebnisdarstellung Auswählen")

        self.options: np.TitleMultiSelect = self.add(np.TitleMultiSelect, scroll_exit=True, editable=True,
                                                     name='Optionen',
                                                     values=['Index Informationen',
                                                             'Häufigste Tätigkeiten',
                                                             'Häufigste Anforderungen',
                                                             'Häufigste Benefits',
                                                             'Häufigkeit Skills'])

    def afterEditing(self):
        """
        Legt Aktionen fest, die ausgeführt werden, sobald der OK-Button des Output Forms betätigt wird.
        Startet die Generierung des Outputs
        """
        self.parentApp.controller.present_results(sorted(self.options.value))


if __name__ == '__main__':
    TestApp = App().run()
