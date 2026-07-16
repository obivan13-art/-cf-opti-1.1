import streamlit as st
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

# ==================== ADATSTRUKTÚRÁK ====================

@dataclass
class Tabla:
    anyag: str
    vastagsag: int
    szelesseg: int
    hossz: int

@dataclass
class KeszDarab:
    anyag: str
    vastagsag: int
    szelesseg: int
    hossz: int
    darabszam: int

@dataclass
class DarabPozicio:
    """Egy darab pozíciója a táblán"""
    szelesseg: int
    hossz: int
    x: int
    y: int
    darabszam: int

@dataclass
class VagasiTerv:
    """Egy tábla vágási terve koordinátákkal"""
    tabla: Tabla
    darabok: List[DarabPozicio]
    felhasznalt_terulet: int
    hulladek_terulet: int
    kihasznaltsag: float
    hulladek_szazalek: float

@dataclass
class SzuksegletEredmeny:
    anyag: str
    vastagsag: int
    ossz_tabla_db: int
    tablak: List[VagasiTerv]
    darabok: List[KeszDarab]
    ossz_felhasznalt: int
    ossz_terulet: int
    kihasznaltsag: float
    hulladek_szazalek: float

# ==================== TÁBLA ADATBÁZIS ====================

def tablak_eloallitasa() -> List[Tabla]:
    tablak = []
    
    # COMPACFOAM - NINCS TOLDÁS!
    compacfoam_meretek = [
        (40, 1200, 2400), (50, 1200, 2400), (60, 1200, 2400),
        (70, 1200, 2400), (80, 1200, 2400),
    ]
    
    for vastag, szel, hossz in compacfoam_meretek:
        tablak.append(Tabla("Compacfoam", vastag, szel, hossz))
    
    # XPS - TOLDÁS LEHETSÉGES!
    xps_meretek = [
        (20, 600, 1250), (30, 600, 1250), (40, 600, 1250),
        (50, 600, 1250), (60, 600, 1250), (80, 600, 1250),
    ]
    
    for vastag, szel, hossz in xps_meretek:
        tablak.append(Tabla("XPS", vastag, szel, hossz))
    
    return tablak

# ==================== TÁBLA KIVÁLASZTÁS ====================

def tabla_kivalasztasa(anyag: str, vastagsag: int, osszes_tabla: List[Tabla]) -> Optional[Tabla]:
    """Kiválasztja a legnagyobb elérhető táblát."""
    elerheto = [t for t in osszes_tabla if t.anyag == anyag and t.vastagsag == vastagsag]
    if not elerheto:
        return None
    return max(elerheto, key=lambda t: t.szelesseg * t.hossz)

# ==================== TOLDÁS KEZELÉSE ====================

def toldas_kezelese(anyag: str, darab_hossz: int, tabla_hossz: int, vagasveszteseg: int) -> int:
    """
    Kiszámolja, hogy hány tábla kell a darab hosszának eléréséhez.
    COMPACFOAM: NINCS TOLDÁS (max 2400)
    XPS: TOLDÁS LEHETSÉGES (1250-nél hosszabb)
    """
    if anyag == "Compacfoam":
        # Compacfoam: nincs toldás, a darab max 2400
        return 1
    
    # XPS: toldás kezelése
    if darab_hossz <= tabla_hossz:
        return 1
    
    # Hány darab kell a hosszhoz (toldás)
    db = math.ceil((darab_hossz + vagasveszteseg) / (tabla_hossz + vagasveszteseg))
    return db

# ==================== DARABOK SZÁMOLÁSA EGY TÁBLÁBÓL ====================

def darabok_szama_egy_tablabol(
    anyag: str,
    tabla: Tabla,
    darab_szelesseg: int,
    darab_hossz: int,
    vagasveszteseg: int
) -> int:
    """
    Kiszámolja, hogy egy táblából hány darab vágható ki.
    COMPACFOAM: NINCS TOLDÁS
    XPS: TOLDÁS LEHETSÉGES
    """
    if darab_szelesseg > tabla.szelesseg:
        return 0
    
    # Hány darab fér a szélességben (vágásveszteséggel)
    db_szelesseg = (tabla.szelesseg + vagasveszteseg) // (darab_szelesseg + vagasveszteseg)
    if db_szelesseg == 0:
        db_szelesseg = 1
    
    # Hány darab fér a hosszban
    if anyag == "Compacfoam":
        # Compacfoam: nincs toldás, egy sorban max 1 darab hosszban
        db_hossz = 1
    else:
        # XPS: toldás kezelése
        db_hossz = toldas_kezelese(anyag, darab_hossz, tabla.hossz, vagasveszteseg)
    
    return db_szelesseg * db_hossz

# ==================== DARABOK KIHELYEZÉSE ====================

