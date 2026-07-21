# Handoff — Cruscotto Aziendale RCS

Questo file serve a un'altra istanza di Claude (o a chiunque riprenda il
progetto senza il contesto della conversazione originale) per continuare lo
sviluppo **mantenendo esattamente lo stesso stile grafico e la stessa
architettura** già stabiliti. Non è un readme utente (quello è `README.md`
nella stessa cartella) — è un documento tecnico per chi scrive codice qui.

Leggilo tutto prima di toccare `cruscotto.py`. I dettagli sotto (colori, nomi
di classi, nomi di funzioni) sono stati riletti dal codice reale, non a
memoria — trattali come verità di base.

---

## 1. Cos'è, e cosa NON deve mai diventare

Un generatore di report HTML **statico e autosufficiente**: legge il
database SQLite del gestionale RCS in **sola lettura**, calcola indicatori e
scrive un unico file HTML (grafici + testo) che si apre nel browser. Nessun
server, nessun build step, nessuna dipendenza pesante.

Vincoli non negoziabili:

- **Sola lettura sul database, sempre.** Ogni connessione passa da
  `config_db.apri_db_sola_lettura()` (`sqlite3.connect(..., uri=True)` con
  `mode=ro`). Non aggiungere mai una `INSERT`/`UPDATE`/`DELETE` su questo DB.
- **Progetto indipendente dal gestionale.** Non importare né modificare nulla
  sotto `ui/`, `database/`, `models/`, `main.py` (la cartella principale del
  repository, un livello sopra `CruscottoAziendale/`). Il Cruscotto trova il
  database solo tramite `config.json` (vedi `config_db.py`), mai per path
  relativo alla cartella del gestionale.
- **Zero dipendenze Python oltre la libreria standard** (`sqlite3`, `json`,
  `os`, `sys`, `webbrowser`, `urllib.request`, `tkinter`). Deve restare
  compilabile con PyInstaller in un `.exe` singolo (vedi
  `crea_eseguibile.bat`) senza sorprese.
- **Niente framework JS** (React/Vue/build step). L'output è un file HTML
  con CSS e JavaScript vanilla inline. Se un domani serve davvero altro,
  fermati e chiedi conferma esplicita all'utente prima di introdurlo — è un
  cambio di filosofia, non un dettaglio.
- **Deve restare utilizzabile offline** dopo il primo avvio (Chart.js viene
  messo in cache locale in `assets/`, vedi §4).

---

## 2. Stato attuale (riletto riga per riga da `cruscotto.py`, non a memoria — se il file è cambiato da quando questo handoff è stato scritto, ri-verifica prima di fidarti dei numeri di riga)

### File della cartella

| File | Righe | Ruolo |
|---|---|---|
| `cruscotto.py` | ~980 | Genera il report HTML. Contiene: funzioni `estrai_*()` (lettura DB), `HTML_TEMPLATE` (Python `string.Template` con dentro CSS + JS), `genera()`, `main()`. |
| `config_db.py` | ~145 | Risoluzione del percorso database: `config.json` → selettore file grafico (tkinter) → validazione tabelle attese. Sola lettura garantita qui. |
| `notiziario.py` | ~190 | Modulo opzionale: raccoglie notizie di settore dal web con Claude + web search, salva `notiziario_ultimo.json` che il report legge se presente. |
| `README.md` | — | Istruzioni utente finali (italiano semplice). Aggiornalo se cambi il comportamento visibile. |
| `config.example.json` | — | Modello di configurazione (mai committare `config.json` reale: è in `.gitignore`). |
| `Cruscotto.bat`, `Notiziario.bat`, `crea_eseguibile.bat` | — | Lanciatori Windows. |

### Cosa mostra oggi il report (sezione per sezione)

