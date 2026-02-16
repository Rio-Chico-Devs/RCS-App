#!/usr/bin/env python3
"""
Simulazione uso reale dell'applicazione RCS-App
Riproduce le operazioni che farebbe un utente passo dopo passo
"""
import sys, os, json, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from models.materiale import Materiale, MaterialeCalcolato
from models.preventivo import Preventivo

PASS = 0
FAIL = 0
ERRORS = []

def test(nome, condizione, dettaglio=""):
    global PASS, FAIL, ERRORS
    if condizione:
        PASS += 1
        print(f"  [OK] {nome}")
    else:
        FAIL += 1
        msg = f"  [FAIL] {nome}"
        if dettaglio:
            msg += f" -> {dettaglio}"
        print(msg)
        ERRORS.append(msg)

def sezione(titolo):
    print(f"\n{'='*70}")
    print(f"  {titolo}")
    print(f"{'='*70}")

# Setup
tmp_dir = tempfile.mkdtemp()
db_path = os.path.join(tmp_dir, "test_sim.db")
db = DatabaseManager(db_path)

# =====================================================
# SIMULAZIONE 1: Utente apre gestione materiali,
# modifica HS300 aggiungendo fornitore e dati magazzino
# =====================================================
sezione("SIM 1: Modifica materiale esistente con dati magazzino")

print("  Utente apre 'Gestisci Materiali'...")
all_mats = db.get_all_materiali()
test("Lista materiali caricata", len(all_mats) == 23, f"{len(all_mats)} materiali")

# Utente cerca e seleziona HS300
print("  Utente seleziona HS300...")
hs300 = None
for m in all_mats:
    if m[1] == "HS300":
        hs300 = m
        break
test("HS300 trovato", hs300 is not None)

# Simula unpack come fa on_materiale_selezionato
id_mat, nome, spessore, prezzo = hs300[:4]
fornitore = hs300[4] if len(hs300) > 4 else ""
prezzo_fornitore = hs300[5] if len(hs300) > 5 else 0.0
capacita_magazzino = hs300[6] if len(hs300) > 6 else 0.0
giacenza = hs300[7] if len(hs300) > 7 else 0.0
test("Unpack HS300 OK", nome == "HS300" and spessore == 0.3 and prezzo == 20.0)

# Utente compila i nuovi campi e salva
print("  Utente compila fornitore=Toray, prezzo_forn=15.50, capacita=200, giacenza=85...")
success = db.update_materiale(id_mat, nome, spessore, prezzo, "Toray", 15.50, 200.0, 85.0)
test("Salvataggio OK", success)

# Verifica
hs300_upd = db.get_materiale_by_id(id_mat)
test("Fornitore salvato", hs300_upd[4] == "Toray")
test("Prezzo fornitore salvato", hs300_upd[5] == 15.50)
test("Capacita salvata", hs300_upd[6] == 200.0)
test("Giacenza salvata", hs300_upd[7] == 85.0)

# Utente aggiorna anche CC200PL
cc200 = db.get_materiale_by_nome("CC200PL")
db.update_materiale(cc200[0], cc200[1], cc200[2], cc200[3], "Hexcel", 24.00, 150.0, 120.0)
cc200_upd = db.get_materiale_by_id(cc200[0])
test("CC200PL aggiornato", cc200_upd[4] == "Hexcel" and cc200_upd[7] == 120.0)

# =====================================================
# SIMULAZIONE 2: Utente crea un nuovo preventivo
# con 3 tele (materiali)
# =====================================================
sezione("SIM 2: Creazione preventivo con 3 tele")

preventivo = Preventivo()

# --- Materiale 1: HS300 ---
print("  Utente aggiunge tela 1: HS300, diametro=0, lunghezza=1000, giri=3...")
mat_info = db.get_materiale_by_id(hs300[0])
id_m, nome_m, spessore_m, prezzo_m = mat_info[:4]

