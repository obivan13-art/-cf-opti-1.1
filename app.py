import math

class VagasiTerv:
    def __init__(self):
        # Alapanyagok definiálása
        self.anyagok = {
            "XPS": {
                "szelesseg": 600,   # mm
                "hossz": 1250,      # mm
                "forgathato": False
            },
            "Compacfoam": {
                "szelesseg": 600,   # mm
                "hossz": 2400,      # mm
                "forgathato": False
            }
        }
        self.vagas_veszteseg = 4    # mm
    
    def szamol_vagasi_tervet(self, anyag_nev, darab_szelesseg, darab_hossz, darab_darabszam):
        """
        Vágási terv számítása adott anyaghoz és darabhoz
        
        Args:
            anyag_nev: str - "XPS" vagy "Compacfoam"
            darab_szelesseg: int - darab szélessége mm-ben
            darab_hossz: int - darab hossza mm-ben
            darab_darabszam: int - hány darab kell
            
        Returns:
            dict: Vágási terv részletekkel
        """
        if anyag_nev not in self.anyagok:
            return {"hiba": f"Ismeretlen anyag: {anyag_nev}"}
        
        anyag = self.anyagok[anyag_nev]
        lap_szelesseg = anyag["szelesseg"]
        lap_hossz = anyag["hossz"]
        
        # Ellenőrizzük, hogy a darab elfér-e a lapban
        darab_sz = darab_szelesseg
        darab_h = darab_hossz
        
        # Ellenőrizzük, hogy elfér-e a szélességben
        if darab_sz > lap_szelesseg:
            return {
                "hiba": f"A {darab_sz} mm széles darab nem fér el a {lap_szelesseg} mm széles lapban!",
                "javaslat": "A darab szélessége kisebb kell legyen, mint a lap szélessége."
            }
        
        # Hány darab fér a szélességben (vágásveszteséggel)
        # Képlet: n × szélesség + (n-1) × vágásveszteség ≤ lap_szélesség
        max_db_szelessegben = 0
        for n in range(1, 100):
            szukseg_hely = n * darab_sz + (n - 1) * self.vagas_veszteseg
            if szukseg_hely <= lap_szelesseg:
                max_db_szelessegben = n
            else:
                break
        
        if max_db_szelessegben == 0:
            return {
                "hiba": f"A {darab_sz} mm széles darabból 1 db sem fér el a {lap_szelesseg} mm széles lapban (vágásveszteséggel)!",
                "javaslat": "Próbálj kisebb darabot választani."
            }
        
        # Hány darab fér a hosszban (vágásveszteséggel)
        max_db_hosszban = 0
        for n in range(1, 100):
            szukseg_hely = n * darab_h + (n - 1) * self.vagas_veszteseg
            if szukseg_hely <= lap_hossz:
                max_db_hosszban = n
            else:
                break
        
        # Ha nem fér a hosszban, akkor toldani kell
        if max_db_hosszban == 0:
            # Toldás szükséges
            toldas_igeny = True
            darabok_per_lap = max_db_szelessegben
            # Hány lap kell egy darabhoz
            lapok_per_darab = math.ceil(darab_h / lap_hossz)
            # Egy lapra hány darab fér (csak szélességben)
            db_lapra = max_db_szelessegben
            # Maradék hossz számítása
            maradek_hossz = lap_hossz - darab_h if darab_h < lap_hossz else 0
        else:
            toldas_igeny = False
            darabok_per_lap = max_db_szelessegben * max_db_hosszban
            db_lapra = darabok_per_lap
            maradek_hossz = lap_hossz - (max_db_hosszban * darab_h + (max_db_hosszban - 1) * self.vagas_veszteseg)
            lapok_per_darab = 1
        
        # Szükséges lapok száma
        szukseges_lapok = math.ceil(darab_darabszam / db_lapra)
        
        # Kihasználtság számítása
        hasznos_terulet = darab_darabszam * darab_sz * darab_h
        teljes_terulet = szukseges_lapok * lap_szelesseg * lap_hossz
        kihasznaltsag = (hasznos_terulet / teljes_terulet) * 100 if teljes_terulet > 0 else 0
        
        # Maradék szélesség számítása
        maradek_szelesseg = lap_szelesseg - (max_db_szelessegben * darab_sz + (max_db_szelessegben - 1) * self.vagas_veszteseg)
        
        # Megoldás összeállítása
        megoldas = {
            "darab_szelesseg": darab_sz,
            "darab_hossz": darab_h,
            "db_szelessegben": max_db_szelessegben,
            "db_hosszban": max_db_hosszban,
            "db_lapra": db_lapra,
            "toldas_szukseges": toldas_igeny,
            "lapok_per_darab": lapok_per_darab,
            "szukseges_lapok": szukseges_lapok,
            "kihasznaltsag": kihasznaltsag,
            "maradek_szelesseg": maradek_szelesseg,
            "maradek_hossz": maradek_hossz
        }
        
        # Részletes vágási terv generálása
        vagasi_terv = self.genaral_vagasi_tervet(
            anyag_nev, 
            darab_szelesseg, 
            darab_hossz, 
            darab_darabszam, 
            megoldas
        )
        
        return {
            "anyag": anyag_nev,
            "lap_meret": f"{lap_szelesseg}×{lap_hossz}",
            "darab_meret": f"{darab_szelesseg}×{darab_hossz}",
            "darab_darabszam": darab_darabszam,
            "szukseges_lapok": szukseges_lapok,
            "kihasznaltsag": round(kihasznaltsag, 1),
            "toldas_szukseges": toldas_igeny,
            "maradek_szelesseg": maradek_szelesseg,
            "maradek_hossz": maradek_hossz,
            "vagasi_terv": vagasi_terv
        }
    
    def genaral_vagasi_tervet(self, anyag_nev, darab_sz, darab_h, darab_darabszam, megoldas):
        """Részletes vágási terv generálása"""
        lapok = []
        db_lapra = megoldas["db_lapra"]
        db_szelessegben = megoldas["db_szelessegben"]
        darab_sz_irany = megoldas["darab_szelesseg"]
        darab_h_irany = megoldas["darab_hossz"]
        toldas = megoldas["toldas_szukseges"]
        
        maradek_darab = darab_darabszam
        lap_index = 1
        
        while maradek_darab > 0:
            # Hány darab megy erre a lapra
            db_ebben = min(db_lapra, maradek_darab)
            
            # Lap részletes vágási információi
            lap_info = {
                "lap_sorszam": lap_index,
                "darabok": [],
                "maradek_meret": ""
            }
            
            # Darabok elhelyezése a lapon
            for i in range(db_ebben):
                sor = i // db_szelessegben
                oszlop = i % db_szelessegben
                
                # Pozíció számítása vágásveszteséggel
                x = oszlop * (darab_sz_irany + self.vagas_veszteseg)
                y = sor * (darab_h_irany + self.vagas_veszteseg)
                
                lap_info["darabok"].append({
                    "sorszam": i + 1,
                    "meret": f"{darab_sz_irany}×{darab_h_irany}",
                    "pozicio": f"({x}, {y})",
                    "toldva": toldas
                })
            
            # Maradék méretek
            maradek_sz = megoldas["maradek_szelesseg"]
            maradek_h = megoldas["maradek_hossz"]
            lap_info["maradek_meret"] = f"{maradek_sz}×{maradek_h}" if maradek_sz > 0 and maradek_h > 0 else "Nincs"
            
            lapok.append(lap_info)
            lap_index += 1
            maradek_darab -= db_ebben
        
        return lapok