1. **Header**: logo testuale "RCS · Cruscotto Aziendale", data generazione, selettore periodo (pill Mese/Trimestre/Anno).
2. **Griglia KPI** (`#grigliaKpi`): 6 schede animate — n. preventivi, valore preventivato, margine medio %, prezzo medio, capitale a magazzino, materiali sotto scorta. Ognuna con delta vs periodo precedente.
3. **"In sintesi"**: tre colonne generate da regole in JS (`disegnaSintesi()`) — Punti di forza / Punti di attenzione / Cambiamenti, in italiano semplice, calcolate dai dati (non testo fisso).
4. **Andamento preventivi**: grafico misto barre+linea (n. preventivi + valore €) per periodo.
5. **Margini** e **Composizione costi**: due grafici affiancati (`.griglia-2`).
6. **Manodopera per fase** (ciambella) e **Materiali più usati** (barre orizzontali) — storico completo, non filtrati per periodo.
7. **Clienti per valore** e **Magazzino: giacenze vs scorta minima** — altri due grafici storico completo.
8. **Tabelle**: ricarico per materiale (vendita vs prezzo fornitore), confronto fornitori (se un materiale ne ha ≥2), ultimi movimenti di magazzino.
9. **Notiziario di settore**: card di notizie con fonte citata, oppure un messaggio che spiega come attivarlo se `notiziario_ultimo.json` non esiste.

### Cosa NON è ancora stato costruito (decisione in sospeso)

**Tracciamento esito preventivo (vinto/perso) e ore reali di lavorazione.**
Oggi il database registra solo il preventivo calcolato, mai se è stato
accettato né quante ore sono state impiegate davvero. Senza questi due dati
non si può calcolare un tasso di conversione reale né un margine vero — è
l'intervento a **più alto ritorno** identificato finora (confermato anche da
ricerca di mercato: la maggior parte delle micro-officine non sa se un
lavoro preso sta davvero guadagnando).

**Decisione già presa dall'utente: NON implementarlo.** Gli è stata posta
esplicitamente la domanda (gestionale vs mini-schermata nel Cruscotto) e ha
risposto "lasciamo stare l'esito del preventivo". Resta descritto qui solo
come nota storica/di contesto — **non riproporre la domanda e non
implementare questa funzione** a meno che sia l'utente stesso a richiederla
di nuovo in futuro. Le due opzioni valutate, per riferimento se dovesse
tornare sull'argomento:

- **Opzione A — nel gestionale**: due colonne in più nella tabella
  `preventivi` (es. `esito` testo, `ore_reali` reale), stesso pattern di
  migrazione additiva già usato in
  `database/db_manager.py::_migrate_database()` (`ALTER TABLE ... ADD COLUMN`
  con default, mai distruttivo).
- **Opzione B — nel Cruscotto stesso**: mini-schermata separata (tkinter o
  form HTML) con salvataggio proprio, associata per ID preventivo. Il
  gestionale resta intoccato, ma il dato si inserisce in due punti diversi.

### Altri interventi già discussi con l'utente, non ancora implementati

Ordina per beneficio/costo quando li affronti, non per ordine di elenco:

- **Simulazione scenario prezzo materiali**: "se il materiale X aumenta del
  15%, quali preventivi/famiglie di prodotto andrebbero rilistinati e di
  quanto". Puro calcolo sui dati già estratti (`estrai_preventivi`,
  `estrai_magazzino`) — nessuna dipendenza nuova.
