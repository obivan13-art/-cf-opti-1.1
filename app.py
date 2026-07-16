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
class VagasiTerv:
    tabla: Tabla
    darabok: List[Tuple[int, int, int]]
    felhasznalt_terulet: int
    hulladek_terulet: int
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
    hulladek_szazalek: float

# ==================== TABLA ADATBAZIS ====================

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

# ==================== VÁGÁSI SZÁMÍTÁS ====================

def darabok_szama_egy_tablabol(tabla: Tabla, darab_szelesseg: int, darab_hossz: int, vagasveszteseg: int) -> int:
    """
    Kiszámolja, hogy egy táblából hány darab vágható ki.
    """
    # Hány darab fér a szélességben (vágásveszteséggel)
    if darab_szelesseg > tabla.szelesseg:
        return 0
    
    # Szélességben: n * darab_szelesseg + (n-1) * vagasveszteseg <= tabla.szelesseg
    db_szelesseg = 0
    while True:
        if (db_szelesseg + 1) * darab_szelesseg + db_szelesseg * vagasveszteseg <= tabla.szelesseg:
            db_szelesseg += 1
        else:
            break
    
    # Hosszban: n * darab_hossz + (n-1) * vagasveszteseg <= tabla.hossz
    db_hossz = 0
    while True:
        if (db_hossz + 1) * darab_hossz + db_hossz * vagasveszteseg <= tabla.hossz:
            db_hossz += 1
        else:
            break
    
    return db_szelesseg * db_hossz

def anyagszukseglet_szamitas(darabok: List[KeszDarab], vagasveszteseg: int) -> Dict[str, Dict[int, SzuksegletEredmeny]]:
    """Kiszamolja a szukseges tablakat anyagonkent es vastagsagonkent."""
    
    # Csoportosítás anyag és vastagság szerint
    csoportok = defaultdict(lambda: defaultdict(list))
    for d in darabok:
        csoportok[d.anyag][d.vastagsag].append(d)
    
    osszes_tabla = tablak_eloallitasa()
    eredmenyek = defaultdict(dict)
    
    for anyag, vastag_csoport in csoportok.items():
        for vastagsag, darab_lista in vastag_csoport.items():
            # Kiválasztjuk a megfelelő táblát
            elerheto_tablak = [
                t for t in osszes_tabla
                if t.anyag == anyag and t.vastagsag == vastagsag
            ]
            
            if not elerheto_tablak:
                continue
            
            # A legnagyobb táblát választjuk
            legjobb_tabla = max(elerheto_tablak, key=lambda t: t.szelesseg * t.hossz)
            
            # Darabok összegyűjtése méretenként (ÖSSZEVONJUK AZ AZONOSAKAT!)
            meret_csoportok = defaultdict(int)
            for d in darab_lista:
                meret_csoportok[(d.szelesseg, d.hossz)] += d.darabszam
            
            ossz_tabla_db = 0
            ossz_felhasznalt = 0
            ossz_terulet = 0
            tablak = []
            
            for (szelesseg, hossz), darabszam in meret_csoportok.items():
                # Hány darab fér egy táblára
                db_egy_tablabol = darabok_szama_egy_tablabol(
                    legjobb_tabla, szelesseg, hossz, vagasveszteseg
                )
                
                if db_egy_tablabol > 0:
                    # Hány tábla kell
                    szukseges_tabla_db = math.ceil(darabszam / db_egy_tablabol)
                    
                    maradek = darabszam
                    for _ in range(szukseges_tabla_db):
                        akt_db = min(maradek, db_egy_tablabol)
                        maradek -= akt_db
                        
                        terv = VagasiTerv(
                            tabla=legjobb_tabla,
                            darabok=[(szelesseg, hossz, akt_db)],
                            felhasznalt_terulet=akt_db * szelesseg * hossz,
                            hulladek_terulet=legjobb_tabla.szelesseg * legjobb_tabla.hossz - akt_db * szelesseg * hossz,
                            hulladek_szazalek=0.0
                        )
                        tablak.append(terv)
                        ossz_felhasznalt += terv.felhasznalt_terulet
                        ossz_terulet += legjobb_tabla.szelesseg * legjobb_tabla.hossz
                    
                    ossz_tabla_db += szukseges_tabla_db
            
            if ossz_terulet > 0:
                hulladek_szazalek = ((ossz_terulet - ossz_felhasznalt) / ossz_terulet) * 100
                if hulladek_szazalek < 0:
                    hulladek_szazalek = 0
            else:
                hulladek_szazalek = 0
            
            # Frissítjük a hulladék százalékot a táblákban
            for terv in tablak:
                terv.hulladek_szazalek = (terv.hulladek_terulet / (terv.tabla.szelesseg * terv.tabla.hossz)) * 100
                if terv.hulladek_szazalek < 0:
                    terv.hulladek_szazalek = 0
            
            eredmenyek[anyag][vastagsag] = SzuksegletEredmeny(
                anyag=anyag,
                vastagsag=vastagsag,
                ossz_tabla_db=ossz_tabla_db,
                tablak=tablak,
                darabok=darab_lista,
                ossz_felhasznalt=ossz_felhasznalt,
                ossz_terulet=ossz_terulet,
                hulladek_szazalek=hulladek_szazalek
            )
    
    return eredmenyek

# ==================== WEBES FELULET ====================

st.set_page_config(page_title="Szabasz Kalkulator", page_icon="🏗️", layout="wide")

st.title("🏗️ Szabasz Kalkulator")
st.markdown("### Tobbfele tabla anyagszukseglet szamitasa")

# ---------- BEALLITASOK ----------
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

# ---------- DARABOK KEZELESE ----------
st.header("📋 Darabok")

if "darabok" not in st.session_state:
    st.session_state.darabok = [
        {"anyag": "Compacfoam", "vastagsag": 40, "szelesseg": 120, "hossz": 2400, "darabszam": 10},
        {"anyag": "XPS", "vastagsag": 20, "szelesseg": 200, "hossz": 2400, "darabszam": 2},
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

# ---------- SZAMITAS ----------
st.markdown("---")

if st.button("🧮 SZAMITAS", type="primary", use_container_width=True):
    st.session_state.szamitva = True

# ---------- EREDMENYEK ----------
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
                            delta=f"Hulladek: {eredmeny.hulladek_szazalek:.1f}%"
                        )
                    
                    with col2:
                        if eredmeny.tablak:
                            with st.expander("📋 Reszletes vagasi terv"):
                                for i, terv in enumerate(eredmeny.tablak, 1):
                                    st.write(f"**{i}. tabla:** {terv.tabla.szelesseg}x{terv.tabla.hossz}")
                                    if terv.darabok:
                                        for szel, hossz, db in terv.darabok:
                                            st.write(f"   - {db} db {szel}x{hossz}")
                                    else:
                                        st.write("   - Nincs kivagott darab")
                                    st.write(f"   Hulladek: {terv.hulladek_szazalek:.1f}%")
            
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
