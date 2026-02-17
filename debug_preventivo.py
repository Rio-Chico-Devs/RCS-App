#!/usr/bin/env python3
"""Script diagnostico per individuare l'errore nell'apertura del preventivo"""
import sys
import traceback

print("=" * 60)
print("  DIAGNOSTICA APERTURA PREVENTIVO")
print("=" * 60)

# Test 1: Import
print("\n[1] Test imports...")
try:
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    print("    OK: PyQt5 importato")
except Exception as e:
    print(f"    ERRORE: {e}")
    sys.exit(1)

# Test 2: Database
print("\n[2] Test database...")
try:
    from database.db_manager import DatabaseManager
    db = DatabaseManager()
    print("    OK: Database connesso")
except Exception as e:
    print(f"    ERRORE: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Lista preventivi
print("\n[3] Test lista preventivi...")
try:
    import sqlite3
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, codice, nome_cliente FROM preventivi LIMIT 5")
        rows = cursor.fetchall()
    print(f"    OK: {len(rows)} preventivi trovati")
    for r in rows:
        print(f"        ID={r[0]}, codice={r[1]}, cliente={r[2]}")
    if not rows:
        print("    ATTENZIONE: Nessun preventivo nel database!")
        sys.exit(0)
except Exception as e:
    print(f"    ERRORE: {e}")
    traceback.print_exc()

# Test 4: get_preventivo_by_id
print("\n[4] Test get_preventivo_by_id...")
try:
    pid = rows[0][0]
    prev_data = db.get_preventivo_by_id(pid)
    print(f"    OK: Preventivo ID={pid} caricato")
    print(f"    Chiavi: {list(prev_data.keys())}")
except Exception as e:
    print(f"    ERRORE: {e}")
    traceback.print_exc()

# Test 5: Import PreventivoWindow
print("\n[5] Test import PreventivoWindow...")
try:
    from ui.preventivo_window import PreventivoWindow
    print("    OK: PreventivoWindow importato")
except Exception as e:
    print(f"    ERRORE: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 6: Creazione PreventivoWindow NUOVO
print("\n[6] Test PreventivoWindow modalita='nuovo'...")
try:
    win_nuovo = PreventivoWindow(db, None, modalita='nuovo')
    print("    OK: PreventivoWindow('nuovo') creata")
except Exception as e:
    print(f"    ERRORE: {e}")
    traceback.print_exc()

# Test 7: Creazione PreventivoWindow VISUALIZZA
print(f"\n[7] Test PreventivoWindow modalita='visualizza' (ID={pid})...")
try:
    win_vis = PreventivoWindow(db, None, preventivo_id=pid, modalita='visualizza')
    print("    OK: PreventivoWindow('visualizza') creata")
except Exception as e:
    print(f"    ERRORE: {e}")
    traceback.print_exc()

# Test 8: Creazione PreventivoWindow MODIFICA
print(f"\n[8] Test PreventivoWindow modalita='modifica' (ID={pid})...")
try:
    win_mod = PreventivoWindow(db, None, preventivo_id=pid, modalita='modifica')
    print("    OK: PreventivoWindow('modifica') creata")
except Exception as e:
    print(f"    ERRORE: {e}")
    traceback.print_exc()

# Test 9: VisualizzaPreventiviWindow
print("\n[9] Test VisualizzaPreventiviWindow...")
try:
    from ui.visualizza_preventivi_window import VisualizzaPreventiviWindow
    win_lista = VisualizzaPreventiviWindow(db)
    print("    OK: VisualizzaPreventiviWindow creata")
except Exception as e:
    print(f"    ERRORE: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("  DIAGNOSTICA COMPLETATA")
print("=" * 60)
print("\nSe tutti i test sono OK ma il problema persiste,")
print("prova ad avviare l'app da terminale con:")
print("  python main.py")
print("e copia qui l'errore che appare nel terminale.")
