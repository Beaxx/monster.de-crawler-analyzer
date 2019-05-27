Monster.de Crawler & Analyzer
===

Dependencies
---
* requests (Handling Requests to Server)
* lxml (Parsing HTML)
* beautifulsoup 4 (Parsing HTML)
* npyscreen (Console based UI)
* curses (windows: [Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/#curses))
* whoosh (Information Retrieval)
* regex (pip install regex, not the python included one)

Features
---
* Gathers deep links of job postings from [monster.de](https://monster.de) for a given search term
* Saves links to file
* Parses and stores the postings content
* Correlation analysis of tokens inside of Postings
* Display of analysis results

How to Run
---
Start UserDialog.py

__Important:__ Because most IDE's reroute stdout to the build in console which npyscreen prohibits this
program must be launches via comandline and not from inside an IDE.
