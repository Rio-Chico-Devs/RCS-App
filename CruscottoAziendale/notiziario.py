#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RCS - Notiziario di settore (modulo opzionale del Cruscotto)

Raccoglie dal web notizie mirate su fibra di carbonio, materiali compositi,
i fornitori e i materiali effettivamente usati dall'azienda (letti dal
database in SOLA LETTURA), le sintetizza in italiano in stile "telegiornale"
e salva il risultato in 'notiziario_ultimo.json', che il report HTML mostra
automaticamente alla generazione successiva.

Richiede:
  - il pacchetto 'anthropic'  ->  pip install anthropic
  - una chiave API nella variabile d'ambiente ANTHROPIC_API_KEY

Uso:
    set ANTHROPIC_API_KEY=la-tua-chiave        (Windows)
    python notiziario.py
    python notiziario.py --quante 6            (numero di notizie, default 5)

Il modello usa la ricerca web e cita sempre le fonti. I numeri aziendali NON
vengono inviati: al modello si passano solo i nomi generici di materiali e
fornitori per mirare la ricerca; nessun prezzo, cliente o importo lascia il PC.
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime

import config_db  # modulo locale: DB e chiave API dal config.json di questo strumento

BASE_DIR = config_db.base_dir()
OUTPUT_PATH = os.path.join(BASE_DIR, "notiziario_ultimo.json")
MODELLO = "claude-opus-4-8"


def trova_db_path():
    return config_db.trova_db_path()


def contesto_azienda(db_path):
    """Ritorna (materiali, fornitori): solo nomi generici, nessun dato sensibile."""
    materiali, fornitori = [], []
    if not db_path or not os.path.exists(db_path):
        return materiali, fornitori
    try:
        uri = "file:{}?mode=ro".format(db_path.replace("\\", "/"))
        conn = sqlite3.connect(uri, uri=True)
        cur = conn.cursor()
        cur.execute("SELECT nome FROM materiali ORDER BY nome")
        materiali = [r[0] for r in cur.fetchall() if r[0]]
        try:
            cur.execute("SELECT nome FROM fornitori ORDER BY nome")
            fornitori = [r[0] for r in cur.fetchall() if r[0]]
        except sqlite3.Error:
            pass
        conn.close()
    except sqlite3.Error:
        pass
    return materiali, fornitori


def costruisci_prompt(materiali, fornitori, quante):
    elenco_mat = ", ".join(materiali[:40]) if materiali else "(non disponibili)"
    elenco_forn = ", ".join(fornitori) if fornitori else "(non disponibili)"
    return f"""Sei l'analista di settore di un'azienda italiana che produce manufatti in
fibra di carbonio e materiali compositi (taglio, avvolgimento, rettifica di tubi e
componenti). Codici materiali usati in produzione: {elenco_mat}.
Fornitori principali: {elenco_forn}.

Cerca sul web notizie RECENTI e VERIFICABILI (ultimi 1-3 mesi quando possibile) che
possano avere un impatto concreto su quest'azienda. Concentrati su:
- prezzo e disponibilita' della fibra di carbonio e dei precursori (PAN, acrilonitrile);
- annunci dei grandi produttori (Toray, Teijin, Mitsubishi Chemical, Hexcel, SGL Carbon,
  Solvay) su capacita', prezzi, chiusure o espansioni;
- domanda nei settori che usano compositi (aerospazio, automotive, nautica, eolico, sport);
- dazi, normative UE, costi energetici che toccano la filiera dei compositi in Europa e Italia.

Devi produrre esattamente {quante} notizie, le piu' rilevanti. Per ognuna:
1. un titolo breve e chiaro in italiano;
2. una sintesi di 2-3 frasi in italiano semplice e diretto, con i numeri se ci sono;
3. "perche' vi riguarda": una frase concreta sull'impatto per un trasformatore di
   fibra di carbonio (es. pressione sui prezzi d'acquisto, opportunita' di mercato);
4. la fonte: nome della testata e URL preciso dell'articolo.

Usa la ricerca web e basa OGNI notizia su una fonte reale che hai trovato: non inventare
nulla. Se non trovi abbastanza notizie recenti e affidabili, restituiscine meno.

Dopo aver cercato, scrivi alla FINE un unico blocco di codice JSON (racchiuso tra ```json
e ```) con questa struttura esatta, e NIENTE testo dopo il blocco:

```json
{{
  "notizie": [
    {{
      "titolo": "...",
      "sintesi": "...",
      "perche_rilevante": "...",
      "fonte_nome": "...",
      "fonte_url": "https://..."
    }}
  ],
  "commento": "Una frase di sintesi generale sul quadro del settore in questo momento."
}}
```"""


def estrai_json(testo):
    """Estrae l'ultimo blocco ```json ... ``` (o il primo oggetto JSON) dal testo."""
    blocchi = re.findall(r"```json\s*(\{.*?\})\s*```", testo, re.DOTALL)
    if not blocchi:
        blocchi = re.findall(r"```\s*(\{.*?\})\s*```", testo, re.DOTALL)
    if not blocchi:
        m = re.search(r"(\{.*\})", testo, re.DOTALL)
        blocchi = [m.group(1)] if m else []
    for blocco in reversed(blocchi):
        try:
            return json.loads(blocco)
        except json.JSONDecodeError:
            continue
    return None


def raccogli(quante):
    try:
        import anthropic
    except ImportError:
        sys.exit("Pacchetto 'anthropic' non installato. Esegui:  pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY") or config_db.carica_config().get("anthropic_api_key")
    if not api_key:
        sys.exit("Chiave API non trovata. Imposta 'anthropic_api_key' nel file config.json "
                 "accanto al programma, oppure la variabile ANTHROPIC_API_KEY (vedi README.md).")

    client = anthropic.Anthropic(api_key=api_key)
    db_path = trova_db_path()
    materiali, fornitori = contesto_azienda(db_path)
    print("Contesto: {} materiali, {} fornitori. Avvio ricerca web...".format(
        len(materiali), len(fornitori)))

    tools = [{"type": "web_search_20260209", "name": "web_search"}]
    messages = [{"role": "user", "content": costruisci_prompt(materiali, fornitori, quante)}]

    # Ciclo per gestire le pause dei tool server-side (pause_turn).
    risposta = None
    for _ in range(6):
        risposta = client.messages.create(
            model=MODELLO,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            tools=tools,
            messages=messages,
        )
        if risposta.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": risposta.content})
            continue
        break

    if risposta is not None and risposta.stop_reason == "refusal":
        sys.exit("La richiesta e' stata rifiutata dal modello per motivi di sicurezza.")

    testo = "".join(b.text for b in risposta.content if getattr(b, "type", "") == "text")
    dati = estrai_json(testo)
    if not dati or "notizie" not in dati:
        sys.exit("Non sono riuscito a interpretare la risposta del modello. "
                 "Riprova; se persiste, controlla la connessione o la chiave API.")

    dati["generato_il"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    dati["modello"] = MODELLO
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, indent=2)

    print("Notiziario salvato: {}".format(OUTPUT_PATH))
    print("  Notizie raccolte: {}".format(len(dati.get("notizie", []))))
    print("  Verra' mostrato nel report alla prossima esecuzione di cruscotto.py")
    for n in dati.get("notizie", []):
        print("   - {}".format(n.get("titolo", "")))


def main():
    parser = argparse.ArgumentParser(description="Notiziario di settore RCS (ricerca web con fonti)")
    parser.add_argument("--quante", type=int, default=5, help="numero di notizie (default 5)")
    args = parser.parse_args()
    raccogli(max(1, min(args.quante, 10)))


if __name__ == "__main__":
    main()
