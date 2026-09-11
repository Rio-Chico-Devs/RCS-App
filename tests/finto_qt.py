#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Un PyQt5 finto, per poter ESEGUIRE la logica delle finestre.

Perche' esiste
--------------
PyQt5 non e' installabile nell'ambiente di sviluppo, e i difetti che sono
sfuggiti alle verifiche stavano tutti li': un nome di metodo sbagliato o un
parametro che non combacia si scoprirebbe solo in produzione, davanti
all'utente.

Questo modulo mette al posto di PyQt5 delle classi finte che accettano
qualunque cosa. Non disegna nulla e non prova che l'aspetto sia giusto: prova
che il CODICE GIRA - che i metodi esistano, che i parametri combacino, che il
flusso arrivi in fondo. E' esattamente cio' che mancava.

Le finestre di dialogo non si aprono: rispondono da sole con la scelta
impostata in RispostaAutomatica, cosi' si possono provare anche i percorsi
"l'utente ha risposto di si'".
"""

import sys
import types


class RispostaAutomatica:
    """Cosa devono rispondere le finte finestre di dialogo."""
    scelta_pulsante = 0          # indice del pulsante da "premere"
    risposta_standard = 16384    # QMessageBox.Yes
    dialoghi_mostrati = []       # per controllare cosa e' stato chiesto

    @classmethod
    def azzera(cls):
        cls.scelta_pulsante = 0
        cls.risposta_standard = 16384
        cls.dialoghi_mostrati = []


class _MetaPermissiva(type):
    """Permette anche le costanti di classe (QComboBox.NoInsert, QFrame.HLine,
    QHeaderView.Stretch...): sono decine e non ha senso elencarle.

    Il valore e' inventato ma COSTANTE: la stessa costante letta due volte
    deve dare lo stesso numero. Prima non era cosi' - il contatore avanzava a
    ogni lettura - e il codice che accende un flag e poi lo spegne
    (windowFlags() | X ... & ~X) non tornava mai al punto di partenza. Il
    difetto era mascherato dal caso: con certi numeri consecutivi il conto
    tornava per combinazione, e bastava aggiungere una classe qui dentro per
    far fallire un test che non c'entrava niente."""

    _contatore = [0]
    _costanti = {}

    def __getattr__(cls, nome):
        if nome.startswith("__"):
            raise AttributeError(nome)
        chiave = (cls.__name__, nome)
        if chiave not in cls._costanti:
            cls._contatore[0] += 1
            cls._costanti[chiave] = cls._contatore[0]
        return cls._costanti[chiave]


class _Base(metaclass=_MetaPermissiva):
    """Oggetto che accetta qualunque metodo e qualunque attributo."""

    def __init__(self, *args, **kwargs):
        self._figli = []

    def __getattr__(self, nome):
        # Deve valere sia per i metodi (widget.setText("x")) sia per i segnali
        # (pulsante.clicked.connect(...)): quindi si restituisce un oggetto che
        # e' a sua volta richiamabile e accetta qualunque attributo.
        return _Base()

    def __call__(self, *args, **kwargs):
        return _Base()

    def __bool__(self):
        return True

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0

    # Molti metodi di Qt restituiscono numeri che il codice poi confronta
    # (per esempio findText() >= 0). Qui l'oggetto finto si comporta come -1,
    # cioe' "non trovato": e' il caso che porta il codice a percorrere il ramo
    # alternativo, che e' proprio quello che vale la pena esercitare.
    _VALORE = -1

    def __int__(self):
        return self._VALORE

    def __index__(self):
        return self._VALORE

    def __float__(self):
        return float(self._VALORE)

    def __eq__(self, altro):
        return altro is self

    def __ne__(self, altro):
        return altro is not self

    def __hash__(self):
        return id(self)

    def __lt__(self, altro):
        return self._VALORE < altro

    def __le__(self, altro):
        return self._VALORE <= altro

    def __gt__(self, altro):
        return self._VALORE > altro

    def __ge__(self, altro):
        return self._VALORE >= altro

    # ATTENZIONE: qui NON si puo' usare getattr(self, nome, predefinito).
    # __getattr__ qui sopra risponde a QUALUNQUE attributo mancante, quindi il
    # valore predefinito non entra mai in gioco e si riceve un _Base al posto
    # di una stringa. Si legge direttamente da __dict__.
    def isVisible(self):
        return self.__dict__.get("_visibile", True)

    def show(self):
        self._visibile = True

    def hide(self):
        self._visibile = False

    # Le etichette devono RICORDARE il testo che ricevono: senza, non si puo'
    # provare cosa l'utente legge sullo schermo - per esempio se al posto di
    # un totale non calcolabile compare un trattino invece del numero vecchio.
    def setText(self, testo):
        self._testo = testo

    def text(self):
        memorizzato = self.__dict__.get("_testo", "")
        return memorizzato if isinstance(memorizzato, str) else ""

    def currentText(self):
        return ""

    def currentData(self):
        # Come una casella a discesa su "Tutti": nessun valore associato.
        return None

    def toString(self, *args):
        return ""

    def currentIndex(self):
        return 0

    def rowCount(self):
        return 0

    def columnCount(self):
        return 0

    def value(self):
        return 0.0

    def count(self):
        return 0

    def font(self):
        return _Font()

    def fontMetrics(self):
        return _Metriche()

    def tabText(self, i):
        return ""

    def selectionModel(self):
        return None

    def findChildren(self, tipo, *args, **kwargs):
        """Cerca fra gli oggetti creati dentro questa finestra."""
        trovati = []
        for valore in vars(self).values():
            if isinstance(valore, tipo):
                trovati.append(valore)
            elif isinstance(valore, _TabWidget):
                barra = valore.tabBar()
                if isinstance(barra, tipo):
                    trovati.append(barra)
        return trovati

    def currentItem(self):
        return None


