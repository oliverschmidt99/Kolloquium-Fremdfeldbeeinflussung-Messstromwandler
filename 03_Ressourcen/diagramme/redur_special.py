import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
import re
from matplotlib.patches import Patch

# --- KONFIGURATION ---
CSV_DATEI = "export_sortiert.csv"
TARGET_CURRENT = "2000"         # Filter für 2000 A
TARGET_MANUFACTURER = "Redur"   # Filter für Redur
PLOT_TITLE = "Fremdfeld-Protektoren Redur bei 2000 A (Klasse 1.)"
GENAUIGKEITSKLASSE = 1.0        # Klasse 1 Grenzwerte

SPALTEN_NAMEN = ["5% In", "20% In", "50% In", "80% In", "90% In", "100% In", "120% In"]
X_WERTE_LINIE = [5, 20, 50, 80, 90, 100, 120]

# --- STYLE ---
FONT_TITLE = 24
FONT_AXIS_LABEL = 18
FONT_TICK_LABEL = 16
FONT_LEGEND = 16
COLOR_REDUR = "#1CAB10"  # Grün

# ==========================================
# PLOT FUNKTION
# ==========================================
def plot_single_redur():
    print(f"Lade Datei {CSV_DATEI} ...")
    if not os.path.exists(CSV_DATEI):
        print("Datei nicht gefunden!")
        return

    # Daten laden
    df = pd.read_csv(CSV_DATEI, sep=";", decimal=",", thousands=".")
    
    # Bereinigen
    df.columns = df.columns.str.strip()
    df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")], errors="ignore")
    for c in ["hersteller", "modell", "technologie", "geometrie", "nennstrom"]:
        if c in df.columns: df[c] = df[c].astype(str).str.strip()

    # Filterung: 2000 A & Redur
    # Nennstrom bereinigen (falls "2000A" drinsteht)
    df["nennstrom_clean"] = df["nennstrom"].str.replace("A", "").str.strip()
    
    df_filtered = df[
        (df["nennstrom_clean"] == TARGET_CURRENT) & 
        (df["hersteller"].str.contains(TARGET_MANUFACTURER, case=False, na=False))
    ].copy()
    
    if df_filtered.empty:
        print(f"Keine Daten für {TARGET_MANUFACTURER} bei {TARGET_CURRENT} A gefunden!")
        return

    print(f"Erstelle Plot für {len(df_filtered)} Datensätze...")

    # Plot erstellen
    fig, axes = plt.subplots(1, 3, figsize=(24, 14), sharey=True)
    fig.suptitle(PLOT_TITLE, fontsize=FONT_TITLE, fontweight='bold', y=0.96)
    phases = ["L1", "L2", "L3"]
    
    for i, ax in enumerate(axes):
        phase = phases[i]
        cols = [f"{c}_{phase}" for c in SPALTEN_NAMEN]
        
        # Grid
        ax.grid(True, which='both', linestyle='--', alpha=0.7)
        ax.axhline(0, color='black', linewidth=1)
        
        # Grenzwerte Klasse 1 zeichnen
        x_lims = [5, 20, 100, 120]
        y_lims = [3.0, 1.5, 1.0, 1.0] # Klasse 1 Werte
        ax.plot(x_lims, y_lims, 'k--', lw=2.5, alpha=0.8, label='Grenzwert') # Label nur für interne Referenz
        ax.plot(x_lims, [-y for y in y_lims], 'k--', lw=2.5, alpha=0.8)
        
        ax.set_title(f"Phase {phase}", fontsize=22, pad=10)
        ax.set_xlabel("Strom (% Nennstrom)", fontsize=FONT_AXIS_LABEL)
        if i == 0: ax.set_ylabel("Messabweichung (%)", fontsize=FONT_AXIS_LABEL)
        ax.set_xlim(0, 125)
        
        # WICHTIG: Kein set_ylim -> Autoscale aktiv!

        # Daten plotten
        for _, row in df_filtered.iterrows():
            # Y-Werte holen
            y_vals = pd.to_numeric(row[cols].values, errors='coerce')
            mask = ~np.isnan(y_vals)
            if not np.any(mask): continue
            
            x_plot = np.array(X_WERTE_LINIE)[mask]
            y_plot = y_vals[mask]
            
            # Style
            geo = str(row.get("geometrie", "")).lower()
            ls, mk = ("--", "^") if "dreieck" in geo else ("-", "o")
            
            # Label bauen
            lbl = f"{row['hersteller']} {row['modell']} | {row['technologie']}"
            if "dreieck" in geo: lbl += " (Dreieck)"
            
            ax.plot(x_plot, y_plot, marker=mk, markersize=10, linestyle=ls, linewidth=3, color=COLOR_REDUR, label=lbl)
            
        ax.tick_params(labelsize=FONT_TICK_LABEL)

    # Legende (nur einmal sammeln)
    handles, labels = axes[0].get_legend_handles_labels()
    # Grenzwert aus Legende entfernen, falls nicht gewünscht (du sagtest "In den Legenden muss die Grenze nicht stehen")
    # Wir filtern alles raus, was "Grenzwert" heißt
    unique_handles = {}
    for h, l in zip(handles, labels):
        if "grenzwert" not in l.lower():
            unique_handles[l] = h
            
    fig.legend(unique_handles.values(), unique_handles.keys(), loc='lower center', ncol=2, fontsize=FONT_LEGEND, bbox_to_anchor=(0.5, 0.05))
    
    plt.tight_layout(rect=[0, 0.15, 1, 0.95])
    filename = f"redur_{TARGET_CURRENT}A_special.png"
    plt.savefig(filename, dpi=300)
    print(f"Gespeichert: {filename}")
    plt.close()

if __name__ == "__main__":
    plot_single_redur()