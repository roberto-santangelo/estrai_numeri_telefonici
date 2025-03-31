import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import re
import time
from docx import Document
from docx.shared import Inches

comune = "Campobasso"
indirizzi = [
    "Via De Sanctis 1",
    "Via De Sanctis 11",
    "Via De Sanctis 13",
    "Via De Sanctis 15",
    "Via Vico 31",
    "Via Vico 35",
    "Via Galanti 2",
    "Via Galanti 4",
]

indirizzi = [
    "Via Toscana 22",
    "Via Toscana 30",
    "Via Toscana 46",
]

# ESEMPIO PARTE DI CODICE PAGINE BIANCHE DI CUI FARE IL WEB SCRAPING
"""
<section class="list-element list-element--free" data-user="frls-54475848">
    <div class="list-element__content">
        <div class="list-element__header d-flex">
            <div class="d-flex align-items-center ml-auto"> </div>
        </div>
        <div class="d-flex position-relative justify-content-between">
            <div class="ln-3">
                <h2 class="list-element__title ln-3 org fn"><a
                        href="https://www.paginebianche.it/torino/fiorenzo-canavesio.dhabgdffbc"
                        title="Canavesio Fiorenzo" class="shinystat_ssxl" data-pag="Rgs"
                        data-tr="listing-search-itm-rag" rel="follow">Canavesio Fiorenzo<span
                            class="list-element__expand"> </span></a></h2>
                <div>
                    <div class="list-element__address adr"><span><span data-tr="listing-search-itm-adr"><span
                                    class="street-address">Via Roma 10 - </span><span>10121</span> <span
                                    class="locality">Torino</span><span> (TO)</span></span></span></div>
                </div>
            </div>
        </div>
        <div class="list-element__footer">
            <div class="d-flex flex-wrap mt-10">
                <div class="phone-numbers phone-numbers--listing d-md-block d-none" data-nosnippet="true"><a
                        data-pag="mostra telefono" href="javascript:void(0);" rel="nofollow"
                        class="phone-numbers__cloak btn shinystat_ssxl js-toggle"><span class="icon icon--tel text-13">
                        </span>
                        <div class="btn__label">TELEFONO</div>
                    </a><a data-controls="#otherPhoneNumbers" href="javascript:void(0);" rel="nofollow"
                        class="phone-numbers__main btn hidden js-toggle">
                        <div class="icon icon--tel"> </div>
                        <div class="btn__label tel">370 1635512</div>
                    </a></div><a rel="nofollow" class="phone-number-call list-element__cta btn d-md-none shinystat_ssxl"
                    data-pag="CHIAMATA" href="tel:370 1635512"><span class="icon icon--tel"> </span>
                    <div class="btn__label">CHIAMA</div>
                </a>
            </div>
        </div>
    </div>
</section>
"""
# ESEMPIO PARTE DI CODICE INELENCO DI CUI FARE IL WEB SCRAPING
"""
<tr>
    <td height=20 class="cerca" bgcolor='#FFFFFF' id='risultati'>
        <a href="/?dir=vedi&id=10969936-privati&nome=Sandrone Rosanna ">
            Sandrone Rosanna
        </a>
    </td>
</tr>
<tr>
    <td height=20 class="dativ" bgcolor='#FFFFFF' id='risultati'>Telefono 0119925118</td>
</tr>
<tr>
    <td bgcolor='#FFFFFF' id='risultati' height=20 class="dati">Via Roma, 6</td>
</tr>
<tr>
    <td height=20 bgcolor='#FFFFFF' id='risultati' class="dati"><b>Comune</b> Mombello Di Torino</td>
</tr>
<tr>
    <td height=20 bgcolor='#FFFFFF' id='risultati' class="dati"><b>Provincia</b> (TO)</td>
</tr>
<tr>
    <td height=20 bgcolor='#FFFFFF' id='risultati' class="dati"><b>CAP</b> 10020</td>
</tr>
"""


elenco_numeri = set()  # Set per evitare duplicati più efficientemente
numeri_di_telefono = defaultdict(list)  # Dizionario con i risultati

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def pulisci_numero(numero):
    """Rimuove spazi e caratteri speciali, lasciando solo le cifre."""
    return re.sub(r"\D", "", numero)  # Rimuove tutto tranne i numeri


n = 0
total_results = 0  # Inizializza la variabile per evitare ReferenceError