m1 = MaterialeCalcolato()
m1.diametro = 0.0  # primo materiale
m1.lunghezza = 1000.0
m1.materiale_id = id_m
m1.materiale_nome = nome_m
m1.spessore = spessore_m
m1.costo_materiale = prezzo_m
m1.giri = 3
m1.ricalcola_tutto()

test("M1 diametro_finale calcolato", m1.diametro_finale > 0, f"d_f={m1.diametro_finale}")
test("M1 sviluppo calcolato", m1.sviluppo > 0, f"svil={m1.sviluppo:.2f}")
test("M1 costo_totale calcolato", m1.costo_totale > 0, f"costo={m1.costo_totale:.4f}")
test("M1 maggiorazione calcolata", m1.maggiorazione > m1.costo_totale, f"magg={m1.maggiorazione:.4f}")

result = preventivo.aggiungi_materiale(m1)
test("M1 aggiunto al preventivo", result)

# --- Materiale 2: CC200PL (diametro = m1.diametro_finale) ---
print(f"  Utente aggiunge tela 2: CC200PL, diametro={m1.diametro_finale}, lunghezza=1000, giri=2...")
cc_info = db.get_materiale_by_id(cc200[0])
id_cc, nome_cc, spessore_cc, prezzo_cc = cc_info[:4]

m2 = MaterialeCalcolato()
m2.diametro = m1.diametro_finale  # catena
m2.lunghezza = 1000.0
m2.materiale_id = id_cc
m2.materiale_nome = nome_cc
m2.spessore = spessore_cc
m2.costo_materiale = prezzo_cc
m2.giri = 2
m2.ricalcola_tutto()

test("M2 diametro iniziale = M1 finale", m2.diametro == m1.diametro_finale)
test("M2 diametro_finale > M2 diametro", m2.diametro_finale > m2.diametro)
preventivo.aggiungi_materiale(m2)

# --- Materiale 3: HS300 di nuovo ---
print(f"  Utente aggiunge tela 3: HS300, diametro={m2.diametro_finale}, lunghezza=1000, giri=4...")
m3 = MaterialeCalcolato()
m3.diametro = m2.diametro_finale
m3.lunghezza = 1000.0
m3.materiale_id = id_m
m3.materiale_nome = nome_m
m3.spessore = spessore_m
m3.costo_materiale = prezzo_m
m3.giri = 4
m3.ricalcola_tutto()

test("M3 catena diametri corretta", m3.diametro == m2.diametro_finale)
preventivo.aggiungi_materiale(m3)

test("Preventivo ha 3 materiali", len(preventivo.materiali_calcolati) == 3)

# Utente compila tempi e costi
print("  Utente compila tempi: taglio=15, avvolg=25, pulizia=10, rettifica=20, imball=8...")
preventivo.minuti_taglio = 15.0
preventivo.minuti_avvolgimento = 25.0
preventivo.minuti_pulizia = 10.0
preventivo.minuti_rettifica = 20.0
preventivo.minuti_imballaggio = 8.0
preventivo.costi_accessori = 35.0
preventivo.ricalcola_tutto()

test("Tot mano opera = 78 min", preventivo.tot_mano_opera == 78.0, f"got {preventivo.tot_mano_opera}")
test("Costo materiali > 0", preventivo.costo_totale_materiali > 0, f"€{preventivo.costo_totale_materiali:.2f}")
test("Subtotale > costo materiali", preventivo.subtotale > preventivo.costo_totale_materiali)
test("Preventivo finale > 0", preventivo.preventivo_finale > 0, f"€{preventivo.preventivo_finale:.2f}")

# Utente salva
print("  Utente clicca 'Salva Preventivo'...")
save_data = preventivo.to_dict()
save_data.update({
    'nome_cliente': 'Mario Rossi',
    'numero_ordine': 'ORD-2026-001',
    'misura': '50x1200',
    'descrizione': 'Tubo carbonio racing',
    'codice': 'TC-001',
    'prezzo_cliente': preventivo.preventivo_finale
})
prev_id = db.save_preventivo(save_data)
test("Preventivo salvato con ID", prev_id > 0, f"ID={prev_id}")

