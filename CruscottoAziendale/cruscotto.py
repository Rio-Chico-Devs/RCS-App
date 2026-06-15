#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RCS - Cruscotto Aziendale
Genera un report HTML interattivo (grafici, sintesi, confronti per
mese/trimestre/anno) leggendo il database del gestionale in SOLA LETTURA.

Uso:
    python cruscotto.py            # genera e apre il report nel browser
    python cruscotto.py --no-open  # genera senza aprire il browser
    python cruscotto.py --db PERCORSO/materiali.db   # database specifico

Non modifica mai il database: la connessione e' aperta in modalita' read-only.
"""

import argparse
import html
import json
import os
import sqlite3
import sys
import urllib.request
import webbrowser
from datetime import datetime
from string import Template

import config_db  # modulo locale: trova il DB dal config.json di questo strumento

BASE_DIR = config_db.base_dir()                               # cartella dello strumento (o dell'exe)
REPORT_DIR = os.path.join(BASE_DIR, "report")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CHARTJS_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.9/dist/chart.umd.min.js"
CHARTJS_CACHE = os.path.join(ASSETS_DIR, "chart.umd.min.js")
NOTIZIARIO_PATH = os.path.join(BASE_DIR, "notiziario_ultimo.json")


# ----------------------------------------------------------------- database

def trova_db_path(cli=None):
    return config_db.trova_db_path(cli)


def apri_db_sola_lettura(db_path):
    return config_db.apri_db_sola_lettura(db_path)


def _num(v):
    try:
        return float(v) if v is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


# ------------------------------------------------------------- estrazione

def estrai_preventivi(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT id, data_creazione, nome_cliente, descrizione, codice,
               prezzo_cliente, preventivo_finale, costo_totale_materiali,
               tot_mano_opera, costi_accessori,
               minuti_taglio, minuti_avvolgimento, minuti_pulizia,
               minuti_rettifica, minuti_imballaggio,
               materiali_utilizzati, numero_revisione
        FROM preventivi ORDER BY data_creazione
    """)
    out = []
    for r in cur.fetchall():
        materiali = []
        try:
            for m in json.loads(r[15] or "[]"):
                materiali.append({
                    "nome": m.get("materiale_nome", "") or "?",
                    "mq": round(_num(m.get("lunghezza_utilizzata")), 3),
                    "costo": round(_num(m.get("costo_totale")), 2),
                })
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
        costo_pieno = _num(r[7]) + _num(r[8]) + _num(r[9])
        out.append({
            "id": r[0],
            "data": (r[1] or "")[:10],
            "cliente": r[2] or "(senza nome)",
            "descrizione": r[3] or "",
            "codice": r[4] or "",
            "valore": round(_num(r[5]), 2),          # prezzo cliente reale
            "listino": round(_num(r[6]), 2),         # preventivo finale calcolato
            "costo_materiali": round(_num(r[7]), 2),
            "mano_opera": round(_num(r[8]), 2),
            "accessori": round(_num(r[9]), 2),
            "costo_pieno": round(costo_pieno, 2),
            "minuti": {
                "Taglio": round(_num(r[10]), 1),
                "Avvolgimento": round(_num(r[11]), 1),
                "Pulizia": round(_num(r[12]), 1),
                "Rettifica": round(_num(r[13]), 1),
                "Imballaggio": round(_num(r[14]), 1),
            },
            "materiali": materiali,
            "revisione": r[16] or 1,
        })
    return out


def estrai_magazzino(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT m.id, m.nome,
               COALESCE((SELECT SUM(giacenza) FROM materiale_fornitori
                         WHERE materiale_id = m.id), m.giacenza) AS giacenza_tot,
               m.scorta_minima, m.scorta_massima,
               COALESCE((SELECT MIN(prezzo_fornitore) FROM materiale_fornitori
                         WHERE materiale_id = m.id AND prezzo_fornitore > 0),
                        NULLIF(m.prezzo_fornitore, 0), 0) AS prezzo_acq,
               (SELECT COUNT(*) FROM materiale_fornitori
                WHERE materiale_id = m.id) AS n_forn,
               m.prezzo
        FROM materiali m ORDER BY m.nome
    """)
    out = []
    for r in cur.fetchall():
        giac = round(_num(r[2]), 2)
        prezzo_acq = round(_num(r[5]), 2)
        out.append({
            "nome": r[1],
            "giacenza": giac,
            "scorta_min": round(_num(r[3]), 2),
            "scorta_max": round(_num(r[4]), 2),
            "prezzo_acq": prezzo_acq,
            "vendita": round(_num(r[7]), 2),
            "capitale": round(giac * prezzo_acq, 2),
            "n_fornitori": r[6],
        })
    return out


def estrai_confronto_fornitori(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT m.nome, mf.fornitore_nome, mf.prezzo_fornitore
        FROM materiale_fornitori mf
        JOIN materiali m ON m.id = mf.materiale_id
        WHERE mf.prezzo_fornitore > 0
        ORDER BY m.nome, mf.prezzo_fornitore
    """)
    per_materiale = {}
    for nome, forn, prezzo in cur.fetchall():
        per_materiale.setdefault(nome, []).append(
            {"nome": forn, "prezzo": round(_num(prezzo), 2)})
    return [{"materiale": k, "fornitori": v}
            for k, v in sorted(per_materiale.items()) if len(v) >= 2]


