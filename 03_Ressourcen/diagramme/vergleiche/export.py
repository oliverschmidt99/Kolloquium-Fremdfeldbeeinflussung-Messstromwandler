import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.patches import Patch

# --- KONFIGURATION ---
CSV_DATEI = "2026-02-11T11-12_export.csv"
SPALTEN_NAMEN = ["5% In", "20% In", "50% In", "80% In", "90% In", "100% In", "120% In"]

# --- STYLE KONSTANTEN ---
FIG_SIZE = (18, 9)
FONT_TITLE = 24
FONT_AXIS_LABEL = 18
FONT_TICK_LABEL = 16
FONT_BAR_LABEL = 16

# --- BALKEN KONFIGURATION ---
FIXED_BAR_WIDTH = 0.3    
BAR_SPACING = 0.02       

def get_custom_color(row):
    """
    Gibt nur noch die Basisfarben zurück.
    Die Unterscheidung Parallel/Dreieck erfolgt später über Muster (Hatch).
    """
    hersteller = str(row.get("hersteller", "")).lower()
    tech = str(row.get("technologie", "")).lower()
    
    c_rot = "#d62728"    # MBS Standard
    c_blau = "#1f77b4"   # Celsa Standard
    c_cyan = "#17becf"   # Celsa Kompensiert
    c_orange = "#ff7f0e" # Redur FFP
    
    if "mbs" in hersteller:
        if "standard" in tech: return c_rot
            
    if "celsa" in hersteller:
        if "standard" in tech: return c_blau
        if "kompensiert" in tech: return c_cyan
            
    if "redur" in hersteller: return c_orange
    if "ffp" in tech: return c_orange

    return "#7f7f7f"

def format_value(val):
    if pd.isna(val): return ""
    if val == 0: return "0"
    
    abs_val = abs(val)
    if abs_val < 0.1:
        return "< 0.1"
    
    if abs_val >= 10:
        return f"{val:.0f}"
    else:
        return f"{val:.1f}"

def plot_unified_bars(data, x_col, y_col, color_col, title, ylabel, filename, sort_col=None):
    if data.empty:
        print(f"Keine Daten für {filename}")
        return

    if sort_col and sort_col in data.columns:
        data = data.sort_values(sort_col)
    
    groups = data[x_col].unique()
    try:
        groups = sorted(groups, key=lambda x: int(x))
    except:
        pass 
        
    plt.figure(figsize=FIG_SIZE)
    ax = plt.gca()
    
    x_positions = []
    x_labels = []

    for i, group_val in enumerate(groups):
        sub = data[data[x_col] == group_val]
        
        if "sort_idx" in sub.columns:
            sub = sub.sort_values("sort_idx")
        
        n_bars = len(sub)
        if n_bars == 0: continue

        current_group_width = n_bars * FIXED_BAR_WIDTH
        group_start_x = i - (current_group_width / 2)
        
        for j in range(n_bars):
            row = sub.iloc[j]
            val = row[y_col]
            color = row[color_col]
            
            x_pos = group_start_x + (j * FIXED_BAR_WIDTH) + (FIXED_BAR_WIDTH / 2)
            
            if pd.notnull(val):
                draw_width = FIXED_BAR_WIDTH * (1 - BAR_SPACING)
                
                ax.bar(x_pos, val, 
                       width=draw_width, 
                       color=color, edgecolor="black", linewidth=1.5)
                
                txt = format_value(val)
                y_pos_txt = val + (val * 0.01) if val != 0 else 0
                va_align = 'bottom' if val >= 0 else 'top'
                if val < 0: y_pos_txt = val - (abs(val)*0.01)

                ax.text(x_pos, y_pos_txt, txt, 
                        ha='center', va=va_align, 
                        fontsize=FONT_BAR_LABEL, fontweight='bold', rotation=0)
        
        x_positions.append(i)
        if str(group_val).isdigit():
            x_labels.append(f"{group_val} A")
        else:
            x_labels.append(str(group_val))

    ax.set_xticks(x_positions)
    ax.set_xticklabels(x_labels, fontsize=FONT_TICK_LABEL, fontweight='bold')
    ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
    
    ax.set_ylabel(ylabel, fontsize=FONT_AXIS_LABEL)
    ax.set_title(title, fontsize=FONT_TITLE, fontweight='bold', pad=20)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    legend_elements = [
        Patch(facecolor="#d62728", edgecolor='black', label='MBS (Standard)'),
        Patch(facecolor="#1f77b4", edgecolor='black', label='Celsa (Standard)'),
        Patch(facecolor="#17becf", edgecolor='black', label='Celsa (Kompensiert)'),
        Patch(facecolor="#ff7f0e", edgecolor='black', label='Redur (FFP)'),
    ]
    ax.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1, 1), 
              fontsize=FONT_TICK_LABEL, title="Legende", title_fontsize=FONT_TICK_LABEL)

    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"Gespeichert {filename}")
    plt.close()