class _Font(_Base):
    def setBold(self, v): pass
    def setPixelSize(self, v): pass
    def setPointSize(self, v): pass


class _Metriche(_Base):
    def horizontalAdvance(self, testo):
        return len(testo) * 8


class _Segnale:
    def __init__(self, *args, **kwargs):
        self._destinatari = []

    def connect(self, funzione):
        self._destinatari.append(funzione)

    def emit(self, *args, **kwargs):
        for f in list(self._destinatari):
            f(*args, **kwargs)


def pyqtSignal(*args, **kwargs):
    return _Segnale()


class _MessageBox(_Base):
    """Finta finestra di dialogo: registra cosa e' stato chiesto e risponde
    da sola."""
    Yes, No, Cancel, Ok = 16384, 65536, 4194304, 1024
    Question = Warning = Critical = Information = 0
    AcceptRole = RejectRole = DestructiveRole = ActionRole = 0

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._pulsanti = []
        self._testo = ""
        self._premuto = None

    def setText(self, testo):
        self._testo = testo

    def setWindowTitle(self, t): pass
    def setIcon(self, i): pass
    def setDefaultButton(self, b): pass

    def addButton(self, etichetta, ruolo=0):
        pulsante = _Base()
        pulsante.etichetta = etichetta
        self._pulsanti.append(pulsante)
        return pulsante

    def exec_(self):
        RispostaAutomatica.dialoghi_mostrati.append(self._testo)
        if self._pulsanti:
            indice = min(RispostaAutomatica.scelta_pulsante, len(self._pulsanti) - 1)
            self._premuto = self._pulsanti[indice]
        return 0

    def clickedButton(self):
        return self._premuto

    @staticmethod
    def _statico(*args, **kwargs):
        if len(args) > 2 and isinstance(args[2], str):
            RispostaAutomatica.dialoghi_mostrati.append(args[2])
        return RispostaAutomatica.risposta_standard


_MessageBox.question = staticmethod(_MessageBox._statico)
_MessageBox.warning = staticmethod(_MessageBox._statico)
_MessageBox.critical = staticmethod(_MessageBox._statico)
_MessageBox.information = staticmethod(_MessageBox._statico)


class _Application(_Base):
    _istanza = None

    def __init__(self, *args, **kwargs):
        super().__init__()
        _Application._istanza = self

    @classmethod
    def instance(cls):
        return cls._istanza

    # Ingrandimento di Windows (125%, 150%...) che il finto schermo riferisce.
    # I test lo cambiano per provare i computer con lo schermo ingrandito.
    ingrandimento = 1.0

    @staticmethod
    def primaryScreen():
        schermo = _Base()
        schermo.availableGeometry = lambda: _Geometria()
        schermo.geometry = lambda: _Geometria()
        schermo.devicePixelRatio = lambda: _Application.ingrandimento
        return schermo

    @staticmethod
    def alert(widget, msec=0): pass

    @staticmethod
    def processEvents(): pass


class _Geometria(_Base):
    def width(self): return 1920
    def height(self): return 1080


class _Timer(_Base):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.timeout = _Segnale()

    def start(self, ms=0): pass
    def stop(self): pass

    @staticmethod
    def singleShot(ms, funzione):
        pass