def estrai_movimenti(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT mov.data, mov.tipo, mov.quantita, m.nome,
               COALESCE(mov.fornitore_nome, ''), COALESCE(mov.note, '')
        FROM movimenti_magazzino mov
        JOIN materiali m ON m.id = mov.materiale_id
        ORDER BY mov.data DESC LIMIT 50
    """)
    return [{"data": (r[0] or "")[:10], "tipo": r[1],
             "quantita": round(_num(r[2]), 2), "materiale": r[3],
             "fornitore": r[4], "note": r[5]} for r in cur.fetchall()]


def carica_notiziario():
    if not os.path.exists(NOTIZIARIO_PATH):
        return None
    try:
        with open(NOTIZIARIO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ------------------------------------------------------------------ assets

def ottieni_chartjs():
    """Restituisce il sorgente di Chart.js (cache locale, poi download).
    Se non disponibile, si usera' il CDN direttamente dal browser."""
    try:
        if os.path.exists(CHARTJS_CACHE) and os.path.getsize(CHARTJS_CACHE) > 100_000:
            with open(CHARTJS_CACHE, "r", encoding="utf-8") as f:
                return f.read()
    except Exception:
        pass
    try:
        os.makedirs(ASSETS_DIR, exist_ok=True)
        with urllib.request.urlopen(CHARTJS_URL, timeout=15) as resp:
            contenuto = resp.read().decode("utf-8")
        if len(contenuto) > 100_000:
            with open(CHARTJS_CACHE, "w", encoding="utf-8") as f:
                f.write(contenuto)
            return contenuto
    except Exception:
        pass
    return None


# ---------------------------------------------------------------- template

HTML_TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RCS · Cruscotto Aziendale</title>
${CHARTJS_TAG}
<style>
  :root {
    --bg: #0d1117; --card: #151c25; --card2: #1a222d; --bordo: #25303d;
    --testo: #e6edf3; --muto: #8b97a5; --accento: #f0b429; --teal: #43c6b9;
    --verde: #4ec97b; --rosso: #ef6a6a; --blu: #6aa9ef;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    color: var(--testo);
    background:
      repeating-linear-gradient(45deg, rgba(255,255,255,.014) 0 2px, transparent 2px 7px),
      repeating-linear-gradient(-45deg, rgba(255,255,255,.014) 0 2px, transparent 2px 7px),
      var(--bg);
    min-height: 100vh; padding-bottom: 60px;
  }
  .contenitore { max-width: 1240px; margin: 0 auto; padding: 0 22px; }

  header { padding: 30px 0 6px; display: flex; flex-wrap: wrap; gap: 16px;
           align-items: flex-end; justify-content: space-between; }
  .logo { font-size: 26px; font-weight: 800; letter-spacing: .4px; }
  .logo b { color: var(--accento); }
  .sottotitolo { color: var(--muto); font-size: 13px; margin-top: 4px; }

  .pills { display: inline-flex; background: var(--card); border: 1px solid var(--bordo);
           border-radius: 999px; padding: 4px; gap: 2px; }
  .pills button { border: 0; background: transparent; color: var(--muto);
    padding: 8px 22px; border-radius: 999px; font-size: 14px; font-weight: 600;
    cursor: pointer; transition: all .25s ease; }
  .pills button.attivo { background: var(--accento); color: #1a1404;
    box-shadow: 0 2px 12px rgba(240,180,41,.35); }
  .pills button:not(.attivo):hover { color: var(--testo); }

  .griglia-kpi { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr));
                 gap: 14px; margin: 22px 0; }
  .kpi { background: linear-gradient(160deg, var(--card2), var(--card));
    border: 1px solid var(--bordo); border-radius: 14px; padding: 16px 18px;
    transition: transform .25s ease, box-shadow .25s ease; }
  .kpi:hover { transform: translateY(-3px); box-shadow: 0 10px 26px rgba(0,0,0,.45); }
  .kpi .etichetta { color: var(--muto); font-size: 12px; font-weight: 600;
                    text-transform: uppercase; letter-spacing: .6px; }
  .kpi .valore { font-size: 27px; font-weight: 800; margin-top: 6px;
                 font-variant-numeric: tabular-nums; }
  .kpi .delta { font-size: 12.5px; margin-top: 5px; font-weight: 600; }
  .delta.su { color: var(--verde); } .delta.giu { color: var(--rosso); }
  .delta.neutro { color: var(--muto); }

  .sezione { background: var(--card); border: 1px solid var(--bordo);
    border-radius: 16px; padding: 22px; margin: 18px 0;
    opacity: 0; transform: translateY(14px);
    transition: opacity .55s ease, transform .55s ease; }
  .sezione.visibile { opacity: 1; transform: none; }
  .sezione h2 { font-size: 16.5px; font-weight: 700; margin-bottom: 16px;
    display: flex; align-items: center; gap: 9px; }
  .sezione h2::before { content: ""; width: 5px; height: 18px;
    background: var(--accento); border-radius: 3px; }
  .nota-periodo { color: var(--muto); font-size: 12px; font-weight: 400; margin-left: auto; }

  .colonne-sintesi { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px,1fr)); gap: 16px; }
  .blocco-sintesi { background: var(--card2); border: 1px solid var(--bordo);
                    border-radius: 12px; padding: 14px 16px; }
  .blocco-sintesi h3 { font-size: 13.5px; margin-bottom: 10px; }
  .blocco-sintesi.forza h3 { color: var(--verde); }
  .blocco-sintesi.attenzione h3 { color: var(--accento); }
  .blocco-sintesi.cambi h3 { color: var(--blu); }
  .blocco-sintesi ul { list-style: none; }
  .blocco-sintesi li { font-size: 13.5px; line-height: 1.5; padding: 6px 0 6px 22px;
    position: relative; border-bottom: 1px dashed rgba(255,255,255,.05); }
  .blocco-sintesi li:last-child { border-bottom: 0; }
  .blocco-sintesi li::before { position: absolute; left: 0; }
  .blocco-sintesi.forza li::before { content: "✔"; color: var(--verde); }
  .blocco-sintesi.attenzione li::before { content: "▲"; color: var(--accento); font-size: 11px; top: 9px; }
  .blocco-sintesi.cambi li::before { content: "→"; color: var(--blu); }
  .vuoto { color: var(--muto); font-style: italic; font-size: 13px; }

  .griglia-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
  @media (max-width: 900px) { .griglia-2 { grid-template-columns: 1fr; } }
  .riquadro-grafico { position: relative; height: 300px; }
  .riquadro-grafico.alto { height: 340px; }

  table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
  th { text-align: left; color: var(--muto); font-size: 12px; text-transform: uppercase;
       letter-spacing: .5px; padding: 8px 10px; border-bottom: 1px solid var(--bordo); }
  td { padding: 9px 10px; border-bottom: 1px solid rgba(255,255,255,.045); }
  tr:hover td { background: rgba(255,255,255,.025); }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
  .tag { display: inline-block; padding: 2px 9px; border-radius: 999px;
         font-size: 11.5px; font-weight: 700; }
  .tag.ok { background: rgba(78,201,123,.14); color: var(--verde); }
  .tag.basso { background: rgba(239,106,106,.14); color: var(--rosso); }
  .tag.medio { background: rgba(240,180,41,.14); color: var(--accento); }
  .tag.carico { background: rgba(106,169,239,.14); color: var(--blu); }
  .tag.scarico { background: rgba(240,180,41,.14); color: var(--accento); }

  .notizia { background: var(--card2); border: 1px solid var(--bordo); border-left: 4px solid var(--teal);
             border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; }
  .notizia h4 { font-size: 14.5px; margin-bottom: 6px; }
  .notizia p { font-size: 13.5px; color: #c4cdd6; line-height: 1.55; }
  .notizia .fonte { font-size: 12px; margin-top: 8px; }
  .notizia .fonte a { color: var(--teal); text-decoration: none; }
  .notizia .fonte a:hover { text-decoration: underline; }
  .rilevanza { font-size: 12.5px; color: var(--accento); margin-top: 6px; font-style: italic; }
  .suggerimento { border: 1px dashed var(--bordo); border-radius: 12px; padding: 16px;
                  color: var(--muto); font-size: 13.5px; line-height: 1.6; }

  footer { color: var(--muto); font-size: 12px; text-align: center; margin-top: 34px;
           line-height: 1.7; }
</style>
</head>
<body>
<div class="contenitore">

  <header>
    <div>
      <div class="logo">RCS · <b>Cruscotto Aziendale</b></div>
      <div class="sottotitolo">Generato il ${GENERATO_IL} · database in sola lettura</div>
    </div>
    <div class="pills" id="selettorePeriodo">
      <button data-gran="mese" class="attivo">Mese</button>
      <button data-gran="trimestre">Trimestre</button>
      <button data-gran="anno">Anno</button>
    </div>
  </header>

  <div class="griglia-kpi" id="grigliaKpi"></div>

  <div class="sezione">
    <h2>In sintesi <span class="nota-periodo" id="notaSintesi"></span></h2>
    <div class="colonne-sintesi">
      <div class="blocco-sintesi forza"><h3>PUNTI DI FORZA</h3><ul id="listaForza"></ul></div>
      <div class="blocco-sintesi attenzione"><h3>PUNTI DI ATTENZIONE</h3><ul id="listaAttenzione"></ul></div>
      <div class="blocco-sintesi cambi"><h3>CAMBIAMENTI</h3><ul id="listaCambi"></ul></div>
    </div>
  </div>

  <div class="sezione">
    <h2>Andamento preventivi <span class="nota-periodo" id="notaAndamento"></span></h2>
    <div class="riquadro-grafico alto"><canvas id="chartAndamento"></canvas></div>
  </div>

  <div class="griglia-2">
    <div class="sezione">
      <h2>Margini</h2>
      <div class="riquadro-grafico"><canvas id="chartMargini"></canvas></div>
    </div>
    <div class="sezione">
      <h2>Composizione dei costi</h2>
      <div class="riquadro-grafico"><canvas id="chartCosti"></canvas></div>
    </div>
  </div>

  <div class="griglia-2">
    <div class="sezione">
      <h2>Manodopera per fase <span class="nota-periodo">tutto lo storico</span></h2>
      <div class="riquadro-grafico"><canvas id="chartFasi"></canvas></div>
    </div>
    <div class="sezione">
      <h2>Materiali più utilizzati <span class="nota-periodo">tutto lo storico</span></h2>
      <div class="riquadro-grafico"><canvas id="chartMateriali"></canvas></div>
    </div>
  </div>

  <div class="griglia-2">
    <div class="sezione">
      <h2>Clienti per valore <span class="nota-periodo">tutto lo storico</span></h2>
      <div class="riquadro-grafico"><canvas id="chartClienti"></canvas></div>
    </div>
    <div class="sezione">
      <h2>Magazzino: giacenze e scorte minime</h2>
      <div class="riquadro-grafico"><canvas id="chartMagazzino"></canvas></div>
    </div>
  </div>

  <div class="sezione">
    <h2>Ricarico per materiale <span class="nota-periodo">prezzo di vendita vs miglior prezzo fornitore</span></h2>
    <div style="overflow-x:auto"><table id="tabRicarichi"></table></div>
  </div>

  <div class="sezione" id="sezFornitori" style="display:none">
    <h2>Confronto fornitori <span class="nota-periodo">materiali con più fornitori</span></h2>
    <div style="overflow-x:auto"><table id="tabFornitori"></table></div>
  </div>

  <div class="sezione" id="sezMovimenti" style="display:none">
    <h2>Magazzino: ultimi movimenti</h2>
    <div style="overflow-x:auto"><table id="tabMovimenti"></table></div>
  </div>

  <div class="sezione">
    <h2>Notiziario di settore</h2>
    <div id="riquadroNotiziario"></div>
  </div>

  <footer>
    Cruscotto generato in sola lettura — nessuna modifica ai dati del gestionale.<br>
    Database: ${DB_PATH} · Preventivi analizzati: ${N_PREVENTIVI}
  </footer>
</div>

<script>
var DATI = ${JSON_DATI};

// ------------------------------------------------------------- utilita'
var fmtEuro = new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
var fmtEuro2 = new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' });
var fmtNum = new Intl.NumberFormat('it-IT', { maximumFractionDigits: 1 });
var MESI = ['gen','feb','mar','apr','mag','giu','lug','ago','set','ott','nov','dic'];

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}
function pct(v) { return fmtNum.format(v) + '%'; }