for ind in indirizzi:
    indirizzo_encoded = requests.utils.quote(ind)

    # --- Pagine Bianche ---
    nome = via = telefono = località = None
    url = f"https://www.paginebianche.it/cerca-da-indirizzo?dv={comune.replace(' ', '%20')}%20{indirizzo_encoded}"
    print(url)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        elementi = soup.find_all("h2", class_="list-element__title")

        for elem in elementi:
            nome = elem.get_text(strip=True) or "Nome non disponibile"

            # Estrazione indirizzo
            indirizzo_tag = elem.find_next("div", class_="list-element__address")
            if indirizzo_tag:
                spans = indirizzo_tag.find_all("span")
                via_completa = (
                    spans[0].get_text() if len(spans) > 0 else "Indirizzo non trovato"
                )
                via_completa = via_completa.split(sep="-")
                via = via_completa[0].strip()
                località = via_completa[1].strip()
            else:
                via, località = "Indirizzo non trovato", "Località non trovata"

            # Estrazione telefono
            telefono_tag = elem.find_next("a", class_="phone-numbers__main")
            telefono = (
                pulisci_numero(telefono_tag.get_text(strip=True))
                if telefono_tag
                else "Telefono non trovato"
            )

            if (
                telefono not in elenco_numeri and telefono.isdigit()
            ):  # Evita numeri errati
                elenco_numeri.add(telefono)
                numeri_di_telefono["PAGINE BIANCHE"].append(
                    {
                        "Nome": nome,
                        "Indirizzo": via,
                        "Telefono": telefono,
                        "Località": località,
                    }
                )
    else:
        print(f"Errore {response.status_code} nell'accesso a {url}")

    # --- InElenco ---
    nome = via = telefono = località = None
    pagine = 1
    da = 0
    while da <= (pagine * 10):  # CICLO PER CONTROLLARE TUTTE LE PAGINE
        url = f"https://mobile.inelenco.com/?dir=cerca&nome=&comune={comune}&provincia=&indirizzo={ind.replace(' ', '+')}&telefono=&da={da}"
        print(url)
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # Trova gli elementi tr che contengono le informazioni degli utenti
            elementi = [
                tr
                for tr in soup.find_all("tr")
                if tr.find("td", class_="cerca", bgcolor="#FFFFFF")
            ]

            for elem in elementi:
                nome = elem.get_text(strip=True)
                if re.match(r"^Elenco telefonico", nome) or re.match(
                    r"^La ricerca -", nome
                ):
                    continue  # SALTO SE NON VALIDO

                tag = elem.find_next("tr")
                if tag:
                    elemento_tag = tag.find("td", class_="dativ")
                telefono = pulisci_numero(elemento_tag.get_text(strip=True))

                if (
                    telefono not in elenco_numeri and telefono.isdigit()
                ):  # Evita numeri errati
                    elenco_numeri.add(telefono)
                    numeri_di_telefono["INELENCO"].append(
                        {
                            "Nome": nome,
                            "Indirizzo": via,
                            "Telefono": telefono,
                            "Località": località,
                        }
                    )

            if da == 0:  # CONTROLLO IL NUMERO DI PAGINE UNA VOLTA SOLA
                # CONTROLLO SE CI SONO ALTRE PAGINE DI CUI ESTRARRE I NUMERI
                tag_risultati = soup.find("td", id="risultati")
                if tag_risultati:
                    match = re.search(r"de (\d+)", tag_risultati.get_text())
                    if match:
                        total_results = int(match.group(1))
                pagine = total_results // 10

        else:
            print(f"Errore {response.status_code} nell'accesso a {url}")

        da += 10  # VADO ALLA PAGINA SUCCESSIVA
        # time.sleep(0.1)  # Pausa di 1 secondo tra le richieste


# --- Stampa risultati ---
if numeri_di_telefono:
    document = Document()
    for sito, contatti in numeri_di_telefono.items():
        document.add_paragraph(f"{sito}")
        document.add_paragraph(f"{"-" * 30}")
        for item in contatti:
            print(sito)
            print(f"Nome: {item['Nome']}")
            print(f"Indirizzo: {item['Indirizzo']}")
            print(f"Telefono: {item['Telefono']}")
            print(f"Località: {item['Località']}")
            print("")

            document.add_paragraph(f"{item['Nome']}")
            document.add_paragraph(f"{item['Indirizzo']}")
            document.add_paragraph(f"{item['Telefono']}")
            document.add_paragraph(f"{item['Località']}")
            document.add_paragraph(f"")

document.save("contatti.docx")
print("")