# =====================================================
# SIMULAZIONE 3: Utente visualizza e modifica preventivo
# =====================================================
sezione("SIM 3: Caricamento e modifica preventivo esistente")

print(f"  Utente apre preventivo #{prev_id}...")
loaded = db.get_preventivo_by_id(prev_id)
test("Preventivo caricato", loaded is not None)
test("Cliente corretto", loaded['nome_cliente'] == 'Mario Rossi')
test("Misura corretta", loaded['misura'] == '50x1200')

# Simula caricamento materiali come fa PreventivoWindow.carica_preventivo_esistente
print("  Caricamento materiali dal preventivo...")
p_loaded = Preventivo()
p_loaded.costi_accessori = float(loaded.get('costi_accessori', 0.0))
p_loaded.minuti_taglio = float(loaded.get('minuti_taglio', 0.0))
p_loaded.minuti_avvolgimento = float(loaded.get('minuti_avvolgimento', 0.0))
p_loaded.minuti_pulizia = float(loaded.get('minuti_pulizia', 0.0))
p_loaded.minuti_rettifica = float(loaded.get('minuti_rettifica', 0.0))
p_loaded.minuti_imballaggio = float(loaded.get('minuti_imballaggio', 0.0))
p_loaded.prezzo_cliente = float(loaded.get('prezzo_cliente', 0.0))

materiali_data = loaded.get('materiali_utilizzati', [])
for mat_data in materiali_data:
    materiale = MaterialeCalcolato()
    materiale.diametro = mat_data.get('diametro', 0.0)
    materiale.lunghezza = mat_data.get('lunghezza', 0.0)
    materiale.materiale_id = mat_data.get('materiale_id', None)
    materiale.materiale_nome = mat_data.get('materiale_nome', "")
    materiale.giri = mat_data.get('giri', 0)
    materiale.spessore = mat_data.get('spessore', 0.0)
    materiale.diametro_finale = mat_data.get('diametro_finale', 0.0)
    materiale.sviluppo = mat_data.get('sviluppo', mat_data.get('stratifica', 0.0))
    materiale.arrotondamento_manuale = mat_data.get('arrotondamento_manuale', 0.0)
    materiale.costo_materiale = mat_data.get('costo_materiale', 0.0)
    materiale.lunghezza_utilizzata = mat_data.get('lunghezza_utilizzata', 0.0)
    materiale.costo_totale = mat_data.get('costo_totale', 0.0)
    materiale.maggiorazione = mat_data.get('maggiorazione', 0.0)
    p_loaded.materiali_calcolati.append(materiale)

p_loaded.ricalcola_tutto()

test("3 materiali caricati", len(p_loaded.materiali_calcolati) == 3)
test("Catena diametri preservata",
     p_loaded.materiali_calcolati[1].diametro == p_loaded.materiali_calcolati[0].diametro_finale,
     f"m1.d={p_loaded.materiali_calcolati[1].diametro} vs m0.df={p_loaded.materiali_calcolati[0].diametro_finale}")
test("Valori ricalcolati coerenti",
     abs(p_loaded.preventivo_finale - preventivo.preventivo_finale) < 0.01,
     f"orig={preventivo.preventivo_finale:.2f} loaded={p_loaded.preventivo_finale:.2f}")
test("Tempi preservati", p_loaded.minuti_taglio == 15.0)

# Utente modifica: aggiunge costi accessori e risalva
print("  Utente modifica costi accessori da 35 a 50 e risalva...")
p_loaded.costi_accessori = 50.0
p_loaded.ricalcola_tutto()
save_data2 = p_loaded.to_dict()
save_data2.update({
    'nome_cliente': 'Mario Rossi',
    'numero_ordine': 'ORD-2026-001',
    'misura': '50x1200',
    'descrizione': 'Tubo carbonio racing',
    'codice': 'TC-001',
    'prezzo_cliente': p_loaded.preventivo_finale
})
success_upd = db.update_preventivo(prev_id, save_data2)
test("Update preventivo OK", success_upd)

