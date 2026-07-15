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
class VagasiEredmeny:
    tabla: Tabla
    darabok: List[Tuple[int, int, int]]
    felhasznalt_hossz: int
    hulladek_hossz: int
    hulladek_szazalek: float
    darabok_szama: int
    vagasok_szama: int

@dataclass
class SzuksegletEredmeny:
    anyag: str
    vastagsag: int
    szukseges_tablak: List[Tabla]
    darabok: List[KeszDarab]
    ossz_tabla_db: int
    ossz_felhasznalt: int
    ossz_hossz: int
    hulladek_szazalek: float
    vagasi_terv: List[VagasiEredmeny]

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

# ==================== VÁGÁSI ALGORITMUS ====================

def optimalizalt_vagas(tabla: Tabla, darab_hossz: int, darab_szelesseg: int, vagasveszteseg: int) -> VagasiEredmeny:
    if darab_szelesseg > tabla.szelesseg:
        return VagasiEredmeny(tabla, [], 0, tabla.hossz, 100.0, 0, 0)
    
    if darab_hossz + vagasveszteseg <= 0:
        return VagasiEredmeny(tabla, [], 0, tabla.hossz, 100.0, 0, 0)
    
    max_darab = (tabla.hossz + vagasveszteseg) // (darab_hossz + vagasveszteseg)
    
    if max_darab == 0:
        return VagasiEredmeny(tabla, [], 0, tabla.hossz, 100.0, 0, 0)
    
    felhasznalt = max_darab * darab_hossz + (max_darab - 1) * vagasveszteseg
    hulladek = tabla.hossz - felhasznalt
    hulladek_szazalek = (hulladek / tabla.hossz) * 100.0
    
    return VagasiEredmeny(
        tabla=tabla,
        darabok=[(darab_hossz, darab_szelesseg, max_darab)],
        felhasznalt_hossz=felhasznalt,
        hulladek_hossz=hulladek,
        hulladek_szazalek=hulladek_szazalek,
        darabok_szama=max_darab,
        vagasok_szama=max_darab - 1 if max_darab > 0 else 0
    )

def anyagszukseglet_szamitas(darabok: List[KeszDarab], vagasveszteseg: int) -> Dict[str, Dict[int, SzuksegletEredmeny]]:
    """Kiszamolja a szukseges tablakat anyagonkent es vastagsagonkent."""
    
    # Csoportositas anyag es vastagsag szerint
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
            
            # *** ITT A JAVÍTÁS - ÖSSZEVONJUK A DARABOKAT ***
            # Egyesítjük az azonos méretű darabokat
            meret_csoportok = defaultdict(int)
            for d in darab_lista:
                meret_csoportok[(d.szelesseg, d.hossz)] += d.darabszam
            
            szukseges_tablak = []
            ossz_tabla_db = 0
            ossz_felhasznalt = 0
            ossz_hossz = 0
            ossz_hulladek = 0
            vagasi_terv = []
            
            # Minden méretcsoportra külön számolunk
            for (szelesseg, hossz), darabszam in meret_csoportok.items():
                # Kiszámoljuk, hány darab fér egy táblára
                eredmeny = optimalizalt_vagas(
                    legjobb_tabla,
                    hossz,
                    szelesseg,
                    vagasveszteseg
                )
                
                if eredmeny.darabok_szama > 0:
                    # Hány tábla kell ehhez a mérethez
                    szukseges_tabla_db = math.ceil(darabszam / eredmeny.darabok_szama)
                    szukseges_tablak.extend([legjobb_tabla] * szukseges_tabla_db)
                    ossz_tabla_db += szukseges_tabla_db
                    ossz_felhasznalt += eredmeny.felhasznalt_hossz * szukseges_tabla_db
                    ossz_hossz += legjobb_tabla.hossz * szukseges_tabla_db
                    ossz_hulladek += eredmeny.hulladek_hossz * szukseges_tabla_db
                    vagasi_terv.append(eredmeny)
            
            if ossz_hossz > 0:
                hulladek_szazalek = (ossz_hulladek / ossz_hossz) * 100
            else:
                hulladek_szazalek = 0
            
            # Eredeti darabok listája (kiíráshoz)
            eredeti_darabok = []
            for d in darab_lista:
                eredeti_darabok.append(d)
            
            eredmenyek[anyag][vastagsag] = SzuksegletEredmeny(
                anyag=anyag,
                vastagsag=vastagsag,
                szukseges_tablak=szukseges_tablak,
                darabok=eredeti_darabok,
                ossz_tabla_db=ossz_tabla_db,
                ossz_felhasznalt=ossz_felhasznalt,
                ossz_hossz=ossz_hossz,
                hulladek_szazalek=hulladek_szazalek,
                vagasi_terv=vagasi_terv
            )
    
    return eredmenyek

# ==================== WEBES FELÜLET ====================

st.set_page_config(
    page_title="Szabasz Kalkulator",
    page_icon="🏗️",
    layout="wide"
)

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
        {"anyag": "Compacfoam", "vastagsag": 40, "szelesseg": 120, "hossz": 2400, "darabszam": 2},
        {"anyag": "XPS", "vastagsag": 20, "szelesseg": 120, "hossz": 2400, "darabszam": 1},
    ]

# Darabok listazasa
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
        hossz = st.number_input("Hossz (mm)", min_value=10, max_value=3000, value=2400)
        darabszam = st.number_input("Darabszam", min_value=1, max_value=1000, value=10)
        
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

# Darab torlese
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
            
            cols = st.columns(len(vastag_eredmenyek))
            for idx, (vastagsag, eredmeny) in enumerate(sorted(vastag_eredmenyek.items())):
                with cols[idx % len(cols)]:
                    st.metric(
                        label=f"{vastagsag} mm",
                        value=f"{eredmeny.ossz_tabla_db} db",
                        delta=f"Hulladek: {eredmeny.hulladek_szazalek:.1f}%"
                    )
                    
                    with st.expander("📋 Reszletek"):
                        st.write(f"**Felhasznalt hossz:** {eredmeny.ossz_felhasznalt} mm")
                        st.write(f"**Teljes tabla hossz:** {eredmeny.ossz_hossz} mm")
                        if eredmeny.darabok:
                            st.write("**Darabok:**")
                            for d in eredmeny.darabok:
                                st.write(f"- {d.darabszam} db {d.szelesseg}x{d.hossz} mm")
        
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