def plot_horizontal_errors(data, filename):
    """
    Erstellt ein horizontales Balkendiagramm der wahren Fehler.
    Dreieck wird durch Schraffur (///) dargestellt.
    Fügt einen Abstand (Gap) zwischen unterschiedlichen Stromstärken ein.
    """
    if data.empty:
        print(f"Keine Daten für {filename}")
        return

    # Sortierung
    data = data.sort_values(by=["nennstrom", "hersteller", "modell", "geometrie"], ascending=[True, True, True, True])

    y_labels = []
    colors = []
    values = []
    geometries = []
    y_positions = [] # Speichert die berechneten Y-Positionen
    
    current_y = 0
    last_nennstrom = None
    GAP_SIZE = 1.5 # Größe des Abstands zwischen den Blöcken

    for _, row in data.iterrows():
        # Abstand einfügen, wenn sich der Nennstrom ändert
        if last_nennstrom is not None and row['nennstrom'] != last_nennstrom:
            current_y += GAP_SIZE
        
        label = f"{row['hersteller']} {row['modell']} | {row['nennstrom']} A | {row['geometrie']}"
        y_labels.append(label)
        colors.append(row['color'])
        values.append(row['total_error'])
        geometries.append(row['geometrie'])
        
        y_positions.append(current_y)
        
        last_nennstrom = row['nennstrom']
        current_y += 1 # Standard-Abstand für den nächsten Balken

    # Dynamische Höhe basierend auf der letzten Y-Position berechnen
    dynamic_height = max(10, current_y * 0.6)
    
    plt.figure(figsize=(18, dynamic_height))
    ax = plt.gca()
    
    # Balken zeichnen mit den manuell berechneten y_positions
    bars = ax.barh(y_positions, values, color=colors, edgecolor="black", height=0.6)
    
    # Schraffur nachträglich anwenden
    for bar, geo in zip(bars, geometries):
        if "dreieck" in str(geo).lower():
            bar.set_hatch('///')
    
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=14, fontweight='bold')
    ax.set_xlabel("Mittlerer Fehler (Total Error)", fontsize=FONT_AXIS_LABEL)
    ax.set_title("Wahre Fehler (Parallel vs. Dreieck)", fontsize=FONT_TITLE, fontweight='bold', pad=20)
    
    # Labels an den Balken
    for bar, val in zip(bars, values):
        width = bar.get_width()
        label_text = format_value(val)
        ax.text(width + (max(values)*0.01), bar.get_y() + bar.get_height()/2, label_text, 
                va='center', fontsize=14, fontweight='bold')

    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    
    # Legende
    legend_elements = [
        Patch(facecolor="#1f77b4", edgecolor='black', label='Celsa Std (Parallel)'),
        Patch(facecolor="#1f77b4", hatch='///', edgecolor='black', label='Celsa Std (Dreieck)'),
        Patch(facecolor="#17becf", edgecolor='black', label='Celsa Komp (Parallel)'),
        Patch(facecolor="#17becf", hatch='///', edgecolor='black', label='Celsa Komp (Dreieck)'),
        Patch(facecolor="#d62728", edgecolor='black', label='MBS (Parallel)'),
        Patch(facecolor="#d62728", hatch='///', edgecolor='black', label='MBS (Dreieck)'),
        Patch(facecolor="#ff7f0e", edgecolor='black', label='Redur (Parallel)'),
        Patch(facecolor="#ff7f0e", hatch='///', edgecolor='black', label='Redur (Dreieck)'),
    ]
    
    ax.legend(handles=legend_elements, loc="upper right", fontsize=12, ncol=2)

    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"Gespeichert {filename}")
    plt.close()