# ============ HASZNÁLATI PÉLDA ============

if __name__ == "__main__":
    vagas = VagasiTerv()
    
    # 1. Eredeti táblázatból a 10 db 200×2400 XPS
    print("=" * 60)
    print("XPS - 10 db 200×2400 mm")
    print("=" * 60)
    
    eredmeny = vagas.szamol_vagasi_tervet("XPS", 200, 2400, 10)
    
    if "hiba" in eredmeny:
        print(f"❌ Hiba: {eredmeny['hiba']}")
        if "javaslat" in eredmeny:
            print(f"💡 {eredmeny['javaslat']}")
    else:
        print(f"Anyag: {eredmeny['anyag']}")
        print(f"Lap méret: {eredmeny['lap_meret']}")
        print(f"Darab: {eredmeny['darab_meret']} × {eredmeny['darab_darabszam']} db")
        print(f"Szükséges lapok: {eredmeny['szukseges_lapok']} db")
        print(f"Kihasználtság: {eredmeny['kihasznaltsag']}%")
        print(f"Toldás szükséges: {'Igen' if eredmeny['toldas_szukseges'] else 'Nem'}")
        print(f"Maradék laponként: {eredmeny['maradek_szelesseg']}×{eredmeny['maradek_hossz']} mm")
        print("\n📐 Részletes vágási terv:")
        
        for lap in eredmeny["vagasi_terv"]:
            print(f"\n{lap['lap_sorszam']}. lap:")
            for darab in lap["darabok"]:
                toldas_str = " (toldva)" if darab["toldva"] else ""
                print(f"  - {darab['meret']} @ {darab['pozicio']}{toldas_str}")
            print(f"  Maradék: {lap['maradek_meret']}")
    
    print("\n" + "=" * 60)
    
    # 2. Teszt: 350×3000 XPS
    print("\nXPS - 1 db 350×3000 mm")
    print("=" * 60)
    
    eredmeny2 = vagas.szamol_vagasi_tervet("XPS", 350, 3000, 1)
    
    if "hiba" in eredmeny2:
        print(f"❌ Hiba: {eredmeny2['hiba']}")
    else:
        print(f"Anyag: {eredmeny2['anyag']}")
        print(f"Lap méret: {eredmeny2['lap_meret']}")
        print(f"Darab: {eredmeny2['darab_meret']} × {eredmeny2['darab_darabszam']} db")
        print(f"Szükséges lapok: {eredmeny2['szukseges_lapok']} db")
        print(f"Kihasználtság: {eredmeny2['kihasznaltsag']}%")
        print(f"Toldás szükséges: {'Igen' if eredmeny2['toldas_szukseges'] else 'Nem'}")
        print(f"Maradék laponként: {eredmeny2['maradek_szelesseg']}×{eredmeny2['maradek_hossz']} mm")
        print("\n📐 Részletes vágási terv:")
        
        for lap in eredmeny2["vagasi_terv"]:
            print(f"\n{lap['lap_sorszam']}. lap:")
            for darab in lap["darabok"]:
                toldas_str = " (toldva)" if darab["toldva"] else ""
                print(f"  - {darab['meret']} @ {darab['pozicio']}{toldas_str}")
            print(f"  Maradék: {lap['maradek_meret']}")
    
    print("\n" + "=" * 60)
    
    # 3. Teszt: Compacfoam - 10 db 40×200×2400 (az eredeti táblázatból)
    print("\nCompacfoam - 10 db 200×2400 mm")
    print("=" * 60)
    
    eredmeny3 = vagas.szamol_vagasi_tervet("Compacfoam", 200, 2400, 10)
    
    if "hiba" in eredmeny3:
        print(f"❌ Hiba: {eredmeny3['hiba']}")
    else:
        print(f"Anyag: {eredmeny3['anyag']}")
        print(f"Lap méret: {eredmeny3['lap_meret']}")
        print(f"Darab: {eredmeny3['darab_meret']} × {eredmeny3['darab_darabszam']} db")
        print(f"Szükséges lapok: {eredmeny3['szukseges_lapok']} db")
        print(f"Kihasználtság: {eredmeny3['kihasznaltsag']}%")
        print(f"Toldás szükséges: {'Igen' if eredmeny3['toldas_szukseges'] else 'Nem'}")
        print(f"Maradék laponként: {eredmeny3['maradek_szelesseg']}×{eredmeny3['maradek_hossz']} mm")
        print("\n📐 Részletes vágási terv:")
        
        for lap in eredmeny3["vagasi_terv"]:
            print(f"\n{lap['lap_sorszam']}. lap:")
            for darab in lap["darabok"]:
                toldas_str = " (toldva)" if darab["toldva"] else ""
                print(f"  - {darab['meret']} @ {darab['pozicio']}{toldas_str}")
            print(f"  Maradék: {lap['maradek_meret']}")