def darabok_kihelyezese(
    anyag: str,
    tabla: Tabla,
    darabok: List[Tuple[int, int, int]],
    vagasveszteseg: int
) -> VagasiTerv:
    """
    Kihelyezi a darabokat a táblára (forgatás nélkül).
    COMPACFOAM: NINCS TOLDÁS
    XPS: TOLDÁS LEHETSÉGES
    """
    poziciok = []
    akt_x = 0
    akt_y = 0
    max_y_this_row = 0
    felhasznalt_terulet = 0
    
    # Rendezés: csökkenő szélesség szerint
    rendezett = sorted(darabok, key=lambda x: x[0], reverse=True)
    
    for szelesseg, hossz, darabszam in rendezett:
        if szelesseg > tabla.szelesseg:
            continue
        
        # Toldás kezelése anyagfüggően
        db_toldas = toldas_kezelese(anyag, hossz, tabla.hossz, vagasveszteseg)
        
        for _ in range(darabszam):
            # Ellenőrizzük, hogy befér-e az aktuális sorba
            if akt_x + szelesseg > tabla.szelesseg:
                # Új sor
                akt_x = 0
                akt_y += max_y_this_row + vagasveszteseg
                max_y_this_row = 0
            
            # Ellenőrizzük, hogy befér-e a táblába
            if anyag == "Compacfoam":
                # Compacfoam: max 2400 a hossz, egy darab fér
                if akt_y + hossz > tabla.hossz:
                    continue
                darab_effektiv_hossz = hossz
            else:
                # XPS: toldás
                if akt_y + (hossz if hossz <= tabla.hossz else tabla.hossz) > tabla.hossz:
                    continue
                darab_effektiv_hossz = hossz if hossz <= tabla.hossz else tabla.hossz
            
            poziciok.append(DarabPozicio(
                szelesseg=szelesseg,
                hossz=hossz,
                x=akt_x,
                y=akt_y,
                darabszam=1
            ))
            
            felhasznalt_terulet += szelesseg * hossz
            akt_x += szelesseg + vagasveszteseg
            max_y_this_row = max(max_y_this_row, darab_effektiv_hossz)
    
    teljes_terulet = tabla.szelesseg * tabla.hossz
    hulladek_terulet = teljes_terulet - felhasznalt_terulet
    kihasznaltsag = (felhasznalt_terulet / teljes_terulet) * 100 if teljes_terulet > 0 else 0
    hulladek_szazalek = 100 - kihasznaltsag
    
    if kihasznaltsag < 0:
        kihasznaltsag = 0
    if hulladek_szazalek < 0:
        hulladek_szazalek = 0
    
    return VagasiTerv(
        tabla=tabla,
        darabok=poziciok,
        felhasznalt_terulet=felhasznalt_terulet,
        hulladek_terulet=hulladek_terulet if hulladek_terulet > 0 else 0,
        kihasznaltsag=kihasznaltsag,
        hulladek_szazalek=hulladek_szazalek
    )

# ==================== DARABOK KIOSZTÁSA ====================

def darabok_kiosztasa(
    anyag: str,
    meret_csoportok: Dict[Tuple[int, int], int],
    legjobb_tabla: Tabla,
    vagasveszteseg: int
) -> Tuple[List[VagasiTerv], int, int]:
    """
    Kiosztja a darabokat a táblákra.
    """
    tablak = []
    ossz_felhasznalt = 0
    ossz_terulet = 0
    tabla_terulet = legjobb_tabla.szelesseg * legjobb_tabla.hossz
    
    for (szelesseg, hossz), darabszam in meret_csoportok.items():
        # Hány darab fér egy táblára
        db_egy_tablabol = darabok_szama_egy_tablabol(
            anyag, legjobb_tabla, szelesseg, hossz, vagasveszteseg
        )
        
        if db_egy_tablabol > 0:
            # Hány tábla kell
            szukseges_tabla_db = math.ceil(darabszam / db_egy_tablabol)
            
            maradek = darabszam
            for _ in range(szukseges_tabla_db):
                akt_db = min(maradek, db_egy_tablabol)
                maradek -= akt_db
                
                darabok_lista = [(szelesseg, hossz, akt_db)]
                
                terv = darabok_kihelyezese(
                    anyag, legjobb_tabla, darabok_lista, vagasveszteseg
                )
                tablak.append(terv)
                ossz_felhasznalt += terv.felhasznalt_terulet
                ossz_terulet += tabla_terulet
    
    return tablak, ossz_felhasznalt, ossz_terulet

# ==================== FŐ SZÁMÍTÁS ====================

