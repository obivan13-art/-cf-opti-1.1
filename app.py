import streamlit as st
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
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
    szelesseg: int
    hossz: int
    x: int
    y: int
    darabszam: int

@dataclass
class VagasiTerv:
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
    
    compacfoam_meretek = [
        (40, 1200, 2400), (50, 1200, 2400), (60, 1200, 2400),
        (70, 1200, 2400), (80, 1200, 2400),
    ]
    
    for vastag, szel, hossz in compacfoam_meretek:
        tablak.append(Tabla("Compacfoam", vastag, szel, hossz))
    
    xps_meretek = [
        (20, 600, 1250), (30, 600, 1250), (40, 600, 1250),
        (50, 600, 1250), (60, 600, 1250), (80, 600, 1250),
    ]
    
    for vastag, szel, hossz in xps_meretek:
        tablak.append(Tabla("XPS", vastag, szel, hossz))
    
    return tablak

# ==================== TÁBLA KIVÁLASZTÁS ====================

def tabla_kivalasztasa(anyag: str, vastagsag: int, osszes_tabla: List[Tabla]) -> Optional[Tabla]:
    elerheto = [t for t in osszes_tabla if t.anyag == anyag and t.vastagsag == vastagsag]
    if not elerheto:
        return None
    return max(elerheto, key=lambda t: t.szelesseg * t.hossz)

# ==================== HELYES TOLDÁS KEZELÉS ====================

def toldashoz_szukseges_tablak_szama(darab_hossz: int, tabla_hossz: int, vagasveszteseg: int) -> int:
    """
    Kiszámolja, hogy hány tábla kell a darab hosszának eléréséhez.
    Ez a HELYES toldás logika!
    
    Példa: 2400 mm-es darab, 1250 mm-es tábla → 2 tábla kell
    """
    if darab_hossz <= tabla_hossz:
        return 1
    
    return math.ceil((darab_hossz + vagasveszteseg) / (tabla_hossz + vagasveszteseg))

# ==================== DARABOK SZÁMOLÁSA EGY TÁBLÁBÓL ====================

def darabok_szama_egy_tablabol(
    tabla: Tabla,
    darab_szelesseg: int,
    darab_hossz: int,
    vagasveszteseg: int
) -> int:
    """
    Kiszámolja, hogy egy táblából hány darab vágható ki.
    FIGYELEM: Ha toldás kell, akkor a darabok száma csökken!
    """
    if darab_szelesseg > tabla.szelesseg:
        return 0
    
    # Hány darab fér a szélességben
    db_szelesseg = (tabla.szelesseg + vagasveszteseg) // (darab_szelesseg + vagasveszteseg)
    if db_szelesseg == 0:
        return 0
    
    # Hány darab fér a hosszban (toldás nélkül)
    if darab_hossz > tabla.hossz:
        # Ha toldás kell, akkor egy táblából CSAK 1 darab fér hosszban!
        db_hossz = 1
    else:
        db_hossz = (tabla.hossz + vagasveszteseg) // (darab_hossz + vagasveszteseg)
        if db_hossz == 0:
            return 0
    
    return db_szelesseg * db_hossz

# ==================== DARABOK KIHELYEZÉSE ====================