function chiavePeriodo(dataIso, gran) {
  var anno = dataIso.slice(0, 4), mese = parseInt(dataIso.slice(5, 7), 10);
  if (gran === 'anno') return anno;
  if (gran === 'trimestre') return anno + '-T' + (Math.floor((mese - 1) / 3) + 1);
  return dataIso.slice(0, 7);
}
function etichettaPeriodo(chiave, gran) {
  if (gran === 'anno') return chiave;
  if (gran === 'trimestre') return chiave.replace('-', ' ');
  return MESI[parseInt(chiave.slice(5, 7), 10) - 1] + ' ' + chiave.slice(0, 4);
}
function periodoSuccessivo(chiave, gran) {
  if (gran === 'anno') return String(parseInt(chiave, 10) + 1);
  if (gran === 'trimestre') {
    var a = parseInt(chiave.slice(0, 4), 10), t = parseInt(chiave.slice(6), 10);
    return t === 4 ? (a + 1) + '-T1' : a + '-T' + (t + 1);
  }
  var anno = parseInt(chiave.slice(0, 4), 10), mese = parseInt(chiave.slice(5, 7), 10);
  if (mese === 12) { anno++; mese = 1; } else { mese++; }
  return anno + '-' + (mese < 10 ? '0' + mese : mese);
}

