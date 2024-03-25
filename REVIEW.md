# Code review met Joël van Ingen
### Thijs Kooijman
### 11896124

---

### Verbeter punten:

1.	Aan requirements : requests en werkzeug en dateutil // DONE
2.	Imports aanpassen // DONE
3.	User_id = session id erboven zetten bij main? // DONE
4.  Verander order_number naar order_id in models.py // NOT DONE
5.	Import from models import *, voor db in helpers // NOT NEEDED IN THE END
6.	In main postcodes/ barcodes buiten de ifstatements!! Kan bij de andere /directions ook!! // DONE
7.	If else statement can korter door else weg te halen, if naar boven toe.// DONE
8.	Delete scraping.py and miscelaneous from git repository // DONE
extra: DOWNLOAD PYCHARM, niet de proffesional, JETBRAINS site? // not DONE

---

Hier heb ik een aantal dingen snel kunnen opschrijven om te kunnen verbeteren. Ze zijn best kryptisch maar ik begrijp goed wat ermee moet gebeuren.
Joel heeft mij goed kunnen helpen met veel verbeterpunten. Ik heb dat bij hem ook proberen te doen. Echter heeft Joel een ontzettende nette code al waar weinig verbetering in te zien was. Hier en daar waren er wel een paar kleine dingen waar hij op kon letten zoals zijn requirements.txt.

Het verbeteren van al deze punten lukte wel degelijk. Bij een paar heb ik het juist net overal gedaan, zoals by nummer 6, omdat dat overbodig is als het stuk code relatief kort is. Verder kwam ik een bug tegen met mijn date_arrival bij add_order. Heb een apology redirection ervoor gemaakt m.b.v chatgpt. Verder had ik nog wat onnodige print statements eruit gehaald die ik als testjes had gerbuikt.

---

Hier zijn bij sommige problemen voorbeelden en overwegingen:

4. Hier gaat het puur om de benaming van mijn order model. Joel zei dat een order_id een betere benoeming zou zijn. Ik begrijp dat enigzins wel maar omdat het om order gaan vind ik order_number een betere benaming. Voor en bij veel post bedrijven gaat het over een order number en niet id, ook al zou het wel kunnen.

5. Dit had te maken met een extra helpers functie die ik niet wil maken. Ik wil dit niet, niet uit luiheid maar omdat ik niet wil riskeren dat mijn add_order en ass_trackandtrace niet zullen werken. Het gaat dus om een functie dat de db.session.commit en queries daar maakt. Het is ook een beetje lastig.

7. Hier gaat het om een hele lange if else statement waarbij "POST" and "GET" wordt gebruikt. In finance hadden wij het zo geleerd maar de oplossing van Joel is veel beter. Een if-statement ervoor plaatsen werkt goed. Ik heb het bij /about en update order niet gedaan omdat die  heel kort zijn.