def darabok_kihelyezese(
    tabla: Tabla,
    darabok: List[Tuple[int, int, int]],
    vagasveszteseg: int
) -> VagasiTerv:
    """
    Kihelyezi a darabokat a táblára.
    """
    poziciok = []
    akt_x = 0
    akt_y = 0
    max_y_this_row = 0
    felhasznalt_terulet = 0
    
    rendezett = sorted(darabok, key=lambda x: x[0], reverse=True)
    
    for szelesseg, hossz, darabszam in rendezett:
        if szelesseg > tabla.szelesseg:
            continue
        
        # Ha toldás kell, akkor a táblán csak a tábla hossza használható
        effektiv_hossz = hossz if hossz <= tabla.hossz else tabla.hossz
        
        for _ in range(darabszam):
            if akt_x + szelesseg > tabla.szelesseg:
                akt_x = 0
                akt_y += max_y_this_row + vagasveszteseg
                max_y_this_row = 0
            
            if akt_y + effektiv_hossz > tabla.hossz:
                continue
            
            poziciok.append(DarabPozicio(
                szelesseg=szelesseg,
                hossz=hossz,
                x=akt_x,
                y=akt_y,
                darabszam=1
            ))
            
            # Csak a táblán elfoglalt területet számoljuk!
            felhasznalt_terulet += szelesseg * effektiv_hossz
            akt_x += szelesseg + vagasveszteseg
            max_y_this_row = max(max_y_this_row, effektiv_hossz)
    
    teljes_terulet = tabla.szelesseg * tabla.hossz
    hulladek_terulet = teljes_terulet - felhasznalt_terulet
    kihasznaltsag = (felhasznalt_terulet / teljes_terulet) * 100 if teljes_terulet > 0 else 0
    hulladek_szazalek = max(0, 100 - kihasznaltsag)
    
    return VagasiTerv(
        tabla=tabla,
        darabok=poziciok,
        felhasznalt_terulet=felhasznalt_terulet,
        hulladek_terulet=max(0, hulladek_terulet),
        kihasznaltsag=max(0, kihasznaltsag),
        hulladek_szazalek=hulladek_szazalek
    )

# ==================== DARABOK KIOSZTÁSA ====================

def darabok_kiosztasa(
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
            legjobb_tabla, szelesseg, hossz, vagasveszteseg
        )
        
        if db_egy_tablabol == 0:
            st.warning(f"⚠️ {legjobb_tabla.anyag} {szelesseg}x{hossz} nem fér a táblára!")
            continue
        
        szukseges_tabla_db = math.ceil(darabszam / db_egy_tablabol)
        
        maradek = darabszam
        for _ in range(szukseges_tabla_db):
            akt_db = min(maradek, db_egy_tablabol)
            maradek -= akt_db
            
            terv = darabok_kihelyezese(
                legjobb_tabla, [(szelesseg, hossz, akt_db)], vagasveszteseg
            )
            tablak.append(terv)
            ossz_felhasznalt += terv.felhasznalt_terulet
            ossz_terulet += tabla_terulet
    
    return tablak, ossz_felhasznalt, ossz_terulet

# ==================== FŐ SZÁMÍTÁS ====================

def anyagszukseglet_szamitas(darabok: List[KeszDarab], vagasveszteseg: int) -> Dict[str, Dict[int, SzuksegletEredmeny]]:
    csoportok = defaultdict(lambda: defaultdict(list))
    for d in darabok:
        if d.szelesseg <= 0 or d.hossz <= 0 or d.darabszam <= 0:
            st.warning(f"⚠️ Hibás adat: {d}")
            continue
        csoportok[d.anyag][d.vastagsag].append(d)
    
    osszes_tabla = tablak_eloallitasa()
    eredmenyek = defaultdict(dict)
    
    for anyag, vastag_csoport in csoportok.items():
        for vastagsag, darab_lista in vastag_csoport.items():
            legjobb_tabla = tabla_kivalasztasa(anyag, vastagsag, osszes_tabla)
            if legjobb_tabla is None:
                st.warning(f"⚠️ Nincs {anyag} {vastagsag}mm-es tábla!")
                continue
            
            meret_csoportok = defaultdict(int)
            for d in darab_lista:
                meret_csoportok[(d.szelesseg, d.hossz)] += d.darabszam
            
            tablak, ossz_felhasznalt, ossz_terulet = darabok_kiosztasa(
                meret_csoportok, legjobb_tabla, vagasveszteseg
            )
            
            if ossz_terulet > 0:
                kihasznaltsag = (ossz_felhasznalt / ossz_terulet) * 100
                hulladek_szazalek = max(0, 100 - kihasznaltsag)
            else:
                kihasznaltsag = 0
                hulladek_szazalek = 0
            
            eredmenyek[anyag][vastagsag] = SzuksegletEredmeny(
                anyag=anyag,
                vastagsag=vastagsag,
                ossz_tabla_db=len(tablak),
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

with st.sidebar:
    st.header("⚙️ Beallitasok")
    vagasveszteseg = st.slider("🔪 Vagasveszteseg (mm)", 1, 10, 4)
    st.markdown("---")
    st.header("📦 Elerheto tablak")
    st.markdown("**Compacfoam:**")
    st.code("40x1200x2400\n50x1200x2400\n60x1200x2400\n70x1200x2400\n80x1200x2400")
    st.markdown("**XPS:**")
    st.code("20x600x1250\n30x600x1250\n40x600x1250\n50x600x1250\n60x600x1250\n80x600x1250")

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
                "ID": i, "Anyag": d["anyag"], "Vastagsag": d["vastagsag"],
                "Szelesseg": d["szelesseg"], "Hossz": d["hossz"], "Darabszam": d["darabszam"]
            })
        st.dataframe(data, use_container_width=True)
    else:
        st.info("Nincs egyetlen darab sem!")

