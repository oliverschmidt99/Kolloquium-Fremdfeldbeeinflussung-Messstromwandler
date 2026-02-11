import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- KONFIGURATION ---
CSV_DATEI = "2026-02-11T11-12_export.csv"
SPALTEN_NAMEN = ["5% In", "20% In", "50% In", "80% In", "90% In", "100% In", "120% In"]

def lade_und_plotte_vergleich():
    print(f"Lade Datei: {CSV_DATEI} ...")

    # 1) Daten laden (deutsches Zahlenformat direkt beim Einlesen)
    try:
        df = pd.read_csv(CSV_DATEI, decimal=",", thousands=".")
    except Exception as e:
        print(f"KRITISCHER FEHLER beim Laden: {e}")
        return

    # Spaltennamen säubern
    df.columns = df.columns.str.strip()

    # Unnötige Index-Spalten entfernen
    df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")], errors="ignore")

    # Pflichtspalten prüfen
    required = {"nennstrom", "technologie", "geometrie"}
    missing = required - set(df.columns)
    if missing:
        print("Fehlende Pflichtspalten:", missing)
        return

    # Strings säubern
    for col in ["nennstrom", "technologie", "geometrie"]:
        df[col] = df[col].astype(str).str.strip()

    # final_legend erzeugen
    df["final_legend"] = df.apply(
        lambda r: f"{r['technologie']} {r['geometrie']} (In={r['nennstrom']}A)", axis=1
    )

    # --- DATENPRÜFUNG & KONVERTIERUNG ---
    cols_to_check = [c for c in SPALTEN_NAMEN if c in df.columns]
    if "Preis (€)" in df.columns:
        cols_to_check.append("Preis (€)")

    # Sicherstellen, dass alles Zahlen sind
    for col in cols_to_check:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fehlende Fehlerspalten mit NaN auffüllen
    for c in SPALTEN_NAMEN:
        if c not in df.columns:
            df[c] = np.nan

    # 2) Max Fehler pro Zeile berechnen (Worst Case)
    df["row_max_error"] = df[SPALTEN_NAMEN].abs().max(axis=1)

    # 3) Aggregation pro Gerät (Summe über Phasen L1+L2+L3)
    agg_dict = {"row_max_error": "sum"}
    if "Preis (€)" in df.columns:
        agg_dict["Preis (€)"] = "first" 

    device_stats = (
        df.groupby(["final_legend", "nennstrom", "technologie", "geometrie"])
        .agg(agg_dict)
        .reset_index()
    )

    if device_stats.empty:
        print("Keine Daten nach Aggregation vorhanden.")
        return

    # 4) Fehler pro Euro berechnen
    if "Preis (€)" in device_stats.columns:
        device_stats["error_per_euro"] = device_stats.apply(
            lambda r: r["row_max_error"] / r["Preis (€)"]
            if pd.notnull(r["Preis (€)"]) and r["Preis (€)"] > 0
            else np.nan,
            axis=1,
        )
    else:
        device_stats["error_per_euro"] = np.nan

    # 5) Zusammenfassung (Worst Case pro Bauart)
    summary = (
        device_stats.groupby(["nennstrom", "technologie", "geometrie"])
        .agg({"row_max_error": "max", "error_per_euro": "max"})
        .reset_index()
    )

    summary["label"] = summary["technologie"] + " " + summary["geometrie"]

    # --- FARBEN ---
    farben_map = {
        "Standard Parallel": "#d62728",     # Rot
        "Standard Dreieck": "#ff9896",      # Hellrot
        "Kompensiert Parallel": "#1f77b4",  # Blau
        "Kompensiert Dreieck": "#aec7e8",   # Hellblau
        "FFP Parallel": "#2ca02c",          # Grün
        "FFP Dreieck": "#98df8a",           # Hellgrün
    }

    def beschrifte_bars(ax, fmt="%.2f", rotation=90):
        for container in ax.containers:
            labels = []
            for v in container.datavalues:
                if pd.notnull(v) and v > 0:
                    labels.append(fmt % v)
                else:
                    labels.append("") 
            ax.bar_label(container, labels=labels, padding=3, rotation=rotation, fontsize=8)

    # --- PLOT FUNKTIONEN ---

    def erstelle_einzeldiagramme():
        # Pivotisieren
        pivot_abs = summary.pivot(index="nennstrom", columns="label", values="row_max_error")
        pivot_eur = summary.pivot(index="nennstrom", columns="label", values="error_per_euro")

        if pivot_abs.empty:
            print("Keine Daten für Diagramme vorhanden.")
            return

        # Sortieren
        cols = sorted(list(pivot_abs.columns))
        pivot_abs = pivot_abs.reindex(columns=cols)
        pivot_eur = pivot_eur.reindex(columns=cols)
        colors = [farben_map.get(c, "#333333") for c in cols]

        # 1) Absoluter Fehler
        plt.figure(figsize=(14, 8))
        ax1 = pivot_abs.plot(kind="bar", width=0.8, color=colors, edgecolor="black", linewidth=0.5, figsize=(14,8))
        plt.title("Vergleich Gesamtfehler (Summe L1+L2+L3)", fontsize=14)
        plt.ylabel("Gesamtfehler [Summe Absolutbeträge]", fontsize=12)
        plt.xlabel("Nennstrom [A]", fontsize=12)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.xticks(rotation=0)
        beschrifte_bars(ax1, fmt="%.2f", rotation=90)
        plt.legend(title="Konfiguration", bbox_to_anchor=(1.01, 1), loc="upper left")
        plt.tight_layout()
        plt.savefig("vergleich_fehler_absolut.png", dpi=300)
        print("Grafik gespeichert: vergleich_fehler_absolut.png")
        plt.close()

        # 2) Fehler pro Euro
        plt.figure(figsize=(14, 8))
        ax2 = pivot_eur.plot(kind="bar", width=0.8, color=colors, edgecolor="black", linewidth=0.5, figsize=(14,8))
        plt.title("Fehler auf Preis normiert (Gesamtfehler / Preis)", fontsize=14)
        plt.ylabel("Normierter Fehler [1/€]", fontsize=12)
        plt.xlabel("Nennstrom [A]", fontsize=12)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.xticks(rotation=0)
        beschrifte_bars(ax2, fmt="%.4f", rotation=90)
        plt.legend(title="Konfiguration", bbox_to_anchor=(1.01, 1), loc="upper left")
        plt.tight_layout()
        plt.savefig("vergleich_fehler_pro_euro.png", dpi=300)
        print("Grafik gespeichert: vergleich_fehler_pro_euro.png")
        plt.close()

        # 3) Effizienz (MIT FFP!)
        basis_label = "Standard Parallel"
        geo_label = "Standard Dreieck"
        tech_komp_label = "Kompensiert Parallel"
        tech_ffp_label = "FFP Parallel"  # <--- FFP hinzugefügt

        eff_rows = []
        # Wir nehmen "error_per_euro" als Maßstab (oder row_max_error, falls gewünscht)
        # Hier: error_per_euro (Effizienz pro Euro)
        col_metric = "error_per_euro"

        for nennstrom in pivot_abs.index:
            sub = summary[summary["nennstrom"] == nennstrom].set_index("label")
            
            def get_val(lbl):
                return sub.loc[lbl, col_metric] if lbl in sub.index else np.nan

            base = get_val(basis_label)
            geo_val = get_val(geo_label)
            komp_val = get_val(tech_komp_label)
            ffp_val = get_val(tech_ffp_label)

            # Faktor Berechnung: Basis / Neu 
            # (Wie viel mal BESSER ist die neue Variante im Vergleich zur Basis?)
            def calc_factor(ref, val):
                if pd.notnull(ref) and ref > 0 and pd.notnull(val) and val > 0:
                    return ref / val
                return np.nan

            eff_rows.append({
                "nennstrom": nennstrom,
                "Parallel (Basis)": 1.0 if pd.notnull(base) and base > 0 else np.nan,
                "Dreieck (Geometrie)": calc_factor(base, geo_val),
                "Kompensiert (Tech)": calc_factor(base, komp_val),
                "FFP (Tech)": calc_factor(base, ffp_val) # <--- FFP hinzugefügt
            })

        eff = pd.DataFrame(eff_rows).set_index("nennstrom")

        # Plot Effizienz
        plt.figure(figsize=(14, 8))
        # Farben für den Effizienz-Plot manuell setzen oder Standard lassen
        eff_colors = ['#d62728', '#ff9896', '#1f77b4', '#2ca02c'] # Rot, Hellrot, Blau, Grün
        
        ax3 = eff.plot(kind="bar", width=0.8, color=eff_colors, edgecolor="black", linewidth=0.5, figsize=(14,8))
        plt.title(f"Effizienz-Steigerung gegenüber '{basis_label}' (bezogen auf Fehler/€)", fontsize=14)
        plt.ylabel("Verbesserungsfaktor [x-fach besser]", fontsize=12)
        plt.xlabel("Nennstrom [A]", fontsize=12)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.xticks(rotation=0)
        beschrifte_bars(ax3, fmt="%.1fx", rotation=0)
        plt.legend(title="Maßnahme", bbox_to_anchor=(1.01, 1), loc="upper left")
        plt.tight_layout()
        plt.savefig("effizienz_faktoren_alle.png", dpi=300)
        print("Grafik gespeichert: effizienz_faktoren_alle.png")
        plt.close()

    erstelle_einzeldiagramme()

if __name__ == "__main__":
    lade_und_plotte_vergleich()