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

def xps_toldas_optimalizalt(darab: KeszDarab, tabla: Tabla, vagasveszteseg: int) -> Tuple[int, int, List[VagasiEredmeny]]:
    szukseges_tabla_db = 0
    ossz_hulladek = 0
    vagasi_terv = []
    
    maradek_hossz = darab.hossz
    
    while maradek_hossz > 0:
        aktualis_hossz = min(maradek_hossz, tabla.hossz)
        
        eredmeny = optimalizalt_vagas(
            tabla,
            darab_hossz=aktualis_hossz,
            darab_szelesseg=darab.szelesseg,
            vagasveszteseg=vagasveszteseg
        )
        
        szukseges_tabla_db += 1
        
        if eredmeny.darabok_szama > 0:
            maradek_hossz -= eredmeny.felhasznalt_hossz
            ossz_hulladek += eredmeny.hulladek_hossz
            vagasi_terv.append(eredmeny)
        else:
            maradek_hossz -= aktualis_hossz
            ossz_hulladek += aktualis_hossz
        
        if 0 < maradek_hossz < 200:
            ossz_hulladek += maradek_hossz
            maradek_hossz = 0
    
    return szukseges_tabla_db, ossz_hulladek, vagasi_terv

def anyagszukseglet_szamitas(darabok: List[KeszDarab], vagasveszteseg: int) -> Dict[str, Dict[int, SzuksegletEredmeny]]:
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
            
            szukseges_tablak = []
            ossz_tabla_db = 0
            ossz_felhasznalt = 0
            ossz_hossz = 0
            ossz_hulladek = 0
            vagasi_terv = []
            
            for darab in darab_lista:
                if anyag == "XPS" and darab.hossz > legjobb_tabla.hossz:
                    for _ in range(darab.darabszam):
                        db, hulladek, terv = xps_toldas_optimalizalt(
                            darab, legjobb_tabla, vagasveszteseg
                        )
                        szukseges_tablak.extend([legjobb_tabla] * db)
                        ossz_tabla_db += db
                        ossz_felhasznalt += darab.hossz
                        ossz_hossz += db * legjobb_tabla.hossz
                        ossz_hulladek += hulladek
                        vagasi_terv.extend(terv)
                else:
                    eredmeny = optimalizalt_vagas(
                        legjobb_tabla,
                        darab.hossz,
                        darab.szelesseg,
                        vagasveszteseg
                    )
                    
                    if eredmeny.darabok_szama > 0:
                        szukseges_tabla_db = math.ceil(
                            darab.darabszam / eredmeny.darabok_szama
                        )
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
            
            eredmenyek[anyag][vastagsag] = SzuksegletEredmeny(
                anyag=anyag,
                vastagsag=vastagsag,
                szukseges_tablak=szukseges_tablak,
                darabok=darab_lista,
                ossz_tabla_db=ossz_tabla_db,
                ossz_felhasznalt=ossz_felhasznalt,
                ossz_hossz=ossz_hossz,
                hulladek_szazalek=hulladek_szazalek,
                vagasi_terv=vagasi_terv
            )
    
    return eredmenyek

# ==================== WEBES FELÜLET ====================

st.set_page_config(
    page_title="Szabász Kalkulátor",
    page_icon="???",
    layout="wide"
)

st.title("??? Szabász Kalkulátor")
st.markdown("### Többféle tábla anyagszükséglet számítása")

# ---------- BEÁLLÍTÁSOK ----------
with st.sidebar:
    st.header("?? Beállítások")
    
    vagasveszteseg = st.slider(
        "?? Vágásveszteség (mm)",
        min_value=1,
        max_value=10,
        value=5,
        help="A fűrészlap vastagsága"
    )
    
    st.markdown("---")
    st.header("?? Elérhető táblák")
    
    st.markdown("**Compacfoam:**")
    st.code("40x1200x2400\n50x1200x2400\n60x1200x2400\n70x1200x2400\n80x1200x2400")
    
    st.markdown("**XPS:**")
    st.code("20x600x1250\n30x600x1250\n40x600x1250\n50x600x1250\n60x600x1250\n80x600x1250")

# ---------- DARABOK KEZELÉSE ----------
st.header("?? Darabok")

