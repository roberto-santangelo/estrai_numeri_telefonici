import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import re
import time

comune = "Campobasso"
indirizzi = ["Via Toscana 22"]


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


def estraiDaInelenco(soup, elenco_numeri):
    # Inizializza la lista dei risultati
    numeri_di_telefono = defaultdict(list)

    # Trova gli elementi tr che contengono le informazioni degli utenti
    elementi = [
        tr
        for tr in soup.find_all("tr")
        if tr.find("td", class_="cerca", bgcolor="#FFFFFF")
    ]

    for elem in elementi:
        nome = indirizzo = telefono = località = None

        # Estrai nome
        nome = elem.get_text(strip=True) or None

        # Estrazione telefono
        telefono_tag = elem.find_next("td", class_="dativ")
        telefono = (
            pulisci_numero(telefono_tag.get_text(strip=True)) if telefono_tag else None
        )

        # Trova indirizzo, comune, provincia e CAP
        indirizzo_tag = elem.find_next("td", class_="dati")
        indirizzo = (
            indirizzo_tag.get_text(strip=True)
            if indirizzo_tag
            else "Indirizzo non trovato"
        )

        # Cerca il comune (presente in un tag td con la parola "Comune")
        comune_tag = elem.find_next(
            "td", class_="dati", string=lambda x: x and "Comune" in x
        )
        comune = (
            comune_tag.get_text(strip=True).replace("Comune", "").strip()
            if comune_tag
            else "Comune non trovato"
        )

        # Cerca la provincia (presente in un tag td con la parola "Provincia")
        provincia_tag = elem.find_next(
            "td", class_="dati", string=lambda x: x and "Provincia" in x
        )
        provincia = (
            provincia_tag.get_text(strip=True).replace("Provincia", "").strip()
            if provincia_tag
            else "Provincia non trovata"
        )

        # Cerca il CAP (presente in un tag td con la parola "CAP")
        cap_tag = elem.find_next("td", class_="dati", string=lambda x: x and "CAP" in x)
        cap = (
            cap_tag.get_text(strip=True).replace("CAP", "").strip()
            if cap_tag
            else "CAP non trovato"
        )

        # Combina i dati per la località
        località = f"{cap} {comune} {provincia}".strip()

        # Aggiungi i numeri di telefono se non sono già stati estratti
        if telefono and telefono not in elenco_numeri and telefono.isdigit():
            elenco_numeri.add(telefono)
            numeri_di_telefono["INELENCO"].append(
                {
                    "Nome": nome,
                    "Indirizzo": indirizzo,
                    "Telefono": telefono,
                    "Località": località,
                }
            )

    return numeri_di_telefono, elenco_numeri


def pulisci_numero(numero):
    """Rimuove spazi e caratteri speciali, lasciando solo le cifre."""
    return re.sub(r"\D", "", numero)  # Rimuove tutto tranne i numeri


n = 0
total_results = 0  # Inizializza la variabile per evitare ReferenceError

for ind in indirizzi:
    indirizzo_encoded = requests.utils.quote(ind)

    # --- Pagine Bianche ---
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
    url = f"https://inelenco.com/?dir=cerca&nome=&comune={comune}&provincia=&indirizzo={ind.replace(' ', '+')}&telefono="
    print(url)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        num_parziali, elenco_numeri = estraiDaInelenco(soup, elenco_numeri)
        numeri_di_telefono.update(num_parziali)

        # CONTROLLO SE CI SONO ALTRE PAGINE DI CUI ESTRARRE I NUMERI
        tag_risultati = soup.find("td", id="risultati")
        if tag_risultati:
            match = re.search(r"de (\d+)", tag_risultati.get_text())
            if match:
                total_results = int(match.group(1))
        pagine = total_results // 10

        # VADO AD ESTRARRE ANCHE LE ALTRE PAGINE
        for i in range(1, pagine + 1):
            da = i * 10
            url = f"https://inelenco.com/?dir=cerca&nome=&comune={comune}&provincia=&indirizzo={ind.replace(' ', '+')}&telefono=&da={da}"
            print(url)
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

            num_parziali, elenco_numeri = estraiDaInelenco(soup, elenco_numeri)
            numeri_di_telefono.update(num_parziali)

    else:
        print(f"Errore {response.status_code} nell'accesso a {url}")

    n += 1
    print(f"{n}/{len(indirizzi)} INDIRIZZI ESTRATTI...")

    # Delay tra le richieste
    time.sleep(1)  # Pausa di 1 secondo tra le richieste

print("")  # RIGA VUOTA

# --- Stampa risultati ---
if numeri_di_telefono:
    for sito, contatti in numeri_di_telefono.items():
        for item in contatti:
            print(sito)
            print(f"Nome: {item['Nome']}")
            print(f"Indirizzo: {item['Indirizzo']}")
            print(f"Telefono: {item['Telefono']}")
            print(f"Località: {item['Località']}")
            print("")