// Aggrega i preventivi per periodo, riempiendo i periodi senza dati.
function aggrega(gran) {
  var gruppi = {};
  DATI.preventivi.forEach(function (p) {
    if (!p.data) return;
    var k = chiavePeriodo(p.data, gran);
    if (!gruppi[k]) gruppi[k] = { n: 0, valore: 0, listino: 0, costo: 0,
      materiali: 0, manodopera: 0, accessori: 0, scontati: 0, sopraListino: 0 };
    var g = gruppi[k];
    g.n++; g.valore += p.valore; g.listino += p.listino; g.costo += p.costo_pieno;
    g.materiali += p.costo_materiali; g.manodopera += p.mano_opera; g.accessori += p.accessori;
    if (p.listino > 0 && p.valore < p.listino * 0.999) g.scontati++;
    if (p.listino > 0 && p.valore > p.listino * 1.001) g.sopraListino++;
  });
  var chiavi = Object.keys(gruppi).sort();
  if (!chiavi.length) return [];
  var serie = [], k = chiavi[0], ultima = chiavi[chiavi.length - 1];
  while (true) {
    var g = gruppi[k] || { n: 0, valore: 0, listino: 0, costo: 0, materiali: 0,
      manodopera: 0, accessori: 0, scontati: 0, sopraListino: 0 };
    g.chiave = k; g.etichetta = etichettaPeriodo(k, gran);
    g.margine = g.valore - g.costo;
    g.marginePct = g.valore > 0 ? (g.margine / g.valore) * 100 : 0;
    serie.push(g);
    if (k === ultima) break;
    k = periodoSuccessivo(k, gran);
    if (serie.length > 400) break;
  }
  return serie;
}

var NOMI_GRAN = { mese: ['mese', 'il mese precedente'], trimestre: ['trimestre', 'il trimestre precedente'], anno: ['anno', "l'anno precedente"] };

// ------------------------------------------------------------------ KPI
function deltaHtml(attuale, precedente, formato, invertito) {
  if (precedente === null || precedente === undefined) {
    return '<div class="delta neutro">primo periodo con dati</div>';
  }
  var diff = attuale - precedente, cls = 'neutro', freccia = '—';
  if (Math.abs(diff) > 1e-9) {
    var positivo = diff > 0;
    if (invertito) positivo = !positivo;
    cls = positivo ? 'su' : 'giu';
    freccia = diff > 0 ? '▲' : '▼';
  }
  var testo;
  if (formato === 'pp') testo = fmtNum.format(Math.abs(diff)) + ' punti';
  else if (formato === 'euro') testo = fmtEuro.format(Math.abs(diff));
  else if (formato === 'pct' && Math.abs(precedente) > 1e-9)
    testo = fmtNum.format(Math.abs(diff / precedente) * 100) + '%';
  else testo = fmtNum.format(Math.abs(diff));
  return '<div class="delta ' + cls + '">' + freccia + ' ' + testo + ' vs periodo prec.</div>';
}

function animaNumero(el, finale, formatta) {
  var durata = 750, t0 = null;
  function passo(t) {
    if (!t0) t0 = t;
    var f = Math.min((t - t0) / durata, 1);
    f = 1 - Math.pow(1 - f, 3);
    el.textContent = formatta(finale * f);
    if (f < 1) requestAnimationFrame(passo);
  }
  requestAnimationFrame(passo);
}

function disegnaKpi(serie, gran) {
  var griglia = document.getElementById('grigliaKpi');
  var conDati = serie.filter(function (s) { return s.n > 0; });
  var ult = conDati[conDati.length - 1] || null;
  var prec = conDati.length > 1 ? conDati[conDati.length - 2] : null;
  var capitale = DATI.magazzino.reduce(function (a, m) { return a + m.capitale; }, 0);
  var sottoScorta = DATI.magazzino.filter(function (m) { return m.scorta_min > 0 && m.giacenza < m.scorta_min; });
  var nomeP = ult ? ult.etichetta : '—';

  var schede = [
    { etich: 'Preventivi · ' + nomeP, val: ult ? ult.n : 0, fmt: function (v) { return Math.round(v); },
      delta: ult ? deltaHtml(ult.n, prec ? prec.n : null, 'num') : '' },
    { etich: 'Valore preventivato · ' + nomeP, val: ult ? ult.valore : 0, fmt: fmtEuro.format,
      delta: ult ? deltaHtml(ult.valore, prec ? prec.valore : null, 'euro') : '' },
    { etich: 'Margine medio · ' + nomeP, val: ult ? ult.marginePct : 0, fmt: pct,
      delta: ult ? deltaHtml(ult.marginePct, prec ? prec.marginePct : null, 'pp') : '' },
    { etich: 'Prezzo medio · ' + nomeP, val: ult && ult.n ? ult.valore / ult.n : 0, fmt: fmtEuro.format,
      delta: ult && ult.n && prec && prec.n ? deltaHtml(ult.valore / ult.n, prec.valore / prec.n, 'euro') : '<div class="delta neutro">&nbsp;</div>' },
    { etich: 'Capitale a magazzino', val: capitale, fmt: fmtEuro.format,
      delta: '<div class="delta neutro">giacenze × prezzo fornitore</div>' },
    { etich: 'Materiali sotto scorta', val: sottoScorta.length, fmt: function (v) { return Math.round(v); },
      delta: sottoScorta.length
        ? '<div class="delta giu">' + esc(sottoScorta.map(function (m) { return m.nome; }).join(', ')) + '</div>'
        : '<div class="delta su">tutte le scorte ok</div>' },
  ];
  griglia.innerHTML = schede.map(function (s) {
    return '<div class="kpi"><div class="etichetta">' + s.etich + '</div>' +
           '<div class="valore"></div>' + s.delta + '</div>';
  }).join('');
  var valori = griglia.querySelectorAll('.valore');
  schede.forEach(function (s, i) { animaNumero(valori[i], s.val, s.fmt); });
}

