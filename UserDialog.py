import npyscreen as np
from MainController import MainController
import itertools
import definitions

menutext = {
    "title": "Monster.de Crawler V0.1",
    "default_search_term": "digital change management",
    "disclaimer": "### Bei jeder Ausführung des Programs gilt zu "
                  "bedenken, dass mehrere hundert Anfragen an den Server gestellt werde können. ###",
    "links_saved_to": "Links werden in das Verzeichnis {0} gelegt.\n",
    "postings_saved_to": "Postings werden in das Verzeichnis {0} gelegt.\n",

    "downloaded_content_available": "Für den eingegebenen Suchbegriff sind heruntergeladene Daten vorhanden. "
                                    "Sollen diese verwendet werden, oder sollen die Daten neu angefragt werden?",
    "posting_intro": "Im nächsten Schritt werden die Job Postings für die gefundenen Links heruntergeladen",
    "link_collection_in_progress": "Linksammlung läuft...(0 bis 3 Minuten)",
    "invalid_input": "",
    "termination_no_entry": "Ohne Abruf kann das Program nicht fortgesetzt weren. Wenn Sie das Programm neu "
                            "starten und einen spezifischeren Suchbegriff verwenden, der weniger Suchergebnisse "
                            "liefert, reduziert sich die Bearbeitungsdauer.",
    "old_new": "[alt/neu]: ",
    "yes_no": "[Y/any]: ",
    "download_postings?": "Sollen die {0} gefundenen Angebote abgerufen werden? Diese Prozess dauert ca. {1} Minuten",
    "posting_collection_in_progress": "Job Angebote werden abgerufen, dies wird ca. {0} Minuten dauern.",
    "postin_collection_completed": "\nAbruf abgeschlossen",
    "postings_saved": "\nEine Textrepresentation der Job-Postings wurde in das Verzeichnis {0} gelegt.",
    "saved_data_may_be_available": ""
}


class App(np.NPSAppManaged):
    done_notice = ""

    def onStart(self):
        self.controller: MainController = MainController()
        self.addForm('MAIN', MainForm, name=menutext["title"], draw_line_at=28)
        self.addForm('Progress', ProgressForm, name=menutext["title"], autowrap=True)


class MainForm(np.SplitForm):
    link_avail_checked = False
    posting_avail_checked = False
    use_stored_links = False
    use_stored_postings = False

    def create(self):
        self.search_term: np.TitleText = self.add(np.TitleText,
                                                  name='Suchbegriff', value=menutext["default_search_term"],
                                                  color='DANGER')
        self.options: np.TitleMultiSelect = self.add(np.TitleMultiSelect,
                                                     scroll_exit=True, max_height=4, name='Optionen',
                                                     values=['Links Abrufen', 'Postings Abrufen', 'Analyse'],
                                                     value=[0, 1])

    def afterEditing(self):
        if self.check_inputs() == 1:
            np.notify_confirm("Suchfeld fehler", "Fehler", editw=1)
        if self.check_inputs() == 2:
            np.notify_confirm("Keine Optionen eingegeben", "Fehler", editw=1)
        if self.check_inputs() == 3:
            np.notify_confirm("Reihenfolge Optionen falsch", "Fehler", editw=1)
        if self.check_inputs() == 4 and not self.link_avail_checked:
            self.use_stored_links: bool = np.notify_yes_no("Saved links avail", "Achtung!", editw=1)
            self.link_avail_checked = True
        if self.check_inputs() == 5 and not self.posting_avail_checked:
            self.use_stored_postings: bool = np.notify_yes_no("Saved Postings avail", "Achtung!", editw=1)
            self.posting_avail_checked = True

        self.parentApp.setNextForm('Progress')

        self.parentApp.done_notice = self.parentApp.controller.run_wih_flags(self.search_term.value.lower(),
                                                                             sorted(self.options.value),
                                                                             self.use_stored_links,
                                                                             self.use_stored_postings)

    def check_inputs(self):
        if self.search_term.value is None or len(self.search_term.value) < 5:
            return 1
        if len(self.options.value) == 0:
            return 2
        elif sorted(self.options.value) != [0, 1, 2] \
                and sorted(self.options.value) != [0, 1] \
                and sorted(self.options.value) != [0]:
            return 3
        if self.parentApp.controller.file_handler.deep_link_file_is_available(self.search_term.value.lower()):
            return 4
        if sorted(self.options.value)[1] == 1 and \
                self.parentApp.controller.file_handler.pickled_posting_file_is_availabe(self.search_term.value.lower()):
            return 5


class ProgressForm(np.Form):
    def create(self):
        self.fixed_text: np.FixedText = self.add(np.FixedText, relx=55, value="PROGRESS")
        self.links_text: np.FixedText = self.add(np.FixedText,
                                                 value=menutext.get("links_saved_to").format(
                                                     definitions.SKRIPT_PATH + "\\Links"))
        self.postings_text: np.FixedText = self.add(np.FixedText,
                                                    value=menutext.get("postings_saved_to").format(
                                                        definitions.SKRIPT_PATH + "\\Postings"))
        self.done_message= self.add(np.Textfield, value=self.parentApp.done_notice)


if __name__ == '__main__':
    TestApp = App().run()
