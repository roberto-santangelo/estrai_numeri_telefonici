import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import re
import time
import docx

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
if False:
    indirizzi = []
    comune = input("INSERISCI IL COMUNE/CITTA' DI CUI VUOI CERCARE GLI INDIRIZZI: ")
    indirizzo = None
    i = 1
    print(
        "INSERISCI UN INDIRIZZO ALLA VOLTA, QUANDO HAI FINITO LASCIA IL CAMPO DI INDIRIZZO VUOTO E PREMI INVIO"
    )
    while indirizzo != "":
        indirizzo = input(f"INSERISCI IL {i}° INDIRIZZO: ")
        indirizzi.append(indirizzo)
        i += 1
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

            cap, comune, provincia = località.split(" ")
            match = re.search(r"\((.*?)\)", provincia)
            provincia = match.group(1)
            località = f"{cap} {comune} {provincia}"

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

                tag = elem.find_next("tr")  # TELEFONO
                if tag:
                    elemento_tag = tag.find("td", class_="dativ")
                telefono = pulisci_numero(elemento_tag.get_text(strip=True))

                tag = tag.find_next("tr")  # VIA
                if tag:
                    elemento_tag = tag.find("td", class_="dati")
                via = elemento_tag.get_text(strip=True)

                # comune, provincia, cap
                tag = tag.find_next("tr")  # VIA
                if tag:
                    elemento_tag = tag.find("td", class_="dati")
                comune = elemento_tag.contents[-1].strip()

                tag = tag.find_next("tr")  # VIA
                if tag:
                    elemento_tag = tag.find("td", class_="dati")
                provincia = elemento_tag.contents[-1].strip()
                match = re.search(r"\((.*?)\)", provincia)
                if match:
                    provincia = match.group(1)

                tag = tag.find_next("tr")  # VIA
                if tag:
                    elemento_tag = tag.find("td", class_="dati")
                cap = elemento_tag.contents[-1].strip()

                if (
                    telefono not in elenco_numeri and telefono.isdigit()
                ):  # Evita numeri errati
                    elenco_numeri.add(telefono)
                    numeri_di_telefono["INELENCO"].append(
                        {
                            "Nome": nome,
                            "Indirizzo": via,
                            "Telefono": telefono,
                            "Località": f"{cap} {comune} {provincia}",
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

# CERCO IL PREFISSO
url = f"https://www.nonsolocap.it/cap?k={comune}"
print(url)
response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    prefisso = soup.find("td", class_="d-none d-md-table-cell")
    prefisso = prefisso.get_text(strip=True)

# --- Stampa risultati ---
if numeri_di_telefono:
    document = docx.Document()
    h1 = document.add_heading(f"CONTATTI TERRITORIO - {comune.upper()}\n")

    for sito, contatti in numeri_di_telefono.items():
        paragrafo_sito = document.add_paragraph(f"{sito}\n{'-' * 30}")
        for item in contatti:
            print(sito)
            print(f"Nome: {item['Nome']}")
            print(f"Indirizzo: {item['Indirizzo']}")
            print(f"Località: {item['Località']}")
            print(f"Telefono: {item['Telefono'].replace(prefisso, f'{prefisso} ')}")
            print("")

            document.add_paragraph(f"{item['Nome']}")
            document.add_paragraph(f"{item['Indirizzo']}")
            document.add_paragraph(f"{item['Località']}")
            document.add_paragraph(
                f"{item['Telefono'].replace(prefisso, f'{prefisso} ')}"
            )

            document.add_paragraph(f"")

print(
    f"NUMERO DI CONTATTI TROVATI: {sum([len(v) for v in numeri_di_telefono.values()])}"
)

document.save("contatti.docx")