- **Margine per cliente nel tempo** (serie storica, non solo il totale
  aggregato che c'è oggi in `disegnaSintesi()`).
- Eventuali altre metriche dalla lista "Fase 1" discussa con l'utente
  (stagionalità, concentrazione clienti nel tempo, ecc.) — se non è chiaro
  cosa intendesse, chiedi piuttosto che indovinare.

---

## 3. Sistema di design — replica esatta, non reinterpretazione

L'utente ha chiesto esplicitamente **"stessa grafica soprattutto"**. Questo
non è un tema riadattabile: riusa le variabili e le classi CSS esistenti,
non definirne di nuove per lo stesso concetto (es. non creare un secondo
stile di "card" — usa `.kpi` o `.sezione`/`.blocco-sintesi` a seconda del
caso).

### Palette (variabili CSS in `:root`, cercale in `cruscotto.py`)

```css
--bg: #0d1117;       /* sfondo pagina */
--card: #151c25;      /* sfondo carte/sezioni */
--card2: #1a222d;     /* sfondo carte annidate (es. blocco-sintesi) */
--bordo: #25303d;     /* tutti i bordi 1px */
--testo: #e6edf3;     /* testo principale */
--muto: #8b97a5;      /* testo secondario, etichette, note */
--accento: #f0b429;   /* ambra — CTA, periodo attivo, punti di attenzione */
--teal: #43c6b9;      /* secondario — notiziario, cambiamenti */
--verde: #4ec97b;     /* positivo, punti di forza */
--rosso: #ef6a6a;     /* negativo, allarmi (sotto scorta, margine negativo) */
--blu: #6aa9ef;        /* neutro informativo (n. preventivi, cambiamenti) */
```

Regola semantica già in uso, mantienila: verde = va bene, rosso = attenzione
seria, ambra = attenzione/evidenzia, blu/teal = informativo neutro.

### Tipografia e forma

- Font: `"Segoe UI", system-ui, -apple-system, sans-serif` (nessun font
  esterno da scaricare).
- Numeri tabellari: `font-variant-numeric: tabular-nums` su tutti i valori
  numerici allineati (KPI, celle `.num`) — mantienilo sui nuovi numeri.
  Include anche `€ 12.345` e simili quando sono in tabella o KPI.
- Raggi: 999px (pillole/tag, completamente arrotondati), 14-16px (carte e
  sezioni), 10-12px (elementi annidati più piccoli).
  Non introdurre un quarto valore di raggio senza motivo.
- Sfondo pagina: leggero pattern a righe diagonali incrociate (`repeating-
  linear-gradient` a 45°/-45°, opacità .014) sopra il colore pieno — è
  voluto, dà texture "tecnica" senza disturbare la lettura. Non rimuoverlo
  per "pulizia" senza chiedere.

### Pattern di componenti (nomi di classe esatti da riusare)

- **Sezione**: `<div class="sezione"><h2>Titolo <span class="nota-periodo">...</span></h2>...</div>`.
  Ogni nuova area del report è una `.sezione`, punto. Il piccolo trattino
  ambra prima del titolo (`.sezione h2::before`) è automatico via CSS.
- **Griglia due colonne**: `.griglia-2` per affiancare due grafici/blocchi
  (collassa a una colonna sotto 900px).
- **KPI**: card in `.griglia-kpi` → `.kpi` con `.etichetta`, `.valore`
  (animato in conteggio, vedi `animaNumero()`), `.delta` (`.su`/`.giu`/
  `.neutro` per verde/rosso/grigio con freccia ▲▼—).
- **Sintesi a tre colonne**: `.blocco-sintesi` con modificatore
  `.forza`/`.attenzione`/`.cambi` — icona diversa per tipo via CSS
  (`::before`), non aggiungerla in JS.
- **Tabelle**: markup HTML standard, classi `.num` su `<td>`/`<th>` per
  allineamento a destra dei numeri; `.tag` con modificatore
  `.ok`/`.basso`/`.medio`/`.carico`/`.scarico` per badge colorati inline.
- **Notiziario**: `.notizia` (card con bordo sinistro teal), `.rilevanza`
  (corsivo ambra per "perché vi riguarda"), `.suggerimento` (bordo
  tratteggiato, per messaggi di stato/aiuto quando manca un dato).

### Movimento (motion) — mantieni gli stessi tempi/curve

- **Comparsa sezioni allo scroll**: `IntersectionObserver` aggiunge la
  classe `.visibile` a `.sezione` quando entra nel viewport (soglia 0.08);
  il CSS fa il resto (`opacity`/`translateY`, transizione 0.55s). Ogni
  nuova sezione deve stare dentro questo stesso meccanismo — non serve
  codice aggiuntivo, basta usare la classe `.sezione`.
- **Conteggio numeri KPI**: `animaNumero()` — 750ms, easing cubico
  (`1 - Math.pow(1-f, 3)`, cioè easeOutCubic). Riusala per ogni nuovo
  numero "grande" da mostrare, non inventare un'altra animazione.
- **Grafici Chart.js**: `animation: { duration: 700-800, easing:
  'easeOutQuart' }` impostato in `opzioniBase()` — i nuovi grafici devono
  passare da lì (vedi §5), non configurare Chart.js a mano.

---

## 4. Architettura tecnica (flusso dati)

```
SQLite (sola lettura)
   │  config_db.apri_db_sola_lettura()
   ▼
estrai_preventivi() / estrai_magazzino() / estrai_confronto_fornitori() /
estrai_movimenti() / carica_notiziario()   (in cruscotto.py)
   │  ognuna ritorna list[dict] o dict — dati già puliti (float arrotondati,
   │  stringhe sicure), MAI oggetti sqlite3.Row grezzi
   ▼
dict "dati" assemblato in genera()
   │  json.dumps(dati, ensure_ascii=False).replace("</", "<\\/")
   │  ↑ l'escape di "</" è per sicurezza (evita chiusura prematura del tag
   │    <script> se un nome cliente o materiale contenesse "</script>")
   ▼
HTML_TEMPLATE.substitute(..., JSON_DATI=...)   → stringa HTML completa
   ▼
scritta su disco: report/report_AAAAMMGG_HHMM.html  e  report/ultimo.html
   ▼
nel browser: JS vanilla legge `var DATI = {...}`, aggrega per periodo
(funzioni aggrega()/chiavePeriodo()), disegna KPI/sintesi/grafici/tabelle
```

### Gotcha critico: `HTML_TEMPLATE` è un `string.Template` Python

Il blocco HTML+CSS+JS è dentro un `Template(r"""...""")`. Python sostituisce
`${NOME}` con le variabili passate a `.substitute()`. Questo significa:

- **Ogni `$` letterale nel CSS/JS deve diventare `$$`**, altrimenti
  `Template.substitute()` lo interpreta come inizio di una sostituzione e
  **lancia `KeyError`** (o peggio, sostituisce silenziosamente qualcosa di
  sbagliato se per caso esiste una chiave con quel nome). Nel file attuale
  ci sono già 8 punti con `$$` — se aggiungi testo con un dollaro letterale
  (raro in questo dominio, ma capita in selettori jQuery-style o in testo
  che parla di soldi in un contesto non-`€`), ricordatene.
- Le **parentesi graffe `{` `}`** (CSS, oggetti JS) sono invece innocue per
  `string.Template` — solo il simbolo `$` è speciale. Non confondere questo
  con le f-string Python, che userebbero `{}` come delimitatore: qui non è
  così.
- Il JavaScript nel file usa **solo concatenazione con `+`**, mai
  template-literal con backtick (`` ` ``) — è una scelta deliberata per
  restare leggibile e per non creare ambiguità visiva col `${}` di Python
  Template. Segui la stessa convenzione quando aggiungi JS: niente
  backtick, concatenazione con `+`.

### Chart.js: caricamento e cache

`ottieni_chartjs()` cerca prima `assets/chart.umd.min.js` in cache locale
(se >100KB, per scartare file corrotti/troncati); se assente prova a
scaricarlo da CDN (`jsdelivr`, versione pinnata `4.4.9`) e lo salva in
cache; se anche questo fallisce, il tag `<script>` finale punta al CDN
direttamente nel browser (serve internet in quel momento, ma il resto del
report — numeri e tabelle — resta comunque leggibile, vedi il controllo
`typeof Chart === 'undefined'` in fondo al JS). Non cambiare questa
strategia di degrado: è pensata per un PC che potrebbe non avere internet
al momento della generazione.

---

## 5. Come estendere il progetto (pattern da seguire)

Per aggiungere una nuova metrica/sezione:

1. **Estrazione dati**: nuova funzione `estrai_nome(conn)` in `cruscotto.py`,
   stile identico alle esistenti — query SQL diretta, ritorna `list[dict]`
   con valori già arrotondati (`round(_num(x), 2)`), mai `None` per un
   numero (usa `_num()` che converte `None`/stringhe vuote in `0.0`).
2. Aggiungila al dict `dati` dentro `genera()`.
3. **Markup**: nuovo blocco `.sezione` nell'HTML, stesso schema di intestazione
   (`<h2>Titolo <span class="nota-periodo">...</span></h2>`).
4. **JS**: se il dato è per-periodo (mese/trimestre/anno), estendi
   `aggrega()` e richiama la tua funzione da `aggiornaTutto()`; se è
   storico/aggregato una volta sola, segui il pattern di
   `creaGraficiStatici()` e chiamala dall'inizializzazione in fondo al file.
5. **Grafico**: passa sempre da `datiGrafico(id, tipo, dati, opzioni)` e
   costruisci `opzioni` a partire da `opzioniBase()` + `asseX()`/`asseY()` —
   non istanziare `new Chart(...)` a mano fuori da questo helper, altrimenti
   perdi coerenza di animazione/colori/font con tutto il resto.
6. **Tabella**: se serve una tabella, segui `disegnaTabelle()` — genera
   l'HTML della riga con template string concatenate e `esc()` su ogni
   valore testuale proveniente dai dati (mai interpolare senza `esc()`,
   anche se il dato "dovrebbe" essere sicuro — i nomi materiali/clienti
   sono testo libero inserito dall'utente nel gestionale).
7. Aggiorna `README.md` se il comportamento visibile per l'utente cambia.

---

## 6. Come verificare che tutto funzioni dopo una modifica

Sequenza usata finora, ripetila identica:

```bash
cd CruscottoAziendale

# 1. Sintassi Python
python3 -m py_compile config_db.py cruscotto.py notiziario.py

# 2. Serve un config.json di test che punti al DB reale (mai committarlo:
#    è in .gitignore). Path relativo alla cartella del repository:
printf '{"db_path": "%s/data/materiali.db"}' "$(cd .. && pwd)" > config.json

# 3. Esecuzione reale, senza aprire il browser
python3 cruscotto.py --no-open

# 4. Validazione del JSON incorporato (deve fare parsing senza errori,
#    controlla che le chiavi attese ci siano tutte)
python3 -c "
import re, json
html = open('report/ultimo.html', encoding='utf-8').read()
m = re.search(r'var DATI = (\{.*?\});\n', html, re.DOTALL)
d = json.loads(m.group(1))
print(list(d.keys()))
"

# 5. Sintassi JavaScript (serve node, già presente nell'ambiente)
python3 -c "
import re
html = open('report/ultimo.html', encoding='utf-8').read()
scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
open('/tmp/app_check.js','w').write(scripts[-1])
"
node --check /tmp/app_check.js && echo "JS OK"

# 6. Pulizia del config.json di test (non va committato)
rm -f config.json
```

Se aggiungi logica di aggregazione (nuove chiavi in `aggrega()`), verificala
anche isolata con `node -e "..."` ricalcolando a mano il numero atteso dal
JSON incorporato e confrontandolo — è il modo con cui si sono trovati
eventuali bug di aggregazione finora, prima di fidarsi del rendering nel
browser.

---

## 7. Cosa NON fare (promemoria)

- Non introdurre framework/bundler JS.
- Non scrivere mai sul database del gestionale, nemmeno "solo per provare".
- Non toccare file fuori da `CruscottoAziendale/`.
- Non aggiungere dipendenze Python oltre alla standard library.
- Non inventare nuovi colori/raggi/animazioni quando uno schema esistente
  copre già il caso — chiedi all'utente solo se serve davvero un concetto
  visivo nuovo (es. un tipo di grafico mai usato prima).
- Non implementare il tracciamento vinto/perso + ore reali: l'utente ha già
  risposto "lasciamo stare" (vedi §2). Non riproporlo di tua iniziativa.
