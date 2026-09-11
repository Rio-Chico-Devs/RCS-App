#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controlli sulla FORMA del codice, non sul suo comportamento.

Perche' esistono
----------------
I test normali provano che il programma faccia la cosa giusta. Questi provano
che il programma sia scritto in modo da non poter nascondere i propri guasti.
Sono due cose diverse, e la seconda non si vede eseguendo il programma.

Il difetto che li ha fatti nascere: 49 punti in cui un errore veniva
intercettato e buttato via senza lasciare traccia ("except Exception: pass").
MITRE lo cataloga come debolezza a se' stante - CWE-390, "rilevare una
condizione di errore senza fare niente" - e CWE-396 mette in guardia sugli
intercettatori generici, che nascondono anche gli errori che non ci si
aspettava.

Il punto non e' togliere le protezioni: un programma che si ferma davanti a
ogni imprevisto e' peggio. Il punto e' che una protezione che fallisce in
SILENZIO e' peggio di nessuna protezione, perche' si continua a lavorare
credendo di essere coperti. Quindi: si intercetta, non ci si ferma, ma si
lascia traccia.

Esegui con:  python -m unittest tests.test_qualita_codice -v
"""

import ast
import os
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# I moduli che REALIZZANO le protezioni: database, backup, bozze, diagnostica.
# E' qui che il silenzio fa il danno peggiore.
CARTELLE_PROTEZIONE = ("database", "utils")

# Chiamate che possono fallire senza che importi a nessuno: si sta chiudendo
# o buttando via qualcosa, e il fallimento non cambia nulla per l'utente.
PULIZIA = {
    "close", "remove", "rmtree", "unlink", "rollback", "stop", "disconnect",
    # letture di contorno per la diagnostica: se non si sa il nome utente o lo
    # spazio libero, si scrive "?" e si va avanti
    "getuser", "getsize", "disk_usage", "GetDriveTypeW", "splitdrive",
    "abspath", "dirname", "join", "exists", "round",
    # formattazione di date per la sola visualizzazione
    "strftime", "fromisoformat",
}

# Unica eccezione motivata: il modulo che COSTRUISCE il registro. Segnalare li'
# un errore vorrebbe dire scriverlo nel registro che non funziona.
FILE_ESENTI = {os.path.join("utils", "logger.py")}


def _chiamate(corpo):
    trovate = set()
    for nodo in ast.walk(ast.Module(body=corpo, type_ignores=[])):
        if isinstance(nodo, ast.Call):
            nome = getattr(nodo.func, "attr", None) or getattr(nodo.func, "id", None)
            if nome:
                trovate.add(nome)
    return trovate


def intercettatori_muti():
    """Ogni 'except generico' che non fa NIENTE, nei moduli delle protezioni."""
    trovati = []
    for cartella in CARTELLE_PROTEZIONE:
        base = os.path.join(RADICE, cartella)
        if not os.path.isdir(base):
            continue
        for nome in sorted(os.listdir(base)):
            if not nome.endswith(".py"):
                continue
            relativo = os.path.join(cartella, nome)
            if relativo in FILE_ESENTI:
                continue
            percorso = os.path.join(base, nome)
            with open(percorso, encoding="utf-8") as f:
                albero = ast.parse(f.read())
            for nodo in ast.walk(albero):
                if not isinstance(nodo, ast.Try):
                    continue
                for gestore in nodo.handlers:
                    generico = (gestore.type is None
                                or getattr(gestore.type, "id", "") == "Exception")
                    muto = (len(gestore.body) == 1
                            and isinstance(gestore.body[0], ast.Pass))
                    if not (generico and muto):
                        continue
                    fuori = _chiamate(nodo.body) - PULIZIA
                    if fuori:
                        trovati.append("%s riga %d -> ingoia in silenzio: %s"
                                       % (relativo, gestore.lineno,
                                          ", ".join(sorted(fuori)[:5])))
    return trovati


class TestNienteErroriSilenziosi(unittest.TestCase):

    def test_le_protezioni_non_falliscono_in_silenzio(self):
        muti = intercettatori_muti()
        self.assertEqual(
            muti, [],
            "Questi punti intercettano un errore e non fanno nulla:\n  "
            + "\n  ".join(muti) +
            "\n\nNon serve togliere il try/except: serve annotare. "
            "Basta sostituire\n'except Exception:' + 'pass' con "
            "'except Exception as e:' e una riga\ndi registro. Una protezione "
            "che si rompe senza dirlo lascia credere\ndi essere protetti.")

    def test_il_controllo_sa_riconoscerli(self):
        """Se domani questo controllo smettesse di trovare qualcosa, passerebbe
        sempre e non proverebbe piu' niente. Qui gli si da' in pasto un caso
        costruito apposta per essere segnalato."""
        codice = ast.parse(
            "def f():\n"
            "    try:\n"
            "        salva_i_dati()\n"
            "    except Exception:\n"
            "        pass\n")
        gestore = [n for n in ast.walk(codice) if isinstance(n, ast.ExceptHandler)][0]
        prova = [n for n in ast.walk(codice) if isinstance(n, ast.Try)][0]
        self.assertTrue(gestore.type is not None)
        self.assertEqual(len(gestore.body), 1)
        self.assertIsInstance(gestore.body[0], ast.Pass)
        self.assertEqual(_chiamate(prova.body) - PULIZIA, {"salva_i_dati"},
                         "deve accorgersi che si stava proteggendo un'operazione vera")


class TestSqlNonCostruitoConIDatiDellUtente(unittest.TestCase):
    """Le poche istruzioni SQL costruite con la formattazione di stringhe
    devono usare SOLO nomi di tabella decisi nel codice, mai qualcosa che
    arrivi da chi usa il programma."""

    def test_nessun_dato_variabile_finisce_dentro_una_query(self):
        sospette = []
        for radice, cartelle, file in os.walk(RADICE):
            cartelle[:] = [c for c in cartelle
                           if c not in ("tests", "CruscottoAziendale",
                                        "__pycache__", "DashboardPage", ".git")]
            for nome in sorted(file):
                if not nome.endswith(".py"):
                    continue
                percorso = os.path.join(radice, nome)
                try:
                    with open(percorso, encoding="utf-8") as f:
                        albero = ast.parse(f.read())
                except SyntaxError:
                    continue
                for nodo in ast.walk(albero):
                    if not (isinstance(nodo, ast.Call)
                            and isinstance(nodo.func, ast.Attribute)
                            and nodo.func.attr in ("execute", "executemany")
                            and nodo.args):
                        continue
                    primo = nodo.args[0]
                    pezzi = []
                    if isinstance(primo, ast.JoinedStr):
                        pezzi = [v for v in primo.values
                                 if isinstance(v, ast.FormattedValue)]
                    elif (isinstance(primo, ast.Call)
                          and getattr(primo.func, "attr", "") == "format"):
                        pezzi = primo.args
                    if not pezzi:
                        continue
                    # Ammesso solo se ciò che viene inserito è un nome semplice
                    # (una variabile di ciclo su una tupla fissa) e non una
                    # espressione che possa venire da fuori.
                    for p in pezzi:
                        interno = p.value if isinstance(p, ast.FormattedValue) else p
                        if not isinstance(interno, (ast.Name, ast.Constant)):
                            sospette.append("%s:%d" % (
                                os.path.relpath(percorso, RADICE), nodo.lineno))
        self.assertEqual(sospette, [],
                         "SQL costruito con espressioni: verificare che non "
                         "arrivino dai dati dell'utente:\n  " + "\n  ".join(sospette))


if __name__ == "__main__":
    unittest.main(verbosity=2)