// ------------------------------------------------------------- sintesi
function disegnaSintesi(serie, gran) {
  var forza = [], attenzione = [], cambi = [];
  var conDati = serie.filter(function (s) { return s.n > 0; });
  var ult = conDati[conDati.length - 1] || null;
  var prec = conDati.length > 1 ? conDati[conDati.length - 2] : null;
  var nomi = NOMI_GRAN[gran];
  document.getElementById('notaSintesi').textContent =
    ult ? 'ultimo ' + nomi[0] + ' con dati: ' + ult.etichetta : '';

  if (ult) {
    if (ult.n < 3) attenzione.push('Dati limitati nel periodo (' + ult.n +
      ' preventivi): leggere le variazioni con cautela.');

    if (ult.marginePct >= 35)
      forza.push('Margine medio del ' + pct(ult.marginePct) + ' su ' + ult.etichetta + ': la maggiorazione copre bene i costi.');
    else if (ult.marginePct < 25 && ult.n >= 2)
      attenzione.push('Margine medio sceso al ' + pct(ult.marginePct) + ' su ' + ult.etichetta + ': sotto questa soglia gli imprevisti non sono più coperti.');

    if (ult.sopraListino > ult.n / 2)
      forza.push('In ' + ult.sopraListino + ' preventivi su ' + ult.n + ' il prezzo concordato è sopra il listino calcolato: i clienti riconoscono il valore del lavoro.');
    if (ult.scontati > ult.n * 0.4 && ult.listino > 0) {
      var scontoMedio = (1 - ult.valore / ult.listino) * 100;
      if (scontoMedio > 3)
        attenzione.push('Nel periodo il ' + Math.round(ult.scontati / ult.n * 100) + '% dei preventivi è stato chiuso sotto listino (sconto medio ' + pct(scontoMedio) + ').');
    }
  }

  if (prec && ult) {
    var diffN = ult.n - prec.n;
    if (diffN !== 0)
      cambi.push((diffN > 0 ? 'Più' : 'Meno') + ' preventivi rispetto a ' + nomi[1] + ': ' +
        prec.n + ' → ' + ult.n + '.');
    if (prec.valore > 0) {
      var diffV = (ult.valore / prec.valore - 1) * 100;
      if (Math.abs(diffV) >= 5)
        cambi.push('Valore preventivato ' + (diffV > 0 ? 'in crescita' : 'in calo') + ' del ' +
          pct(Math.abs(diffV)) + ' (' + fmtEuro.format(prec.valore) + ' → ' + fmtEuro.format(ult.valore) + ').');
    }
    var diffM = ult.marginePct - prec.marginePct;
    if (Math.abs(diffM) >= 3)
      cambi.push('Margine medio ' + (diffM > 0 ? 'salito' : 'sceso') + ' di ' + fmtNum.format(Math.abs(diffM)) +
        ' punti rispetto a ' + nomi[1] + ' (' + pct(prec.marginePct) + ' → ' + pct(ult.marginePct) + ').');
  }

  // Concentrazione clienti (storico completo)
  var perCliente = {}, totale = 0;
  DATI.preventivi.forEach(function (p) {
    perCliente[p.cliente] = (perCliente[p.cliente] || 0) + p.valore; totale += p.valore;
  });
  var top = Object.keys(perCliente).map(function (k) { return [k, perCliente[k]]; })
    .sort(function (a, b) { return b[1] - a[1]; })[0];
  if (top && totale > 0) {
    var quota = top[1] / totale * 100;
    if (quota > 40)
      attenzione.push('Il ' + pct(quota) + ' del valore storico viene da un solo cliente (' + esc(top[0]) + '): dipendenza da monitorare.');
    else if (Object.keys(perCliente).length >= 4)
      forza.push('Clientela diversificata: il cliente principale (' + esc(top[0]) + ') pesa solo il ' + pct(quota) + ' del totale.');
  }

  // Fase di manodopera dominante (storico completo)
  var fasi = {};
  DATI.preventivi.forEach(function (p) {
    Object.keys(p.minuti).forEach(function (f) { fasi[f] = (fasi[f] || 0) + p.minuti[f]; });
  });
  var totMin = Object.keys(fasi).reduce(function (a, f) { return a + fasi[f]; }, 0);
  if (totMin > 0) {
    var faseTop = Object.keys(fasi).sort(function (a, b) { return fasi[b] - fasi[a]; })[0];
    var quotaFase = fasi[faseTop] / totMin * 100;
    if (quotaFase > 45)
      attenzione.push("L'" + faseTop.toLowerCase() + ' assorbe il ' + pct(quotaFase) +
        ' della manodopera: è la fase dove un guadagno di efficienza rende di più.');
  }

  // Ricarichi bassi
  var bassi = DATI.ricarichi.filter(function (r) { return r.pct !== null && r.pct < 50; });
  if (bassi.length)
    attenzione.push(bassi.length + (bassi.length === 1 ? ' materiale ha' : ' materiali hanno') +
      ' un ricarico sotto il 50% sul prezzo fornitore: ' +
      esc(bassi.slice(0, 4).map(function (r) { return r.nome; }).join(', ')) + (bassi.length > 4 ? '…' : '') + '.');

  // Sotto scorta
  var sotto = DATI.magazzino.filter(function (m) { return m.scorta_min > 0 && m.giacenza < m.scorta_min; });
  if (sotto.length)
    attenzione.push('Materiali sotto la scorta minima: ' + esc(sotto.map(function (m) {
      return m.nome + ' (' + fmtNum.format(m.giacenza) + ' / min ' + fmtNum.format(m.scorta_min) + ' m²)';
    }).join(', ')) + '.');

  function riempi(id, voci) {
    document.getElementById(id).innerHTML = voci.length
      ? voci.map(function (v) { return '<li>' + v + '</li>'; }).join('')
      : '<li class="vuoto" style="border:0">Niente da segnalare per ora.</li>';
  }
  riempi('listaForza', forza);
  riempi('listaAttenzione', attenzione);
  riempi('listaCambi', cambi);
}