# Verifica storico
loaded_after = db.get_preventivo_by_id(prev_id)
test("Storico modifiche creato", len(loaded_after['storico_modifiche']) == 1)
test("Costi accessori aggiornati", loaded_after['costi_accessori'] == 50.0)

# =====================================================
# SIMULAZIONE 4: Eliminazione materiale dal mezzo
# e ricalcolo catena diametri
# =====================================================
sezione("SIM 4: Elimina tela 2/3 e ricalcola diametri")

print(f"  Preventivo ha {len(p_loaded.materiali_calcolati)} materiali")
print(f"  Diametri: {[f'{m.diametro:.2f}->{m.diametro_finale:.2f}' for m in p_loaded.materiali_calcolati]}")

# Salva valori prima
d0_prima = p_loaded.materiali_calcolati[0].diametro
df0_prima = p_loaded.materiali_calcolati[0].diametro_finale
d2_prima = p_loaded.materiali_calcolati[2].diametro

# Utente seleziona checkbox materiale 2 (indice 1) e clicca elimina
print("  Utente flagga materiale #2 e clicca 'Elimina Selezionati'...")
checked = [1]  # indice 1
primo_eliminato = min(checked)
for indice in sorted(checked, reverse=True):
    p_loaded.rimuovi_materiale(indice)

# Ricalcolo come fa elimina_materiali_selezionati
if p_loaded.materiali_calcolati:
    if primo_eliminato == 0:
        p_loaded.materiali_calcolati[0].diametro = 0.0
        p_loaded.materiali_calcolati[0].ricalcola_tutto()
        # ricalcola_diametri_successivi(0)
        for i in range(1, len(p_loaded.materiali_calcolati)):
            p_loaded.materiali_calcolati[i].diametro = p_loaded.materiali_calcolati[i-1].diametro_finale
            p_loaded.materiali_calcolati[i].ricalcola_tutto()
    else:
        # ricalcola_diametri_successivi(primo_eliminato - 1)
        for i in range(primo_eliminato, len(p_loaded.materiali_calcolati)):
            p_loaded.materiali_calcolati[i].diametro = p_loaded.materiali_calcolati[i-1].diametro_finale
            p_loaded.materiali_calcolati[i].ricalcola_tutto()
    p_loaded.ricalcola_costo_totale_materiali()

test("2 materiali rimasti", len(p_loaded.materiali_calcolati) == 2)
test("M1 invariato", p_loaded.materiali_calcolati[0].diametro == d0_prima)
test("M1 diametro_finale invariato", p_loaded.materiali_calcolati[0].diametro_finale == df0_prima)
test("M2(ex-3) prende diametro da M1",
     p_loaded.materiali_calcolati[1].diametro == p_loaded.materiali_calcolati[0].diametro_finale,
     f"got d={p_loaded.materiali_calcolati[1].diametro}, expected {p_loaded.materiali_calcolati[0].diametro_finale}")
print(f"  Diametri dopo: {[f'{m.diametro:.2f}->{m.diametro_finale:.2f}' for m in p_loaded.materiali_calcolati]}")

# =====================================================
# SIMULAZIONE 5: Eliminazione primo materiale
# =====================================================
sezione("SIM 5: Elimina primo materiale, nuovo primo riparte da 0")

# Ricostruisci 3 materiali
p5 = Preventivo()
for i in range(3):
    m = MaterialeCalcolato()
    m.lunghezza = 1000.0
    m.spessore = 0.25
    m.giri = 2
    m.costo_materiale = 30.0
    m.materiale_nome = f"Tela_{i+1}"
    m.diametro = p5.materiali_calcolati[-1].diametro_finale if p5.materiali_calcolati else 0.0
    m.ricalcola_tutto()
    p5.aggiungi_materiale(m)

