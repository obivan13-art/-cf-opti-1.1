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

# ==================== VAGASI ALGORITMUS ====================

def optimalizalt_vagas(tabla: Tabla, darabok: List[Tuple[int, int, int]], vagasveszteseg: int) -> VagasiTerv:
    """Egy tablabol vagja ki a darabokat szelesseg es hossz alapjan."""
    
    felhasznalt_terulet = 0
    kivagott_darabok = []
    
    for szelesseg, hossz, darabszam in darabok:
        if szelesseg > tabla.szelesseg:
            continue
        
        # Hany darab fer egymas melle a szelessegben
        db_szelessegben = tabla.szelesseg // szelesseg
        
        # Hany darab fer a hosszban (vagasveszteseget figyelembe veve)
        db_hosszban = (tabla.hossz + vagasveszteseg) // (hossz + vagasveszteseg)
        
        # Osszes darab egy tablabol
        db_egy_tablabol = db_szelessegben * db_hosszban
        
        if db_egy_tablabol > 0 and darabszam > 0:
            tenyleges_db = min(db_egy_tablabol, darabszam)
            kivagott_darabok.append((szelesseg, hossz, tenyleges_db))
            felhasznalt_terulet += tenyleges_db * szelesseg * hossz
    
    teljes_terulet = tabla.szelesseg * tabla.hossz
    hulladek_terulet = teljes_terulet - felhasznalt_terulet
    hulladek_szazalek = (hulladek_terulet / teljes_terulet) * 100.0 if teljes_terulet > 0 else 100.0
    
    return VagasiTerv(
        tabla=tabla,
        darabok=kivagott_darabok,
        felhasznalt_terulet=felhasznalt_terulet,
        hulladek_terulet=hulladek_terulet,
        hulladek_szazalek=hulladek_szazalek
    )

def anyagszukseglet_szamitas(darabok: List[KeszDarab], vagasveszteseg: int) -> Dict[str, Dict[int, SzuksegletEredmeny]]:
    """Kiszamolja a szukseges tablakat anyagonkent es vastagsagonkent."""
    
    csoportok = defaultdict(lambda: defaultdict(list))
    for d in darabok:
        csoportok[d.anyag][d.vastagsag].append(d)
    
    osszes_tabla = tablak_eloallitasa()
    eredmenyek = defaultdict(dict)
    
    for anyag, vastag_csoport in csoportok.items():
        for vastagsag, darab_lista in vastag_csoport.items():
            elerheto_tablak = [
                t for t in osszes_tabla
                if t.anyag == anyag and t.vastagsag == vastagsag
            ]
            
            if not elerheto_tablak:
                continue
            
            legjobb_tabla = max(elerheto_tablak, key=lambda t: t.hossz)
            
            # Darabok osszegyujtese meretenkent
            meret_csoportok = defaultdict(int)
            for d in darab_lista:
                meret_csoportok[(d.szelesseg, d.hossz)] += d.darabszam
            
            ossz_tabla_db = 0
            ossz_felhasznalt = 0
            ossz_terulet = 0
            tablak = []
            
            for (szelesseg, hossz), darabszam in meret_csoportok.items():
                # Hany darab fer egy tablara
                db_szelessegben = legjobb_tabla.szelesseg // szelesseg
                db_hosszban = (legjobb_tabla.hossz + vagasveszteseg) // (hossz + vagasveszteseg)
                db_egy_tablabol = db_szelessegben * db_hosszban
                
                if db_egy_tablabol > 0:
                    szukseges_tabla_db = math.ceil(darabszam / db_egy_tablabol)
                    
                    maradek = darabszam
                    for _ in range(szukseges_tabla_db):
                        akt_db = min(maradek, db_egy_tablabol)
                        maradek -= akt_db
                        
                        terv = optimalizalt_vagas(
                            legjobb_tabla,
                            [(szelesseg, hossz, akt_db)],
                            vagasveszteseg
                        )
                        tablak.append(terv)
                        ossz_felhasznalt += terv.felhasznalt_terulet
                        ossz_terulet += legjobb_tabla.szelesseg * legjobb_tabla.hossz
                    
                    ossz_tabla_db += szukseges_tabla_db
            
            hulladek_szazalek = ((ossz_terulet - ossz_felhasznalt) / ossz_terulet * 100) if ossz_terulet > 0 else 0
            
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
        value=5,
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
        {"anyag": "Compacfoam", "vastagsag": 40, "szelesseg": 120, "hossz": 2350, "darabszam": 2},
        {"anyag": "XPS", "vastagsag": 20, "szelesseg": 120, "hossz": 2400, "darabszam": 1},
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
        st.info("Nincs egyetlen darab sem! Adj hozza az alabbi urlapon.")

with col2:
    st.subheader("➕ Uj darab hozzaadasa")
    
    with st.form("add_piece"):
        anyag = st.selectbox("Anyag", ["Compacfoam", "XPS"])
        vastagsag = st.number_input("Vastagsag (mm)", min_value=10, max_value=100, value=40)
        szelesseg = st.number_input("Szelesseg (mm)", min_value=10, max_value=1000, value=120)
        hossz = st.number_input("Hossz (mm)", min_value=10, max_value=3000, value=2350)
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
    st.subheader("🗑️ Darab torlese")
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

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
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
                                for szel, hossz, db in terv.darabok:
                                    st.write(f"   - {db} db {szel}x{hossz}")
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
st.caption("🏗️ Szabasz Kalkulator - Tobbfele tabla anyagszukseglet szamitasa")