class _Size(_Base):
    def __init__(self, larghezza=0, altezza=0):
        super().__init__()
        self._l, self._a = larghezza, altezza

    def width(self): return self._l
    def height(self): return self._a


class _Rettangolo(_Base):
    def __init__(self, larghezza=0, altezza=0):
        super().__init__()
        self._l, self._a = larghezza, altezza

    def width(self): return self._l
    def height(self): return self._a


class _TabWidget(_Base):
    """Contenitore a schede: tiene davvero la sua barra, così le prove possono
    misurarne le linguette come farebbe Qt vero."""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._barra = _TabBar()

    def setTabBar(self, barra):
        self._barra = barra

    def tabBar(self):
        return self._barra

    def addTab(self, contenuto, testo=""):
        return self._barra.addTab(testo)

    def count(self):
        return self._barra.count()

    def tabText(self, indice):
        return self._barra.tabText(indice)


class _TabBar(_Base):
    """Barra delle linguette. Tiene i testi aggiunti e sa dire quanto spazio
    occuperebbero, così si può provare il controllo del testo tagliato."""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._testi = []
        # Come in Qt: la barra disegna la propria "base" (la riga sotto le
        # linguette, che prosegue per tutta la larghezza) se non le si dice
        # di smettere.
        self._base = True

    def setDrawBase(self, disegna):
        self._base = bool(disegna)

    def drawBase(self):
        return self._base

    def addTab(self, testo):
        self._testi.append(testo)
        return len(self._testi) - 1

    def count(self):
        return len(self._testi)

    def tabText(self, indice):
        try:
            return self._testi[indice]
        except IndexError:
            return ""

    def tabRect(self, indice):
        """Larghezza effettiva della linguetta: si usa la stessa regola del
        programma, così se un giorno cambiasse, la prova la seguirebbe."""
        return _Rettangolo(self.tabSizeHint(indice).width(), 30)

    def tabSizeHint(self, indice):
        return _Size(50, 30)

    def setFont(self, f): pass
    def setElideMode(self, m): pass
    def setUsesScrollButtons(self, b): pass



class _ComboBox(_Base):
    """Una tendina che tiene davvero le voci e la scelta.

    Serve per provare i filtri: con una tendina finta che risponde sempre
    "nessuna scelta" si proverebbe solo il caso "nessun filtro", cioe' proprio
    quello in cui il filtro non fa niente."""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._voci = []          # (testo, dato)
        self._indice = 0
        self._muto = False
        self.currentIndexChanged = _Segnale()

    def addItem(self, testo, dato=None):
        self._voci.append((testo, dato))

    def clear(self):
        self._voci = []
        self._indice = 0

    def count(self):
        return len(self._voci)

    def currentIndex(self):
        return self._indice

    def setCurrentIndex(self, indice):
        if 0 <= indice < len(self._voci):
            self._indice = indice
            if not self._muto:
                self.currentIndexChanged.emit()

    def currentText(self):
        return self._voci[self._indice][0] if self._voci else ""

    def currentData(self):
        return self._voci[self._indice][1] if self._voci else None

    def itemText(self, indice):
        return self._voci[indice][0] if 0 <= indice < len(self._voci) else ""

    def itemData(self, indice):
        return self._voci[indice][1] if 0 <= indice < len(self._voci) else None

    def findData(self, dato):
        for i, (_t, d) in enumerate(self._voci):
            if d == dato:
                return i
        return -1

    def findText(self, testo, *modalita):
        # Qt accetta anche un secondo argomento (Qt.MatchFixedString e simili):
        # qui il confronto e' sempre esatto, ma l'argomento va accettato.
        for i, (t, _d) in enumerate(self._voci):
            if t == testo:
                return i
        return -1

    def addItems(self, elenco):
        for voce in elenco:
            self.addItem(voce)

    def setCurrentText(self, testo):
        indice = self.findText(testo)
        if indice >= 0:
            self.setCurrentIndex(indice)
        else:
            self._voci.append((testo, None))
            self.setCurrentIndex(len(self._voci) - 1)

    def blockSignals(self, muto):
        self._muto = bool(muto)

    def scegli(self, dato):
        """Comodita' per i test: sceglie la voce con quel dato."""
        indice = self.findData(dato)
        if indice < 0:
            raise AssertionError("voce non presente nella tendina: %r" % (dato,))
        self.setCurrentIndex(indice)