with col2:
    st.subheader("➕ Uj darab")
    with st.form("add_piece"):
        anyag = st.selectbox("Anyag", ["Compacfoam", "XPS"])
        vastagsag = st.number_input("Vastagsag (mm)", 10, 100, 40)
        szelesseg = st.number_input("Szelesseg (mm)", 10, 1000, 200)
        hossz = st.number_input("Hossz (mm)", 10, 3000, 2400)
        darabszam = st.number_input("Darabszam", 1, 1000, 2)
        if st.form_submit_button("➕ Hozzaad"):
            st.session_state.darabok.append({
                "anyag": anyag, "vastagsag": vastagsag,
                "szelesseg": szelesseg, "hossz": hossz, "darabszam": darabszam
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

st.markdown("---")
if st.button("🧮 SZAMITAS", type="primary", use_container_width=True):
    st.session_state.szamitva = True

if st.session_state.get("szamitva", False):
    st.markdown("---")
    st.header("📊 EREDMENYEK")
    
    darabok_lista = [
        KeszDarab(**d) for d in st.session_state.darabok
    ]
    
    try:
        eredmenyek = anyagszukseglet_szamitas(darabok_lista, vagasveszteseg)
        
        for anyag, vastag_eredmenyek in eredmenyek.items():
            st.subheader(f"📦 {anyag.upper()}")
            for vastagsag, eredmeny in sorted(vastag_eredmenyek.items()):
                c1, c2 = st.columns([1, 1])
                c1.metric(f"{vastagsag} mm", f"{eredmeny.ossz_tabla_db} db tabla",
                         f"Kihasznaltsag: {eredmeny.kihasznaltsag:.1f}%")
                if eredmeny.tablak:
                    with c2.expander("📋 Reszletes vagasi terv"):
                        for i, terv in enumerate(eredmeny.tablak, 1):
                            st.write(f"**{i}. tabla:** {terv.tabla.szelesseg}x{terv.tabla.hossz}")
                            for p in terv.darabok:
                                st.write(f"   - {p.darabszam} db {p.szelesseg}x{p.hossz} @ ({p.x}, {p.y})")
                            st.write(f"   Kihasznaltsag: {terv.kihasznaltsag:.1f}%")
        
        st.markdown("---")
        st.subheader("📊 TELJES OSSZESITES")
        ossz = 0
        for anyag, vastag_eredmenyek in eredmenyek.items():
            db = sum(e.ossz_tabla_db for e in vastag_eredmenyek.values())
            ossz += db
            st.metric(f"{anyag.upper()}", f"{db} db")
        st.metric("🏗️ MINDOSSZESEN", f"{ossz} db")
    except Exception as e:
        st.error(f"❌ Hiba: {e}")

st.markdown("---")
st.caption("🏗️ Szabasz Kalkulator")