print(f"  Diametri: {[f'{m.diametro:.2f}->{m.diametro_finale:.2f}' for m in p5.materiali_calcolati]}")

# Elimina primo (indice 0)
print("  Utente elimina tela #1 (indice 0)...")
checked = [0]
primo_eliminato = min(checked)
for indice in sorted(checked, reverse=True):
    p5.rimuovi_materiale(indice)

if p5.materiali_calcolati:
    if primo_eliminato == 0:
        p5.materiali_calcolati[0].diametro = 0.0
        p5.materiali_calcolati[0].ricalcola_tutto()
        for i in range(1, len(p5.materiali_calcolati)):
            p5.materiali_calcolati[i].diametro = p5.materiali_calcolati[i-1].diametro_finale
            p5.materiali_calcolati[i].ricalcola_tutto()
    p5.ricalcola_costo_totale_materiali()

test("2 materiali rimasti", len(p5.materiali_calcolati) == 2)
test("Nuovo primo parte da 0", p5.materiali_calcolati[0].diametro == 0.0)
test("Nuovo primo d_f=1.0", abs(p5.materiali_calcolati[0].diametro_finale - 1.0) < 0.001)
test("Secondo prende da primo", p5.materiali_calcolati[1].diametro == p5.materiali_calcolati[0].diametro_finale)
test("Catena corretta: ultimo d_f=2.0", abs(p5.materiali_calcolati[1].diametro_finale - 2.0) < 0.001)
print(f"  Diametri dopo: {[f'{m.diametro:.2f}->{m.diametro_finale:.2f}' for m in p5.materiali_calcolati]}")

# =====================================================
# SIMULAZIONE 6: Eliminazione multipla (1, 3, 5 su 6)
# =====================================================
sezione("SIM 6: Eliminazione multipla non contigua")

p6 = Preventivo()
for i in range(6):
    m = MaterialeCalcolato()
    m.lunghezza = 1000.0
    m.spessore = 0.25
    m.giri = 2
    m.costo_materiale = 30.0
    m.materiale_nome = f"Tela_{i+1}"
    m.diametro = p6.materiali_calcolati[-1].diametro_finale if p6.materiali_calcolati else 0.0
    m.ricalcola_tutto()
    p6.aggiungi_materiale(m)

print(f"  6 tele, diametri: {[f'{m.diametro:.1f}->{m.diametro_finale:.1f}' for m in p6.materiali_calcolati]}")

# Elimina indici 0, 2, 4 (tele 1, 3, 5)
print("  Utente flagga tele #1, #3, #5 (indici 0, 2, 4) e elimina...")
checked = [0, 2, 4]
primo_eliminato = min(checked)
for indice in sorted(checked, reverse=True):
    p6.rimuovi_materiale(indice)

if p6.materiali_calcolati:
    if primo_eliminato == 0:
        p6.materiali_calcolati[0].diametro = 0.0
        p6.materiali_calcolati[0].ricalcola_tutto()
        for i in range(1, len(p6.materiali_calcolati)):
            p6.materiali_calcolati[i].diametro = p6.materiali_calcolati[i-1].diametro_finale
            p6.materiali_calcolati[i].ricalcola_tutto()
    else:
        for i in range(primo_eliminato, len(p6.materiali_calcolati)):
            p6.materiali_calcolati[i].diametro = p6.materiali_calcolati[i-1].diametro_finale
            p6.materiali_calcolati[i].ricalcola_tutto()
    p6.ricalcola_costo_totale_materiali()

test("3 materiali rimasti", len(p6.materiali_calcolati) == 3)
test("Primo parte da 0", p6.materiali_calcolati[0].diametro == 0.0)
# Rimasti: ex-Tela_2, ex-Tela_4, ex-Tela_6 -> tutti con spessore=0.25, giri=2
# Catena: 0->1, 1->2, 2->3
test("Catena 0->1->2->3",
     abs(p6.materiali_calcolati[2].diametro_finale - 3.0) < 0.001,
     f"got {p6.materiali_calcolati[2].diametro_finale}")