// -------------------------------------------------------------- grafici
var grafici = {};
var coloriBase = { griglia: 'rgba(255,255,255,.055)', testo: '#8b97a5' };

function opzioniBase(extra) {
  var base = {
    responsive: true, maintainAspectRatio: false,
    animation: { duration: 700, easing: 'easeOutQuart' },
    plugins: { legend: { labels: { color: '#c4cdd6', boxWidth: 14, font: { size: 12 } } } },
    scales: {}
  };
  return Object.assign(base, extra || {});
}
function asseY(titolo, formatta) {
  return { grid: { color: coloriBase.griglia }, ticks: { color: coloriBase.testo,
    callback: function (v) { return formatta ? formatta(v) : v; } },
    title: titolo ? { display: true, text: titolo, color: coloriBase.testo } : undefined };
}
function asseX() { return { grid: { display: false }, ticks: { color: coloriBase.testo } }; }

function creaGrafici(serie, gran) {
  var etich = serie.map(function (s) { return s.etichetta; });
  document.getElementById('notaAndamento').textContent = 'per ' + NOMI_GRAN[gran][0];

  // 1. Andamento: barre = numero, linea = valore
  datiGrafico('chartAndamento', 'bar', {
    labels: etich,
    datasets: [
      { type: 'line', label: 'Valore (€)', data: serie.map(function (s) { return s.valore; }),
        borderColor: '#f0b429', backgroundColor: 'rgba(240,180,41,.12)', yAxisID: 'y1',
        tension: .35, fill: true, pointRadius: 4, pointBackgroundColor: '#f0b429' },
      { label: 'N. preventivi', data: serie.map(function (s) { return s.n; }),
        backgroundColor: 'rgba(106,169,239,.55)', borderColor: '#6aa9ef', borderWidth: 1,
        borderRadius: 6, yAxisID: 'y' }
    ]
  }, opzioniBase({ scales: { x: asseX(),
      y: Object.assign(asseY('n. preventivi'), { beginAtZero: true, position: 'left',
        ticks: { color: coloriBase.testo, stepSize: 1 } }),
      y1: Object.assign(asseY('valore', fmtEuro.format), { beginAtZero: true, position: 'right',
        grid: { display: false } }) } }));

  // 2. Margini
  datiGrafico('chartMargini', 'bar', {
    labels: etich,
    datasets: [
      { label: 'Margine (€)', data: serie.map(function (s) { return Math.round(s.margine * 100) / 100; }),
        backgroundColor: serie.map(function (s) { return s.margine >= 0 ? 'rgba(78,201,123,.55)' : 'rgba(239,106,106,.6)'; }),
        borderRadius: 6, yAxisID: 'y' },
      { type: 'line', label: 'Margine medio (%)', data: serie.map(function (s) { return s.n ? Math.round(s.marginePct * 10) / 10 : null; }),
        borderColor: '#43c6b9', tension: .35, yAxisID: 'y1', pointRadius: 4,
        pointBackgroundColor: '#43c6b9', spanGaps: true }
    ]
  }, opzioniBase({ scales: { x: asseX(),
      y: Object.assign(asseY('€', fmtEuro.format), { position: 'left' }),
      y1: Object.assign(asseY('%', function (v) { return v + '%'; }),
        { position: 'right', grid: { display: false }, suggestedMax: 80 }) } }));

  // 3. Composizione costi (impilato)
  datiGrafico('chartCosti', 'bar', {
    labels: etich,
    datasets: [
      { label: 'Materiali', data: serie.map(function (s) { return s.materiali; }), backgroundColor: 'rgba(106,169,239,.6)', borderRadius: 4 },
      { label: 'Manodopera', data: serie.map(function (s) { return s.manodopera; }), backgroundColor: 'rgba(240,180,41,.6)', borderRadius: 4 },
      { label: 'Accessori', data: serie.map(function (s) { return s.accessori; }), backgroundColor: 'rgba(67,198,185,.55)', borderRadius: 4 }
    ]
  }, opzioniBase({ scales: { x: Object.assign(asseX(), { stacked: true }),
      y: Object.assign(asseY('€', fmtEuro.format), { stacked: true, beginAtZero: true }) } }));
}

function datiGrafico(id, tipo, dati, opzioni) {
  if (grafici[id]) {
    grafici[id].data = dati;
    grafici[id].options = opzioni;
    grafici[id].update();
    return;
  }
  grafici[id] = new Chart(document.getElementById(id).getContext('2d'),
    { type: tipo, data: dati, options: opzioni });
}

