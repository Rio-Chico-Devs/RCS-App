# RCS · Cruscotto Aziendale

Strumento **separato** che legge il database del gestionale e produce un report
visivo (grafici fluidi, sintesi automatica, confronti per mese/trimestre/anno).

> **Non modifica nulla.** Il database viene aperto sempre in **sola lettura**.
> Puoi usarlo in tutta sicurezza mentre il gestionale è in uso: è un'app a parte,
> non tocca i dati né i file dell'applicazione principale.

---

## Cosa fa

- **Cruscotto HTML interattivo** (`genera_report.py`): apre nel browser un report
  con indicatori chiave, grafici animati e una sezione **"In sintesi"** che elenca
  in italiano semplice i **punti di forza**, i **punti di attenzione** e i
  **cambiamenti** rispetto al periodo precedente. In alto si cambia la vista tra
  **Mese / Trimestre / Anno** con un clic.
- **Notiziario di settore** (`notiziario.py`, opzionale): raccoglie dal web notizie
  mirate sulla fibra di carbonio, i compositi e i vostri fornitori, le riassume in
  stile telegiornale **con le fonti citate**, e le mostra dentro al report.

Le analisi incluse: andamento e valore dei preventivi, margine reale (prezzo
cliente vs costo pieno), composizione dei costi, manodopera per fase, materiali
più usati, clienti per valore, giacenze vs scorta minima, ricarico per materiale,
confronto prezzi tra fornitori, ultimi movimenti di magazzino.

---

## Requisiti

- **Python 3** installato (lo stesso che fa girare il gestionale).
- Per il **cruscotto**: niente da installare. Alla prima esecuzione scarica una
  piccola libreria grafica da internet e la tiene in cache nella cartella `assets`;
  dopo funziona anche offline. Se non c'è internet, numeri e tabelle restano
  comunque visibili.
- Per il **notiziario** (opzionale): il pacchetto `anthropic` e una chiave API.
  ```
  pip install anthropic
  ```

---

## Come si usa

### Cruscotto (consigliato per iniziare)

Doppio clic su **`Cruscotto.bat`** (Windows), oppure da terminale, nella cartella
`analisi`:

```
python genera_report.py
```

Genera il report e lo apre nel browser. I report restano salvati nella cartella
`report` (ne trovi anche uno sempre aggiornato in `report/ultimo.html`).

Opzioni:
```
python genera_report.py --no-open          genera senza aprire il browser
python genera_report.py --db "Z:\RCS\materiali.db"   usa un database specifico
```

Il database viene individuato **come fa il gestionale**: se esiste `config.json`
(database in rete) usa quello, altrimenti `data\materiali.db`.

### Notiziario di settore (opzionale)

1. Procurati una chiave API (console Anthropic) e impostala come variabile
   d'ambiente:
   ```
   set ANTHROPIC_API_KEY=la-tua-chiave        (Windows, sessione corrente)
   ```
2. Esegui:
   ```
   python notiziario.py
   ```
3. Rigenera il report (`python genera_report.py`): le notizie compaiono nella
   sezione **"Notiziario di settore"**.

**Privacy:** al servizio online vengono inviati solo i **nomi generici** di
materiali e fornitori, per mirare la ricerca. Nessun prezzo, cliente, importo o
dato di preventivo lascia il computer.

---

## Domande frequenti

**Può rovinare i dati del gestionale?**
No. Apre il database in sola lettura (modalità `mode=ro` di SQLite): qualsiasi
tentativo di scrittura fallirebbe. Non scrive nella cartella dell'app: salva tutto
qui dentro, in `analisi`.

**Perché alcuni numeri sono "direzionali"?**
Con pochi preventivi le variazioni vanno lette come tendenze, non come statistiche.
Più lo storico cresce, più le analisi diventano solide. Lo strumento lo segnala da
solo quando i dati di un periodo sono pochi.

**Posso eseguirlo ogni giorno / settimana?**
Sì. Ogni esecuzione crea un nuovo report con data e ora nel nome; `ultimo.html` è
sempre l'ultimo generato.

---

## File della cartella

| File | A cosa serve |
|------|--------------|
| `genera_report.py` | Genera il cruscotto HTML (sola lettura) |
| `notiziario.py` | Raccoglie le notizie di settore (opzionale, richiede chiave API) |
| `Cruscotto.bat` | Avvio rapido su Windows (doppio clic) |
| `report/` | I report generati (`ultimo.html` è il più recente) |
| `assets/` | Cache della libreria grafica |
| `notiziario_ultimo.json` | Ultime notizie raccolte (mostrate nel report) |