test("Nomi rimasti corretti",
     [m.materiale_nome for m in p6.materiali_calcolati] == ['Tela_2', 'Tela_4', 'Tela_6'])
print(f"  Diametri dopo: {[f'{m.diametro:.1f}->{m.diametro_finale:.1f}' for m in p6.materiali_calcolati]}")

# =====================================================
# SIMULAZIONE 7: Magazzino - carico, scarico, verifica
# =====================================================
sezione("SIM 7: Gestione magazzino completa")

# Setup: HS300 ha giacenza=85, capacita=200 (dalla sim 1)
hs300_mag = db.get_materiale_by_nome("HS300")
test("HS300 giacenza iniziale 85", hs300_mag[7] == 85.0, f"got {hs300_mag[7]}")

# Utente fa carico di 50 m²
print("  Utente fa carico 50 m² di HS300...")
db.registra_movimento(hs300_mag[0], 'carico', 50.0, "Arrivo lotto #A123")
hs300_after = db.get_materiale_by_id(hs300_mag[0])
test("Giacenza dopo carico: 135", hs300_after[7] == 135.0, f"got {hs300_after[7]}")

# Utente fa scarico di 20 m²
print("  Utente fa scarico 20 m² di HS300...")
db.registra_movimento(hs300_mag[0], 'scarico', 20.0, "Produzione ordine ORD-001")
hs300_after2 = db.get_materiale_by_id(hs300_mag[0])
test("Giacenza dopo scarico: 115", hs300_after2[7] == 115.0, f"got {hs300_after2[7]}")

# Carico CC200PL
print("  Utente fa carico 30 m² di CC200PL...")
cc200_mag = db.get_materiale_by_nome("CC200PL")
db.registra_movimento(cc200_mag[0], 'carico', 30.0, "Lotto B456")
cc200_after = db.get_materiale_by_id(cc200_mag[0])
test("CC200PL giacenza: 150", cc200_after[7] == 150.0, f"got {cc200_after[7]}")

# Scarico CC200PL
db.registra_movimento(cc200_mag[0], 'scarico', 45.0, "Produzione ORD-002")
cc200_after2 = db.get_materiale_by_id(cc200_mag[0])
test("CC200PL giacenza: 105", cc200_after2[7] == 105.0, f"got {cc200_after2[7]}")

# Verifica storico movimenti
print("  Utente apre storico movimenti HS300...")
movimenti_hs = db.get_movimenti_per_materiale(hs300_mag[0])
test("HS300: 2 movimenti", len(movimenti_hs) == 2, f"got {len(movimenti_hs)}")
test("Ultimo mov: scarico 20", movimenti_hs[0][1] == 'scarico' and movimenti_hs[0][2] == 20.0)
test("Primo mov: carico 50", movimenti_hs[1][1] == 'carico' and movimenti_hs[1][2] == 50.0)

# Verifica scorte ordinate
print("  Utente apre vista scorte ordinate per 'basse prima'...")
scorte = db.get_scorte('giacenza_asc')
test("Scorte caricate", len(scorte) > 0)

# Calcola percentuali
for s in scorte:
    s_id, s_nome, s_giacenza, s_capacita, s_fornitore, s_prezzo_f = s
    if s_capacita > 0:
        perc = (s_giacenza / s_capacita) * 100
    else:
        perc = 0
    # Solo per HS300 e CC200PL verifica
    if s_nome == "HS300":
        test(f"HS300 scorta {perc:.0f}%", abs(perc - 57.5) < 1, f"115/200 = {perc:.1f}%")
    elif s_nome == "CC200PL":
        test(f"CC200PL scorta {perc:.0f}%", abs(perc - 70.0) < 1, f"105/150 = {perc:.1f}%")