def anyagszukseglet_szamitas(darabok: List[KeszDarab], vagasveszteseg: int) -> Dict[str, Dict[int, SzuksegletEredmeny]]:
    """Kiszámolja a szükséges táblákat anyagonként és vastagságonként."""
    
    # 1. CSOPORTOSÍTÁS
    csoportok = defaultdict(lambda: defaultdict(list))
    for d in darabok:
        if d.szelesseg <= 0:
            st.warning(f"⚠️ Figyelem: {d.anyag} {d.vastagsag}mm - szélesség 0 vagy negatív!")
            continue
        if d.hossz <= 0:
            st.warning(f"⚠️ Figyelem: {d.anyag} {d.vastagsag}mm - hossz 0 vagy negatív!")
            continue
        if d.darabszam <= 0:
            st.warning(f"⚠️ Figyelem: {d.anyag} {d.vastagsag}mm - darabszám 0 vagy negatív!")
            continue
        csoportok[d.anyag][d.vastagsag].append(d)
    
    osszes_tabla = tablak_eloallitasa()
    eredmenyek = defaultdict(dict)
    
    for anyag, vastag_csoport in csoportok.items():
        for vastagsag, darab_lista in vastag_csoport.items():
            # 2. TÁBLA KIVÁLASZTÁS
            legjobb_tabla = tabla_kivalasztasa(anyag, vastagsag, osszes_tabla)
            if legjobb_tabla is None:
                st.warning(f"⚠️ Figyelem: Nincs {anyag} {vastagsag}mm-es tábla!")
                continue
            
            # 3. DARABOK ÖSSZEGYŰJTÉSE
            meret_csoportok = defaultdict(int)
            for d in darab_lista:
                meret_csoportok[(d.szelesseg, d.hossz)] += d.darabszam
            
            # 4. DARABOK KIOSZTÁSA
            tablak, ossz_felhasznalt, ossz_terulet = darabok_kiosztasa(
                anyag, meret_csoportok, legjobb_tabla, vagasveszteseg
            )
            
            # 5. HULLADÉK SZÁMÍTÁSA
            if ossz_terulet > 0:
                kihasznaltsag = (ossz_felhasznalt / ossz_terulet) * 100
                hulladek_szazalek = 100 - kihasznaltsag
                if kihasznaltsag < 0:
                    kihasznaltsag = 0
                if hulladek_szazalek < 0:
                    hulladek_szazalek = 0
            else:
                kihasznaltsag = 0
                hulladek_szazalek = 0
            
            # 6. EREDMÉNY ÖSSZEÁLLÍTÁSA
            ossz_tabla_db = len(tablak)
            
            for terv in tablak:
                if terv.felhasznalt_terulet > 0:
                    terv.kihasznaltsag = (terv.felhasznalt_terulet / (terv.tabla.szelesseg * terv.tabla.hossz)) * 100
                    if terv.kihasznaltsag < 0:
                        terv.kihasznaltsag = 0
                    terv.hulladek_szazalek = 100 - terv.kihasznaltsag
            
            eredmenyek[anyag][vastagsag] = SzuksegletEredmeny(
                anyag=anyag,
                vastagsag=vastagsag,
                ossz_tabla_db=ossz_tabla_db,
                tablak=tablak,
                darabok=darab_lista,
                ossz_felhasznalt=ossz_felhasznalt,
                ossz_terulet=ossz_terulet,
                kihasznaltsag=kihasznaltsag,
                hulladek_szazalek=hulladek_szazalek
            )
    
    return eredmenyek

# ==================== WEBES FELÜLET ====================

st.set_page_config(page_title="Szabasz Kalkulator", page_icon="🏗️", layout="wide")

st.title("🏗️ Szabasz Kalkulator")
st.markdown("### Tobbfele tabla anyagszukseglet szamitasa")

# ---------- BEÁLLÍTÁSOK ----------
with st.sidebar:
    st.header("⚙️ Beallitasok")
    
    vagasveszteseg = st.slider(
        "🔪 Vagasveszteseg (mm)",
        min_value=1,
        max_value=10,
        value=4,
        help="A fureszlap vastagsaga"
    )
    
    st.markdown("---")
    st.header("📦 Elerheto tablak")
    
    st.markdown("**Compacfoam:**")
    st.code("40x1200x2400\n50x1200x2400\n60x1200x2400\n70x1200x2400\n80x1200x2400")
    
    st.markdown("**XPS:**")
    st.code("20x600x1250\n30x600x1250\n40x600x1250\n50x600x1250\n60x600x1250\n80x600x1250")

# ---------- DARABOK KEZELÉSE ----------
st.header("📋 Darabok")