# Munkamenetben tároljuk a darabokat
if "darabok" not in st.session_state:
    st.session_state.darabok = [
        {"anyag": "Compacfoam", "vastagsag": 40, "szelesseg": 100, "hossz": 2400, "darabszam": 5},
        {"anyag": "Compacfoam", "vastagsag": 40, "szelesseg": 200, "hossz": 1800, "darabszam": 3},
        {"anyag": "Compacfoam", "vastagsag": 50, "szelesseg": 150, "hossz": 2400, "darabszam": 8},
        {"anyag": "Compacfoam", "vastagsag": 60, "szelesseg": 120, "hossz": 1200, "darabszam": 10},
        {"anyag": "XPS", "vastagsag": 50, "szelesseg": 200, "hossz": 2400, "darabszam": 2},
        {"anyag": "XPS", "vastagsag": 50, "szelesseg": 600, "hossz": 1000, "darabszam": 12},
        {"anyag": "XPS", "vastagsag": 40, "szelesseg": 500, "hossz": 1250, "darabszam": 8},
        {"anyag": "XPS", "vastagsag": 30, "szelesseg": 400, "hossz": 800, "darabszam": 15},
    ]

# Darabok listázása
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("?? Jelenlegi darabok")
    
    if st.session_state.darabok:
        data = []
        for i, d in enumerate(st.session_state.darabok):
            data.append({
                "ID": i,
                "Anyag": d["anyag"],
                "Vastagság": d["vastagsag"],
                "Szélesség": d["szelesseg"],
                "Hossz": d["hossz"],
                "Darabszám": d["darabszam"]
            })
        st.dataframe(data, use_container_width=True)
    else:
        st.info("Nincs egyetlen darab sem! Adj hozzá az alábbi űrlapon.")

with col2:
    st.subheader("? Új darab hozzáadása")
    
    with st.form("add_piece"):
        anyag = st.selectbox("Anyag", ["Compacfoam", "XPS"])
        vastagsag = st.number_input("Vastagság (mm)", min_value=10, max_value=100, value=40)
        szelesseg = st.number_input("Szélesség (mm)", min_value=10, max_value=1000, value=120)
        hossz = st.number_input("Hossz (mm)", min_value=10, max_value=3000, value=2400)
        darabszam = st.number_input("Darabszám", min_value=1, max_value=1000, value=10)
        
        submitted = st.form_submit_button("? Hozzáad")
        if submitted:
            st.session_state.darabok.append({
                "anyag": anyag,
                "vastagsag": vastagsag,
                "szelesseg": szelesseg,
                "hossz": hossz,
                "darabszam": darabszam
            })
            st.rerun()

# Darab törlése
if st.session_state.darabok:
    st.subheader("??? Darab törlése")
    torlendo = st.selectbox(
        "Válaszd ki a törlendő darabot",
        options=range(len(st.session_state.darabok)),
        format_func=lambda i: f"{st.session_state.darabok[i]['anyag']} {st.session_state.darabok[i]['vastagsag']}mm - {st.session_state.darabok[i]['darabszam']} db"
    )
    if st.button("??? Törlés"):
        del st.session_state.darabok[torlendo]
        st.rerun()

# ---------- SZÁMÍTÁS ----------
st.markdown("---")

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("?? SZÁMÍTÁS", type="primary", use_container_width=True):
        st.session_state.szamitva = True

# ---------- EREDMÉNYEK ----------
if st.session_state.get("szamitva", False):
    st.markdown("---")
    st.header("?? EREDMÉNYEK")
    
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
            st.subheader(f"?? {anyag.upper()}")
            
            cols = st.columns(len(vastag_eredmenyek))
            for idx, (vastagsag, eredmeny) in enumerate(sorted(vastag_eredmenyek.items())):
                with cols[idx % len(cols)]:
                    st.metric(
                        label=f"{vastagsag} mm",
                        value=f"{eredmeny.ossz_tabla_db} db",
                        delta=f"Hulladék: {eredmeny.hulladek_szazalek:.1f}%"
                    )
                    
                    with st.expander("?? Részletek"):
                        st.write(f"**Felhasznált hossz:** {eredmeny.ossz_felhasznalt} mm")
                        st.write(f"**Teljes tábla hossz:** {eredmeny.ossz_hossz} mm")
                        if eredmeny.darabok:
                            st.write("**Darabok:**")
                            for d in eredmeny.darabok:
                                st.write(f"- {d.darabszam} db {d.szelesseg}x{d.hossz} mm")
        
        st.markdown("---")
        st.subheader("?? TELJES ÖSSZESÍTÉS")
        
        ossz_tabla = 0
        for anyag, vastag_eredmenyek in eredmenyek.items():
            anyag_db = sum(e.ossz_tabla_db for e in vastag_eredmenyek.values())
            ossz_tabla += anyag_db
            st.metric(f"{anyag.upper()}", f"{anyag_db} db")
        
        st.metric("??? MINDÖSSZESEN", f"{ossz_tabla} db", delta="Táblák száma")
        
    except Exception as e:
        st.error(f"? Hiba a számítás során: {e}")

st.markdown("---")
st.caption("??? Szabász Kalkulátor - Többféle tábla anyagszükséglet számítása")