# Test consumi periodo
print("  Utente apre tab 'Consumi e Spese' per il periodo corrente...")
consumi = db.get_consumi_periodo("2000-01-01", "2099-12-31")
test("Consumi trovati", len(consumi) >= 2)

for c in consumi:
    c_id, c_nome, c_prezzo_f, c_totale = c
    spesa = c_totale * c_prezzo_f
    if c_nome == "HS300":
        test(f"HS300 consumo: 20 m²", c_totale == 20.0, f"got {c_totale}")
        test(f"HS300 spesa: €{spesa:.2f}", abs(spesa - 20.0 * 15.50) < 0.01, f"got {spesa}")
    elif c_nome == "CC200PL":
        test(f"CC200PL consumo: 45 m²", c_totale == 45.0, f"got {c_totale}")
        test(f"CC200PL spesa: €{spesa:.2f}", abs(spesa - 45.0 * 24.0) < 0.01, f"got {spesa}")

# =====================================================
# SIMULAZIONE 8: Nuovo materiale da dialog
# =====================================================
sezione("SIM 8: Creazione nuovo materiale da dialog")

print("  Utente clicca 'Nuovo Materiale'...")
print("  Compila: nome=KEVLAR49, spess=0.12, prezzo=55, forn=DuPont, p_forn=42, cap=80, giac=80...")
new_id = db.add_materiale("KEVLAR49", 0.12, 55.0, "DuPont", 42.0, 80.0, 80.0)
test("Nuovo materiale creato", new_id is not None and new_id is not False)

# Verifica nella lista
all_after = db.get_all_materiali()
kevlar = [m for m in all_after if m[1] == "KEVLAR49"]
test("KEVLAR49 nella lista", len(kevlar) == 1)
test("KEVLAR49 dati corretti", kevlar[0][4] == "DuPont" and kevlar[0][5] == 42.0)

# Usalo in un preventivo
print("  Utente usa KEVLAR49 in un nuovo preventivo...")
mk = MaterialeCalcolato()
mk.diametro = 0.0
mk.lunghezza = 800.0
mk.materiale_id = new_id
mk.materiale_nome = "KEVLAR49"
mk.spessore = 0.12
mk.costo_materiale = 55.0
mk.giri = 5
mk.ricalcola_tutto()
test("KEVLAR49 calcoli OK", mk.diametro_finale > 0 and mk.costo_totale > 0)

# =====================================================
# SIMULAZIONE 9: Preventivo con 25 tele (scalabilita)
# =====================================================
sezione("SIM 9: Preventivo con 25 tele")

p25 = Preventivo()
for i in range(25):
    m = MaterialeCalcolato()
    m.lunghezza = 1000.0
    m.spessore = 0.15
    m.giri = 2
    m.costo_materiale = 20.0
    m.materiale_nome = f"Tela_{i+1}"
    m.diametro = p25.materiali_calcolati[-1].diametro_finale if p25.materiali_calcolati else 0.0
    m.ricalcola_tutto()
    p25.aggiungi_materiale(m)

test("25 materiali aggiunti", len(p25.materiali_calcolati) == 25)

# Verifica catena completa
catena_ok = True
for i in range(1, 25):
    if abs(p25.materiali_calcolati[i].diametro - p25.materiali_calcolati[i-1].diametro_finale) > 0.001:
        catena_ok = False
        break
test("Catena 25 diametri corretta", catena_ok)

# Diametro finale atteso: ogni materiale aggiunge 0.15 * 2 * 2 = 0.6mm
# Dopo 25: 25 * 0.6 = 15.0
test("Diametro finale 25a tela = 15.0",
     abs(p25.materiali_calcolati[24].diametro_finale - 15.0) < 0.001,
     f"got {p25.materiali_calcolati[24].diametro_finale}")