if "darabok" not in st.session_state:
    st.session_state.darabok = [
        {"anyag": "Compacfoam", "vastagsag": 40, "szelesseg": 120, "hossz": 2400, "darabszam": 10},
        {"anyag": "XPS", "vastagsag": 20, "szelesseg": 200, "hossz": 2400, "darabszam": 2},
        {"anyag": "XPS", "vastagsag": 20, "szelesseg": 200, "hossz": 2400, "darabszam": 10},
    ]

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📄 Jelenlegi darabok")
    
    if st.session_state.darabok:
        data = []
        for i, d in enumerate(st.session_state.darabok):
            data.append({
                "ID": i,
                "Anyag": d["anyag"],
                "Vastagsag": d["vastagsag"],
                "Szelesseg": d["szelesseg"],
                "Hossz": d["hossz"],
                "Darabszam": d["darabszam"]
            })
        st.dataframe(data, use_container_width=True)
    else:
        st.info("Nincs egyetlen darab sem!")

with col2:
    st.subheader("➕ Uj darab")
    
    with st.form("add_piece"):
        anyag = st.selectbox("Anyag", ["Compacfoam", "XPS"])
        vastagsag = st.number_input("Vastagsag (mm)", min_value=10, max_value=100, value=40)
        szelesseg = st.number_input("Szelesseg (mm)", min_value=10, max_value=1000, value=200)
        hossz = st.number_input("Hossz (mm)", min_value=10, max_value=3000, value=2400)
        darabszam = st.number_input("Darabszam", min_value=1, max_value=1000, value=2)
        
        submitted = st.form_submit_button("➕ Hozzaad")
        if submitted:
            st.session_state.darabok.append({
                "anyag": anyag,
                "vastagsag": vastagsag,
                "szelesseg": szelesseg,
                "hossz": hossz,
                "darabszam": darabszam
            })
            st.rerun()

if st.session_state.darabok:
    st.subheader("🗑️ Torles")
    torlendo = st.selectbox(
        "Valaszd ki a torlendo darabot",
        options=range(len(st.session_state.darabok)),
        format_func=lambda i: f"{st.session_state.darabok[i]['anyag']} {st.session_state.darabok[i]['vastagsag']}mm - {st.session_state.darabok[i]['darabszam']} db"
    )
    if st.button("🗑️ Torles"):
        del st.session_state.darabok[torlendo]
        st.rerun()

# ---------- SZÁMÍTÁS ----------
st.markdown("---")

if st.button("🧮 SZAMITAS", type="primary", use_container_width=True):
    st.session_state.szamitva = True

# ---------- EREDMÉNYEK ----------
if st.session_state.get("szamitva", False):
    st.markdown("---")
    st.header("📊 EREDMENYEK")
    
    darabok_lista = []
    for d in st.session_state.darabok:
        darabok_lista.append(KeszDarab(
            anyag=d["anyag"],
            vastagsag=d["vastagsag"],
            szelesseg=d["szelesseg"],
            hossz=d["hossz"],
            darabszam=d["darabszam"]
        ))
    
    try:
        eredmenyek = anyagszukseglet_szamitas(darabok_lista, vagasveszteseg)
        
        if not eredmenyek:
            st.warning("Nincs eredmeny! Ellenorizd a darabok adatait.")
        else:
            for anyag, vastag_eredmenyek in eredmenyek.items():
                st.subheader(f"📦 {anyag.upper()}")
                
                for vastagsag, eredmeny in sorted(vastag_eredmenyek.items()):
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.metric(
                            label=f"{vastagsag} mm",
                            value=f"{eredmeny.ossz_tabla_db} db tabla",
                            delta=f"Kihasznaltsag: {eredmeny.kihasznaltsag:.1f}%"
                        )
                    
                    with col2:
                        if eredmeny.tablak:
                            with st.expander("📋 Reszletes vagasi terv"):
                                for i, terv in enumerate(eredmeny.tablak, 1):
                                    st.write(f"**{i}. tabla:** {terv.tabla.szelesseg}x{terv.tabla.hossz}")
                                    if terv.darabok:
                                        for poz in terv.darabok:
                                            st.write(f"   - {poz.darabszam} db {poz.szelesseg}x{poz.hossz} @ ({poz.x}, {poz.y})")
                                    else:
                                        st.write("   - Nincs kivagott darab")
                                    st.write(f"   Kihasznaltsag: {terv.kihasznaltsag:.1f}%")
            
            st.markdown("---")
            st.subheader("📊 TELJES OSSZESITES")
            
            ossz_tabla = 0
            for anyag, vastag_eredmenyek in eredmenyek.items():
                anyag_db = sum(e.ossz_tabla_db for e in vastag_eredmenyek.values())
                ossz_tabla += anyag_db
                st.metric(f"{anyag.upper()}", f"{anyag_db} db")
            
            st.metric("🏗️ MINDOSSZESEN", f"{ossz_tabla} db", delta="Tablak szama")
        
    except Exception as e:
        st.error(f"❌ Hiba a szamitas soran: {e}")

st.markdown("---")
st.caption("🏗️ Szabasz Kalkulator")