def lade_und_plotte_alle():
    print(f"Lade Datei {CSV_DATEI} ...")
    
    if not os.path.exists(CSV_DATEI):
        print(f"Datei nicht gefunden {CSV_DATEI}")
        return

    try:
        df = pd.read_csv(CSV_DATEI, decimal=",", thousands=".")
    except Exception as e:
        print(f"Fehler {e}")
        return

    df.columns = df.columns.str.strip()
    df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")], errors="ignore")
    
    for c in ["hersteller", "modell", "technologie", "geometrie", "nennstrom"]:
        if c in df.columns: df[c] = df[c].astype(str).str.strip()
            
    for c in SPALTEN_NAMEN + ["Preis (€)"]:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")

    # --- FILTERUNG 5000 A ---
    if "nennstrom" in df.columns:
        df["nennstrom_num"] = pd.to_numeric(df["nennstrom"], errors="coerce")
        df = df[df["nennstrom_num"] != 5000]
        # Wir sortieren hier einmal numerisch vor, damit 2000 vor 10000 kommt, falls nötig
        df = df.sort_values("nennstrom_num")
        df = df.drop(columns=["nennstrom_num"])

    # --- FEHLER BERECHNUNG ---
    df["phase_mean_val"] = df[SPALTEN_NAMEN].abs().mean(axis=1)
    
    agg_rules = {"phase_mean_val": "mean"}
    if "Preis (€)" in df.columns: agg_rules["Preis (€)"] = "first"
    
    df_agg = df.groupby(["nennstrom", "hersteller", "modell", "technologie", "geometrie"]).agg(agg_rules).reset_index()
    df_agg.rename(columns={"phase_mean_val": "total_error"}, inplace=True)
    
    df_agg["color"] = df_agg.apply(get_custom_color, axis=1)
    
    def get_sort_idx(r):
        h, t = r['hersteller'].lower(), r['technologie'].lower()
        if "mbs" in h: return 1
        if "celsa" in h and "standard" in t: return 2
        if "celsa" in h and "kompensiert" in t: return 3
        if "redur" in h: return 4
        return 99
        
    df_agg["sort_idx"] = df_agg.apply(get_sort_idx, axis=1)

    # --- PLOT 0 NEU Wahre Fehler Horizontal (mit Abstand) ---
    plot_horizontal_errors(df_agg, "diag0_wahre_fehler_horizontal.png")
    
    # --- VORBEREITUNG DIAGRAMM 1 und 2 ---
    df_pivot = df_agg.pivot(
        index=["nennstrom", "hersteller", "modell", "technologie", "color", "sort_idx"],
        columns="geometrie",
        values=["total_error", "Preis (€)"]
    ).reset_index()
    
    df_pivot.columns = [f"{c[0]}_{c[1]}" if c[1] else c[0] for c in df_pivot.columns]

    if "total_error_Parallel" in df_pivot.columns and "total_error_Dreieck" in df_pivot.columns:
        df_pivot["imp_pct"] = (1 - (df_pivot["total_error_Dreieck"] / df_pivot["total_error_Parallel"])) * 100
        df_pivot["imp_pct_eur"] = df_pivot["imp_pct"] / df_pivot["Preis (€)_Parallel"]
        
        plot_unified_bars(df_pivot, x_col="nennstrom", y_col="imp_pct", color_col="color",
                          title="Diagramm 1 Verbesserung Dreiecksanordnung (%)", 
                          ylabel="Verbesserung [%]", 
                          filename="diag1_dreieck_pct.png", sort_col="nennstrom")

        plot_unified_bars(df_pivot, x_col="nennstrom", y_col="imp_pct_eur", color_col="color",
                          title="Diagramm 2 Wirtschaftlichkeit Dreieck (% pro €)", 
                          ylabel="Verbesserung [% / €]", 
                          filename="diag2_dreieck_pct_eur.png", sort_col="nennstrom")
    else:
        print("Konnte Diagramm 1 und 2 nicht erstellen, da Parallel/Dreieck Paarung fehlt.")

if __name__ == "__main__":
    lade_und_plotte_alle()