p25.minuti_taglio = 30.0
p25.minuti_avvolgimento = 60.0
p25.minuti_pulizia = 15.0
p25.minuti_rettifica = 25.0
p25.minuti_imballaggio = 10.0
p25.costi_accessori = 100.0
p25.ricalcola_tutto()

test("Preventivo 25 tele: finale > 0", p25.preventivo_finale > 0, f"€{p25.preventivo_finale:.2f}")

# Salva e ricarica
save25 = p25.to_dict()
save25.update({
    'nome_cliente': 'Azienda Racing',
    'numero_ordine': 'ORD-BIG-001',
    'misura': '25x2000',
    'descrizione': '25 strati tubo racing',
    'codice': 'BIG-001',
    'prezzo_cliente': p25.preventivo_finale
})
id25 = db.save_preventivo(save25)
loaded25 = db.get_preventivo_by_id(id25)
test("Preventivo 25 tele salvato/caricato", len(loaded25['materiali_utilizzati']) == 25)

# =====================================================
# SIMULAZIONE 10: Modifica materiale e verifica in combo
# =====================================================
sezione("SIM 10: Aggiornamento prezzi materiali nel preventivo aperto")

print("  Utente cambia prezzo HS300 da 20 a 25...")
db.update_prezzo_materiale(hs300_mag[0], 25.0)
hs_check = db.get_materiale_by_id(hs300_mag[0])
test("Prezzo aggiornato a 25", hs_check[3] == 25.0)
test("Fornitore NON modificato", hs_check[4] == "Toray")
test("Giacenza NON modificata", hs_check[7] == 115.0)

# Simula aggiorna_prezzi_materiali
print("  Simula 'Aggiorna Prezzi' nel preventivo aperto...")
for mat_calc in p_loaded.materiali_calcolati:
    mat_db = db.get_materiale_by_nome(mat_calc.materiale_nome)
    if mat_db:
        mat_calc.costo_materiale = mat_db[3]
        mat_calc.ricalcola_tutto()
p_loaded.ricalcola_costo_totale_materiali()
p_loaded.ricalcola_tutto()
test("Prezzi aggiornati nel preventivo", p_loaded.preventivo_finale > 0)

# =====================================================
# SIMULAZIONE 11: Elimina preventivo e revisioni
# =====================================================
sezione("SIM 11: Eliminazione preventivo")

print(f"  Utente elimina preventivo #{prev_id}...")
success_del = db.delete_preventivo_e_revisioni(prev_id)
test("Eliminazione OK", success_del)
loaded_del = db.get_preventivo_by_id(prev_id)
test("Preventivo non piu' trovato", loaded_del is None)

# =====================================================
# SIMULAZIONE 12: Verifica integrità database finale
# =====================================================
sezione("SIM 12: Verifica integrita' database finale")

all_prev = db.get_all_preventivi()
test("Preventivi rimasti coerenti", len(all_prev) >= 1)  # almeno il 25-tele

all_mats_final = db.get_all_materiali()
test("Materiali integri", len(all_mats_final) >= 24)  # 23 default + KEVLAR49

# Verifica che ogni materiale ha 8 campi
test("Tutti i materiali hanno 8 campi", all(len(m) == 8 for m in all_mats_final))

# Verifica che le scorte funzionano
scorte_final = db.get_scorte('nome')
test("Scorte funzionanti", len(scorte_final) > 0)

# Cleanup
shutil.rmtree(tmp_dir)

# =====================================================
# RISULTATI
# =====================================================
print(f"\n{'='*70}")
print(f"  RISULTATI SIMULAZIONE COMPLETA")
print(f"{'='*70}")
print(f"  Totale test: {PASS + FAIL}")
print(f"  Passati:     {PASS}")
print(f"  Falliti:     {FAIL}")

if ERRORS:
    print(f"\n  ERRORI:")
    for e in ERRORS:
        print(f"    {e}")
else:
    print(f"\n  TUTTE LE SIMULAZIONI PASSATE!")

print(f"{'='*70}")
sys.exit(1 if FAIL > 0 else 0)