function creaGraficiStatici() {
  // Fasi manodopera (ciambella)
  var fasi = {};
  DATI.preventivi.forEach(function (p) {
    Object.keys(p.minuti).forEach(function (f) { fasi[f] = (fasi[f] || 0) + p.minuti[f]; });
  });
  var nomiFasi = Object.keys(fasi).filter(function (f) { return fasi[f] > 0; });
  datiGrafico('chartFasi', 'doughnut', {
    labels: nomiFasi.map(function (f) { return f + ' (' + Math.round(fasi[f]) + ' min)'; }),
    datasets: [{ data: nomiFasi.map(function (f) { return Math.round(fasi[f]); }),
      backgroundColor: ['#f0b429', '#6aa9ef', '#43c6b9', '#4ec97b', '#ef6a6a'],
      borderColor: '#151c25', borderWidth: 3, hoverOffset: 8 }]
  }, { responsive: true, maintainAspectRatio: false, cutout: '58%',
       animation: { duration: 800, easing: 'easeOutQuart' },
       plugins: { legend: { position: 'right', labels: { color: '#c4cdd6', font: { size: 12 } } } } });

  // Materiali piu' usati (m² e €)
  var mat = {};
  DATI.preventivi.forEach(function (p) {
    p.materiali.forEach(function (m) {
      if (!mat[m.nome]) mat[m.nome] = { mq: 0, costo: 0 };
      mat[m.nome].mq += m.mq; mat[m.nome].costo += m.costo;
    });
  });
  var topMat = Object.keys(mat).sort(function (a, b) { return mat[b].mq - mat[a].mq; }).slice(0, 8);
  datiGrafico('chartMateriali', 'bar', {
    labels: topMat,
    datasets: [{ label: 'm² utilizzati', data: topMat.map(function (n) { return Math.round(mat[n].mq * 100) / 100; }),
      backgroundColor: 'rgba(240,180,41,.55)', borderColor: '#f0b429', borderWidth: 1, borderRadius: 6 }]
  }, opzioniBase({ indexAxis: 'y',
      plugins: { legend: { display: false }, tooltip: { callbacks: {
        label: function (ctx) {
          var n = ctx.label; return fmtNum.format(mat[n].mq) + ' m² · costo ' + fmtEuro2.format(mat[n].costo);
        } } } },
      scales: { x: Object.assign(asseY('m²'), { beginAtZero: true }), y: asseX() } }));

  // Clienti per valore
  var cli = {};
  DATI.preventivi.forEach(function (p) { cli[p.cliente] = (cli[p.cliente] || 0) + p.valore; });
  var topCli = Object.keys(cli).sort(function (a, b) { return cli[b] - cli[a]; }).slice(0, 8);
  datiGrafico('chartClienti', 'bar', {
    labels: topCli,
    datasets: [{ label: 'Valore (€)', data: topCli.map(function (n) { return Math.round(cli[n]); }),
      backgroundColor: 'rgba(67,198,185,.5)', borderColor: '#43c6b9', borderWidth: 1, borderRadius: 6 }]
  }, opzioniBase({ indexAxis: 'y', plugins: { legend: { display: false } },
      scales: { x: Object.assign(asseY('€', fmtEuro.format), { beginAtZero: true }), y: asseX() } }));

  // Magazzino: giacenze vs scorta minima
  var magaz = DATI.magazzino.filter(function (m) { return m.giacenza > 0 || m.scorta_min > 0; })
    .sort(function (a, b) { return b.giacenza - a.giacenza; }).slice(0, 12);
  datiGrafico('chartMagazzino', 'bar', {
    labels: magaz.map(function (m) { return m.nome; }),
    datasets: [
      { label: 'Giacenza (m²)', data: magaz.map(function (m) { return m.giacenza; }),
        backgroundColor: magaz.map(function (m) {
          return m.scorta_min > 0 && m.giacenza < m.scorta_min ? 'rgba(239,106,106,.65)' : 'rgba(106,169,239,.55)';
        }), borderRadius: 6 },
      { type: 'line', label: 'Scorta minima', data: magaz.map(function (m) { return m.scorta_min || null; }),
        borderColor: '#ef6a6a', borderDash: [6, 4], pointStyle: 'rectRot', pointRadius: 5,
        pointBackgroundColor: '#ef6a6a', spanGaps: true, fill: false }
    ]
  }, opzioniBase({ scales: { x: asseX(), y: Object.assign(asseY('m²'), { beginAtZero: true }) } }));
}

// --------------------------------------------------------------- tabelle
function disegnaTabelle() {
  var ric = DATI.ricarichi.slice().sort(function (a, b) {
    return (a.pct === null ? 1e9 : a.pct) - (b.pct === null ? 1e9 : b.pct);
  });
  document.getElementById('tabRicarichi').innerHTML =
    '<tr><th>Materiale</th><th class="num">Prezzo vendita €/m²</th>' +
    '<th class="num">Prezzo fornitore €/m²</th><th class="num">Ricarico</th><th></th></tr>' +
    ric.map(function (r) {
      var tag = '', pctTxt = '—';
      if (r.pct !== null) {
        pctTxt = pct(r.pct);
        tag = r.pct < 50 ? '<span class="tag basso">basso</span>'
            : r.pct < 90 ? '<span class="tag medio">medio</span>'
            : '<span class="tag ok">ok</span>';
      }
      return '<tr><td>' + esc(r.nome) + '</td><td class="num">' + fmtEuro2.format(r.vendita) +
        '</td><td class="num">' + (r.acquisto > 0 ? fmtEuro2.format(r.acquisto) : '—') +
        '</td><td class="num">' + pctTxt + '</td><td>' + tag + '</td></tr>';
    }).join('');

  if (DATI.fornitori_confronto.length) {
    document.getElementById('sezFornitori').style.display = '';
    document.getElementById('tabFornitori').innerHTML =
      '<tr><th>Materiale</th><th>Fornitori e prezzi</th><th class="num">Risparmio scegliendo il migliore</th></tr>' +
      DATI.fornitori_confronto.map(function (f) {
        var prezzi = f.fornitori.map(function (x) { return x.prezzo; });
        var risparmio = Math.max.apply(null, prezzi) - Math.min.apply(null, prezzi);
        return '<tr><td>' + esc(f.materiale) + '</td><td>' +
          f.fornitori.map(function (x) { return esc(x.nome) + ' <b>' + fmtEuro2.format(x.prezzo) + '</b>'; }).join(' · ') +
          '</td><td class="num">' + (risparmio > 0 ? fmtEuro2.format(risparmio) + '/m²' : '—') + '</td></tr>';
      }).join('');
  }

  if (DATI.movimenti.length) {
    document.getElementById('sezMovimenti').style.display = '';
    document.getElementById('tabMovimenti').innerHTML =
      '<tr><th>Data</th><th>Tipo</th><th>Materiale</th><th class="num">Quantità m²</th><th>Fornitore</th><th>Note</th></tr>' +
      DATI.movimenti.slice(0, 12).map(function (m) {
        return '<tr><td>' + esc(m.data) + '</td><td><span class="tag ' + (m.tipo === 'carico' ? 'carico' : 'scarico') + '">' +
          esc(m.tipo) + '</span></td><td>' + esc(m.materiale) + '</td><td class="num">' + fmtNum.format(m.quantita) +
          '</td><td>' + esc(m.fornitore || '—') + '</td><td>' + esc(m.note) + '</td></tr>';
      }).join('');
  }
}

