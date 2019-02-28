import npyscreen as np
from MainController import MainController
import definitions
import logging.handlers
import time
import threading

menutext = {
    "title": "Monster.de Crawler V0.1",
    "disclaimer1": "### Bei jeder Ausführung des Programs gilt zu bedenken, ",
    "disclaimer2": "dass mehrere hundert Anfragen an den Server gestellt werde können. ###",
}


class App(np.NPSAppManaged):
    use_stored_links = False
    use_stored_postings = False
    picked_options = None
    search_term = None

    def onStart(self):
        self.controller: MainController = MainController()
        self.addForm('MAIN', MainForm, name=menutext.get("title"))
        self.addForm('Progress', ProgressForm, name=menutext.get("title"))
        self.init_logger()

    # Debugging via log_listener
    def init_logger(self):
        self.rootLogger = logging.getLogger('')
        self.rootLogger.setLevel(logging.DEBUG)
        socketHandler = logging.handlers.SocketHandler('localhost', logging.handlers.DEFAULT_TCP_LOGGING_PORT, )
        self.rootLogger.addHandler(socketHandler)
        logging.info('-' * 20)  # I added this line, to separate traces from multiple runs.


class MainForm(np.SplitForm):
    def create(self):
        self.search_term: np.TitleText = self.add(np.TitleText, name='Suchbegriff', color='DANGER', editable=True,
                                                  value='digital change management')

        self.options: np.TitleMultiSelect = self.add(np.TitleMultiSelect, scroll_exit=True, editable=True,
                                                     max_height=4, name='Optionen',
                                                     values=['Links Abrufen', 'Postings Abrufen', 'Analyse'],
                                                     value=[0,1])

        self.nextrely += 4
        self.disclaimer1: np.FixedText = self.add(np.FixedText, value=menutext.get("disclaimer1"), color="STANDOUT",
                                                  name='disclaimer1')
        self.disclaimer2: np.FixedText = self.add(np.FixedText, value=menutext.get("disclaimer2"), color="STANDOUT",
                                                  name='disclaimer2')

    def afterEditing(self):
        # all_checked = [False, False, False, False, False]
        #
        # if not self.check_inputs("term") and not all_checked[0]:
        #     np.notify_confirm("Suchfeld fehler", "Fehler", editw=1)
        # else:
        #     all_checked[0] = True
        #
        # if not self.check_inputs("options") and not all_checked[1]:
        #     np.notify_confirm("Keine Optionen eingegeben", "Fehler", editw=1)
        # else:
        #     all_checked[1] = True
        #
        # if not self.check_inputs("options_order") and not all_checked[2]:
        #     np.notify_confirm("Reihenfolge Optionen falsch", "Fehler", editw=1)
        # else:
        #     all_checked[2] = True
        self.parentApp.search_term = self.search_term.value
        self.parentApp.picked_options = self.options.value

        if self.check_inputs("links"):
            self.parentApp.use_stored_links: bool = np.notify_yes_no("Saved links avail", "Achtung!", editw=1)

        if self.check_inputs("postings"):
            self.parentApp.use_stored_postings: bool = np.notify_yes_no("Saved Postings avail", "Achtung!", editw=1)

        self.parentApp.setNextForm('Progress')

    def check_inputs(self, identifier):
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

        switcher = {
            "term": search_term_ok,
            "options": options__input_ok,
            "options_order": options_order_ok,
            "links": saved_links_available,
            "postings": saved_postings_available
        }

        return switcher[identifier]()


class ProgressForm(np.Form):
    def create(self):
        self.keypress_timeout = 1
        self.fixed_text: np.FixedText = self.add(np.FixedText, relx=55, value="PROGRESS")

        self.links_text: np.TitleText = self.add(np.TitleText, name="Speicherort Links:",
                                                 value=definitions.SKRIPT_PATH + "\\Links")
        self.nextrely += 2
        self.links_text: np.TitleText = self.add(np.TitleText, name="Speicherort Postings:",
                                                 value=definitions.SKRIPT_PATH + "\\Postings")

    def beforeEditing(self):
        self.crawling_thread: threading.Thread = threading.Thread(target=self.parentApp.controller.run_wih_flags,
                                                                  args=(self.parentApp.search_term,
                                                                        sorted(self.parentApp.picked_options),
                                                                        self.parentApp.use_stored_links,
                                                                        self.parentApp.use_stored_postings))
        self.crawling_thread.setDaemon(True)
        self.crawling_thread.start()
        self.nextrely += 5
        self.progress_notify = self.add(np.FixedText, relx=50, color='DANGER', value="Vorgang läuft...")

        self.blink_kill_flag = False
        self.blink_thread: threading.Thread = threading.Thread(target=self.blink)
        self.blink_thread.setDaemon(True)
        self.blink_thread.start()

        finished_thread = threading.Thread(target=self.finished_message)
        finished_thread.start()

        managing_thread: threading.Thread = threading.Thread(target=self.manage_threads)
        managing_thread.setDaemon(True)
        managing_thread.start()

    def finished_message(self):
        while not self.blink_kill_flag:
            time.sleep(1)
        self.progress_notify.color = 'GOOD'
        self.progress_notify.relx = 40
        self.progress_notify.value = 'Prozess erfolgreich abgeschlossen!'
        self.progress_notify.update()

    def manage_threads(self):
        while self.crawling_thread.isAlive():
            time.sleep(1)
        self.blink_kill_flag = True

    def blink(self):
        while not self.blink_kill_flag:
            self.progress_notify.color = 'CAUTION'
            self.progress_notify.update()
            time.sleep(0.7)
            self.progress_notify.color = 'DANGER'
            self.progress_notify.update()
            time.sleep(0.7)


if __name__ == '__main__':
    TestApp = App().run()
