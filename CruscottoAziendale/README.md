# RCS · Cruscotto Aziendale

Applicazione **indipendente** che legge il database del gestionale e produce un
report visivo (grafici fluidi, sintesi automatica, confronti per
mese/trimestre/anno).

> **È un programma a sé.** Non fa parte del gestionale, non lo modifica, non
> parte insieme a lui. L'unica cosa che fa è **leggere** il file del database
> (sempre in **sola lettura**: una scrittura fallirebbe per costruzione).
> Puoi tenere questa cartella dove vuoi — anche su un altro PC — e dirle dove
> trovare il database tramite il file `config.json`.

---

## Indice rapido

1. Avvia **`Cruscotto.bat`** (o `python cruscotto.py`).
2. La **prima volta** si apre una finestra: **scegli il file del database**
   (`materiali.db`). Fatto — la scelta viene ricordata.
3. (Facoltativo) Per il notiziario di settore: vedi più sotto.

---

## 1. Il database (te lo chiede da solo)

Al **primo avvio** il programma apre una finestra e ti fa **selezionare il file
del database** del gestionale (di solito si chiama `materiali.db`). Lo scegli una
volta e la scelta viene **ricordata** (salvata in `config.json`): le volte
successive parte da sola.

Per **cambiare** database in seguito:
```
python cruscotto.py --scegli
```
(ri-apre la finestra di selezione), oppure modifica a mano il file `config.json`.

**Alternativa manuale** (facoltativa): puoi anche partire da `config.example.json`,
copiarlo in `config.json` e scrivere il percorso a mano:
```json
{ "db_path": "Z:/RCS/data/materiali.db", "anthropic_api_key": "" }
```
Usa la barra normale `/` anche su Windows. Se tieni una copia del database accanto
al programma (`materiali.db` o `data/materiali.db`), lo trova da solo senza
chiedere nulla. `anthropic_api_key` serve solo per il notiziario.

---

## 2. Cruscotto

Doppio clic su **`Cruscotto.bat`**, oppure da terminale:

```
python cruscotto.py
```

Genera il report e lo apre nel browser. I report restano in `report/`
(`report/ultimo.html` è sempre il più recente).

Opzioni:
```
python cruscotto.py --scegli                    scegli/cambia il database (finestra)
python cruscotto.py --no-open                   genera senza aprire il browser
python cruscotto.py --db "Z:/RCS/materiali.db"  usa un database specifico al volo
```

Cosa mostra: indicatori chiave animati, una sezione **"In sintesi"** con
**forza / attenzione / cambiamenti** scritti in italiano semplice, e i grafici:
andamento e valore preventivi, margini, composizione costi, manodopera per fase,
materiali più usati, clienti per valore, giacenze vs scorta minima. Più le
tabelle di ricarico per materiale, confronto fornitori e ultimi movimenti.

In alto si cambia la vista **Mese / Trimestre / Anno** con un clic.

---

## 3. Notiziario di settore (opzionale)

Raccoglie dal web notizie mirate su fibra di carbonio, compositi e i vostri
fornitori, le riassume **con le fonti citate** e le mostra dentro al report.

1. Installa il pacchetto necessario (una volta sola):
   ```
   pip install anthropic
   ```
2. Metti la chiave API in `config.json` (`"anthropic_api_key": "..."`),
   **oppure** nella variabile d'ambiente `ANTHROPIC_API_KEY`.
3. Avvia **`Notiziario.bat`** (o `python notiziario.py`).
4. Rigenera il cruscotto: le notizie compaiono nella sezione apposita.

**Privacy:** al servizio online vengono inviati solo i **nomi generici** di
materiali e fornitori, per mirare la ricerca. Nessun prezzo, cliente, importo o
dato di preventivo lascia il computer.

---

## 4. Creare l'eseguibile (.exe) — distribuzione autonoma

Per avere un programma che gira **senza installare Python**, doppio clic su
**`crea_eseguibile.bat`**. Crea nella cartella `dist/`:

- `CruscottoAziendale.exe` — il cruscotto
- `Notiziario.exe` — il notiziario

Per usarli su un altro PC: copia gli `.exe` insieme a un file **`config.json`**
(con il percorso del database) nella stessa cartella. Tutto qui — niente Python,
niente gestionale.

---

## Domande frequenti

**Può rovinare i dati del gestionale?**
No. Apre il database in sola lettura (`mode=ro` di SQLite). Non scrive mai sul
database e non tocca i file del gestionale: salva solo qui dentro.

**Devo tenerlo nella stessa cartella del gestionale?**
No. È indipendente: mettilo dove vuoi e indica il percorso del database in
`config.json`.

**Perché alcuni numeri sono "direzionali"?**
Con pochi preventivi le variazioni sono tendenze, non statistiche. Più lo storico
cresce, più le analisi diventano solide. Lo strumento lo segnala da solo quando i
dati di un periodo sono pochi.

---

## File della cartella

| File | A cosa serve |
|------|--------------|
| `cruscotto.py` | Genera il cruscotto HTML (sola lettura) |
| `notiziario.py` | Raccoglie le notizie di settore (opzionale) |
| `config_db.py` | Trova il database dal `config.json` (sola lettura) |
| `config.example.json` | Modello di configurazione (copialo in `config.json`) |
| `Cruscotto.bat` | Avvio rapido del cruscotto (Windows) |
| `Notiziario.bat` | Avvio rapido del notiziario (Windows) |
| `crea_eseguibile.bat` | Crea gli `.exe` autonomi (cartella `dist/`) |
| `report/` | I report generati (`ultimo.html` è il più recente) |
| `assets/` | Cache della libreria grafica |