// ------------------------------------------------------------ notiziario
function disegnaNotiziario() {
  var box = document.getElementById('riquadroNotiziario');
  var n = DATI.notiziario;
  if (!n || !n.notizie || !n.notizie.length) {
    box.innerHTML = '<div class="suggerimento">Il notiziario di settore non è ancora attivo. ' +
      'Per attivarlo: esegui <b>python notiziario.py</b> nella cartella <b>analisi</b> ' +
      '(richiede una chiave API — vedi README.md). Raccoglie notizie mirate su fibra di carbonio, ' +
      'compositi e fornitori, con le fonti citate, e le mostra qui al prossimo report.</div>';
    return;
  }
  var testa = '<div class="sottotitolo" style="margin-bottom:12px">Aggiornato il ' + esc(n.generato_il || '') + '</div>';
  box.innerHTML = testa + n.notizie.map(function (x) {
    var fonte = x.fonte_url
      ? '<div class="fonte">Fonte: <a href="' + esc(x.fonte_url) + '" target="_blank" rel="noopener">' +
        esc(x.fonte_nome || x.fonte_url) + '</a></div>'
      : (x.fonte_nome ? '<div class="fonte">Fonte: ' + esc(x.fonte_nome) + '</div>' : '');
    var ril = x.perche_rilevante ? '<div class="rilevanza">Perché vi riguarda: ' + esc(x.perche_rilevante) + '</div>' : '';
    return '<div class="notizia"><h4>' + esc(x.titolo) + '</h4><p>' + esc(x.sintesi) + '</p>' + ril + fonte + '</div>';
  }).join('') + (n.commento ? '<div class="suggerimento" style="margin-top:8px">' + esc(n.commento) + '</div>' : '');
}

// --------------------------------------------------------------- regia
var granAttuale = 'mese';
function aggiornaTutto() {
  var serie = aggrega(granAttuale);
  disegnaKpi(serie, granAttuale);
  disegnaSintesi(serie, granAttuale);
  creaGrafici(serie, granAttuale);
}

document.getElementById('selettorePeriodo').addEventListener('click', function (e) {
  var btn = e.target.closest('button');
  if (!btn || btn.classList.contains('attivo')) return;
  this.querySelectorAll('button').forEach(function (b) { b.classList.remove('attivo'); });
  btn.classList.add('attivo');
  granAttuale = btn.dataset.gran;
  aggiornaTutto();
});

var osservatore = new IntersectionObserver(function (voci) {
  voci.forEach(function (v) { if (v.isIntersecting) v.target.classList.add('visibile'); });
}, { threshold: 0.08 });
document.querySelectorAll('.sezione').forEach(function (s) { osservatore.observe(s); });

if (typeof Chart === 'undefined') {
  document.body.insertAdjacentHTML('afterbegin',
    '<div style="background:#5a1f1f;color:#fff;padding:10px 16px;font-size:13px">' +
    'Libreria grafica non disponibile (serve internet al primo avvio per scaricarla). ' +
    'I numeri e le tabelle restano comunque visibili.</div>');
  document.querySelectorAll('.riquadro-grafico').forEach(function (r) { r.style.display = 'none'; });
  aggiornaTuttoSenzaGrafici();
} else {
  aggiornaTutto();
  creaGraficiStatici();
}
function aggiornaTuttoSenzaGrafici() {
  var serie = aggrega(granAttuale);
  disegnaKpi(serie, granAttuale);
  disegnaSintesi(serie, granAttuale);
}
disegnaTabelle();
disegnaNotiziario();
</script>
</body>
</html>
""")


# -------------------------------------------------------------------- main

def genera(db_path, apri_browser=True):
    conn = apri_db_sola_lettura(db_path)
    try:
        dati = {
            "preventivi": estrai_preventivi(conn),
            "magazzino": estrai_magazzino(conn),
            "fornitori_confronto": estrai_confronto_fornitori(conn),
            "movimenti": estrai_movimenti(conn),
            "notiziario": carica_notiziario(),
        }
    finally:
        conn.close()

    # Ricarichi: prezzo di vendita vs miglior prezzo di acquisto
    dati["ricarichi"] = []
    for m in dati["magazzino"]:
        ricarico = None
        if m["prezzo_acq"] > 0 and m["vendita"] > 0:
            ricarico = round((m["vendita"] - m["prezzo_acq"]) / m["prezzo_acq"] * 100, 1)
        dati["ricarichi"].append({"nome": m["nome"], "vendita": m["vendita"],
                                  "acquisto": m["prezzo_acq"], "pct": ricarico})

    chartjs = ottieni_chartjs()
    if chartjs:
        chart_tag = "<script>{}</script>".format(chartjs.replace("</", "<\\/"))
    else:
        chart_tag = '<script src="{}"></script>'.format(CHARTJS_URL)

    pagina = HTML_TEMPLATE.substitute(
        CHARTJS_TAG=chart_tag,
        GENERATO_IL=datetime.now().strftime("%d/%m/%Y %H:%M"),
        DB_PATH=html.escape(db_path),
        N_PREVENTIVI=len(dati["preventivi"]),
        JSON_DATI=json.dumps(dati, ensure_ascii=False).replace("</", "<\\/"),
    )

    os.makedirs(REPORT_DIR, exist_ok=True)
    nome = "report_{}.html".format(datetime.now().strftime("%Y%m%d_%H%M"))
    percorso = os.path.join(REPORT_DIR, nome)
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(pagina)
    ultimo = os.path.join(REPORT_DIR, "ultimo.html")
    with open(ultimo, "w", encoding="utf-8") as f:
        f.write(pagina)

    print("Report generato: {}".format(percorso))
    print("  Preventivi: {} | Materiali: {} | Movimenti: {}".format(
        len(dati["preventivi"]), len(dati["magazzino"]), len(dati["movimenti"])))
    if not chartjs:
        print("  Nota: Chart.js non in cache; il report usera' il CDN (serve internet alla visualizzazione).")
    if apri_browser:
        webbrowser.open("file://" + os.path.abspath(percorso))
    return percorso


def main():
    parser = argparse.ArgumentParser(description="Genera il Cruscotto Aziendale RCS (sola lettura)")
    parser.add_argument("--db", help="percorso del database (default: come l'app)")
    parser.add_argument("--no-open", action="store_true", help="non aprire il browser")
    args = parser.parse_args()
    db_path = trova_db_path(args.db)
    print("Database (sola lettura): {}".format(db_path or "(non configurato - vedi README)"))
    genera(db_path, apri_browser=not args.no_open)


if __name__ == "__main__":
    main()