class _TableWidget(_Base):
    """Tabella che tiene conto di quante righe le vengono messe.

    Senza, rowCount() risponde sempre 0 e un test che conta le righe mostrate
    misura una costante: passerebbe qualunque cosa faccia il programma.
    E' successo scrivendo i test dei filtri di magazzino."""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._righe = 0
        self._colonne = 0
        self._celle = {}

    def setRowCount(self, n):
        self._righe = int(n)

    def rowCount(self):
        return self._righe

    def setColumnCount(self, n):
        self._colonne = int(n)

    def columnCount(self):
        return self._colonne

    def setItem(self, riga, colonna, elemento):
        self._celle[(riga, colonna)] = elemento

    def item(self, riga, colonna):
        return self._celle.get((riga, colonna))

    def setCellWidget(self, riga, colonna, widget):
        self._celle[(riga, colonna, "w")] = widget

    def cellWidget(self, riga, colonna):
        return self._celle.get((riga, colonna, "w"))

    def testo_cella(self, riga, colonna):
        """Comodita' per i test: il testo mostrato in quella cella."""
        elemento = self.item(riga, colonna)
        return elemento.text() if elemento is not None else ""


def _crea_modulo(nome, simboli):
    modulo = types.ModuleType(nome)
    for simbolo, valore in simboli.items():
        setattr(modulo, simbolo, valore)
    return modulo


def installa():
    """Mette il finto PyQt5 al posto di quello vero (che qui non c'e')."""
    if "PyQt5" in sys.modules and getattr(sys.modules["PyQt5"], "_finto", False):
        return

    widgets = {n: type(n, (_Base,), {}) for n in [
        "QAbstractItemView", "QAbstractScrollArea", "QButtonGroup", "QCheckBox",
        "QComboBox", "QDesktopWidget", "QDialog", "QDialogButtonBox",
        "QDoubleSpinBox", "QFileDialog", "QFormLayout", "QFrame",
        "QGraphicsDropShadowEffect", "QGridLayout", "QGroupBox", "QHBoxLayout",
        "QHeaderView", "QLabel", "QLineEdit", "QListWidget", "QListWidgetItem",
        "QMainWindow", "QPushButton", "QRadioButton", "QScrollArea",
        "QSizePolicy", "QSpinBox", "QSplitter", "QStackedWidget", "QTabWidget",
        "QTableWidget", "QTableWidgetItem", "QTextEdit", "QVBoxLayout", "QWidget",
    ]}
    widgets["QMessageBox"] = _MessageBox
    widgets["QApplication"] = _Application
    widgets["QTabBar"] = _TabBar
    widgets["QTabWidget"] = _TabWidget
    widgets["QComboBox"] = _ComboBox
    widgets["QTableWidget"] = _TableWidget

    core = {n: type(n, (_Base,), {}) for n in
            ["QDate", "QDir", "QPointF", "QRectF", "QSizeF", "QUrl"]}
    core["QSize"] = _Size
    core["QT_VERSION_STR"] = "5.15.0-finto"
    core["QTimer"] = _Timer
    core["pyqtSignal"] = pyqtSignal
    # Qt eredita da _Base per avere anche lui le costanti "qualunque"
    # (Qt.MatchFixedString, Qt.ElideNone, Qt.UserRole, ...): sono decine.
    core["Qt"] = type("Qt", (_Base,), {n: i for i, n in enumerate([
        "UserRole", "ElideNone", "AlignLeft", "AlignCenter", "AlignRight",
        "WindowMaximized", "Horizontal", "Vertical", "NoPen",
        "WindowContextHelpButtonHint",
    ])})
    core["QUrl"].fromLocalFile = staticmethod(lambda p: p)

    gui = {n: type(n, (_Base,), {}) for n in
           ["QBrush", "QColor", "QDoubleValidator", "QLinearGradient",
            "QPainter", "QPen", "QPolygonF", "QTextDocument"]}
    gui["QFont"] = _Font
    gui["QDesktopServices"] = type("QDesktopServices", (), {
        "openUrl": staticmethod(lambda u: True)})

    stampa = {n: type(n, (_Base,), {}) for n in ["QPrintDialog", "QPrinter"]}

    pacchetto = types.ModuleType("PyQt5")
    pacchetto._finto = True
    pacchetto.__path__ = []
    sys.modules["PyQt5"] = pacchetto
    sys.modules["PyQt5.QtWidgets"] = _crea_modulo("PyQt5.QtWidgets", widgets)
    sys.modules["PyQt5.QtCore"] = _crea_modulo("PyQt5.QtCore", core)
    sys.modules["PyQt5.QtGui"] = _crea_modulo("PyQt5.QtGui", gui)
    sys.modules["PyQt5.QtPrintSupport"] = _crea_modulo("PyQt5.QtPrintSupport", stampa)
    return pacchetto
