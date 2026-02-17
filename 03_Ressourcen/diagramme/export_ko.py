import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
import re
from matplotlib.patches import Patch

# --- KONFIGURATION ---
CSV_DATEI = "export_sortiert.csv"
GENAUIGKEITSKLASSE = 1.0 

SPALTEN_NAMEN = ["5% In", "20% In", "50% In", "80% In", "90% In", "100% In", "120% In"]
X_WERTE_LINIE = [5, 20, 50, 80, 90, 100, 120]

# --- STYLE KONSTANTEN ---
FONT_TITLE = 24
FONT_AXIS_LABEL = 18
FONT_TICK_LABEL = 16
FONT_BAR_LABEL = 12
FONT_LEGEND = 16
BASE_HEIGHT_BAR = 10
FIXED_BAR_WIDTH = 0.25 # Schmaler, da wir jetzt 3 Balken pro Eintrag haben könnten

# --- FARB DEFINITIONEN ---
COLOR_MBS_STD = "#d62728"    
COLOR_CELSA_STD = "#2366fc"  
COLOR_CELSA_KOMP = "#071080" 
COLOR_REDUR_FFP = "#1CAB10"  

# Farben für die Bereiche
COLOR_RANGE_LOW = "#1f77b4"  # Blau
COLOR_RANGE_NOM = "#2ca02c"  # Grün
COLOR_RANGE_HIGH = "#d62728" # Rot

# ==========================================
# GRENZWERT FUNKTION
# ==========================================
def draw_din_limits(ax, klasse):
    x_vals = [5, 20, 100, 120]
    if klasse == 0.1: y_vals = [0.4, 0.2, 0.1, 0.1]
    elif klasse == 0.2: y_vals = [0.75, 0.35, 0.2, 0.2]
    elif klasse == 0.5: y_vals = [1.5, 0.75, 0.5, 0.5]
    elif klasse == 1.0: y_vals = [3.0, 1.5, 1.0, 1.0]
    else: y_vals = [3.0, 1.5, 1.0, 1.0]

    y_pos = np.array(y_vals)
    y_neg = -np.array(y_vals)
    ax.plot(x_vals, y_pos, color='black', linestyle='--', linewidth=2.5, alpha=0.8)
    ax.plot(x_vals, y_neg, color='black', linestyle='--', linewidth=2.5, alpha=0.8)

# ==========================================
# HELPER
# ==========================================
def is_dark_color(hex_color, threshold=0.5):
    try:
        c = mcolors.to_rgb(hex_color)
        return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) < threshold
    except:
        return False

def calculate_layout_adjustments(data, base_height, ncol=2):
    unique_items = len(data)
    n_rows = np.ceil(unique_items / ncol)
    height_factor = 0.8 if ncol == 1 else 0.6 
    extra_height = n_rows * height_factor
    total_height = max(base_height, base_height + extra_height - 5)
    needed_bottom_inches = 2.0 + (n_rows * 0.3)
    bottom_fraction = needed_bottom_inches / total_height
    bottom_fraction = min(0.60, max(0.25, bottom_fraction))
    return total_height, bottom_fraction

def format_label_text(row):
    h = str(row.get("hersteller", "")).strip()
    m = str(row.get("modell", "")).strip()
    if m.lower() in ["nan", "none", ""]: m = ""
    t = str(row.get("technologie", "")).strip()
    geo = str(row.get("geometrie", "")).strip()
    label = f"{h} {m} | {t}"
    if geo: label += f" ({geo})"
    return re.sub(r"\s+", " ", label).strip()

def create_dynamic_legend_handles(data, color_col="color"):
    legend_dict = {}
    if "nennstrom_num" in data.columns:
        data = data.sort_values(by=["nennstrom_num", "hersteller"])
    for _, row in data.iterrows():
        color = row.get(color_col, "#7f7f7f")
        geo = str(row.get("geometrie", "")).lower()
        is_tri = "dreieck" in geo
        hatch = "///" if is_tri else None
        edge_color = "white" if (is_tri and is_dark_color(color)) else "black"
        label = format_label_text(row)
        if label not in legend_dict:
            legend_dict[label] = Patch(facecolor=color, hatch=hatch, edgecolor=edge_color, label=label)
    return list(legend_dict.values())

def format_value(val):
    if pd.isna(val): return ""
    if val == 0: return "0"
    if abs(val) < 0.1: return "< 0.1"
    if abs(val) >= 10: return f"{val:.0f}"
    return f"{val:.1f}"

def get_custom_color(row):
    hersteller = str(row.get("hersteller", "")).lower()
    tech = str(row.get("technologie", "")).lower()
    if "mbs" in hersteller and "standard" in tech: return COLOR_MBS_STD
    if "celsa" in hersteller:
        if "standard" in tech: return COLOR_CELSA_STD
        if "kompensiert" in tech: return COLOR_CELSA_KOMP
    if "redur" in hersteller: return COLOR_REDUR_FFP
    if "ffp" in tech: return COLOR_REDUR_FFP
    return "#7f7f7f"

# ==========================================
# PLOT FUNKTIONEN
# ==========================================

def plot_unified_bars(data, x_col, y_col, color_col, title, ylabel, filename):
    data = data[data[y_col].notna() & (data[y_col] != 0)].copy()
    if data.empty: return

    groups = sorted(data[x_col].unique(), key=lambda x: int(str(x).replace("A", "").strip()) if str(x).isdigit() else str(x))
    calc_height, calc_bottom = calculate_layout_adjustments(data, BASE_HEIGHT_BAR, ncol=2)

    plt.figure(figsize=(20, calc_height))
    ax = plt.gca()

    x_positions, x_labels = [], []

    for i, group_val in enumerate(groups):
        sub = data[data[x_col] == group_val]
        if "sort_idx" in sub.columns: sub = sub.sort_values("sort_idx")
        n_bars = len(sub)
        if n_bars == 0: continue

        # Breite etwas anpassen
        bar_w = 0.3
        current_group_width = n_bars * bar_w
        group_start_x = i - (current_group_width / 2)

        for j in range(n_bars):
            row = sub.iloc[j]
            val = row[y_col]
            color = row[color_col]
            x_pos = group_start_x + (j * bar_w) + (bar_w / 2)
            edge_c = "white" if is_dark_color(color) else "black"
            
            ax.bar(x_pos, val, width=bar_w * 0.9, color=color, edgecolor=edge_c, linewidth=1.0)
            
            txt = format_value(val)
            y_pos_txt = val + (val * 0.02) if val >= 0 else val - (abs(val)*0.02)
            va_align = 'bottom' if val >= 0 else 'top'
            if val < 0 and abs(val) < 1: y_pos_txt = val - (abs(val)*0.05)

            ax.text(x_pos, y_pos_txt, txt, ha='center', va=va_align, fontsize=FONT_BAR_LABEL, fontweight='bold')

        x_positions.append(i)
        x_labels.append(f"{group_val} A")

    ax.set_xticks(x_positions)
    ax.set_xticklabels(x_labels, fontsize=FONT_TICK_LABEL, fontweight='bold')
    ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
    ax.set_ylabel(ylabel, fontsize=FONT_AXIS_LABEL)
    ax.set_title(title, fontsize=FONT_TITLE, fontweight='bold', pad=20)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    handles = create_dynamic_legend_handles(data, color_col)
    if handles:
        ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.15), fontsize=FONT_LEGEND, title="Legende", ncol=2)

    plt.tight_layout()
    plt.subplots_adjust(bottom=calc_bottom)
    plt.savefig(filename, dpi=300)
    print(f"Gespeichert {filename}")
    plt.close()

def plot_horizontal_generic(data, value_col, title, x_label, filename, is_cost=False):
    if "nennstrom_num" in data.columns:
        data = data.sort_values(by=["nennstrom_num", "hersteller", "modell", "geometrie"])
    
    y_labels, colors, values, geometries, y_positions = [], [], [], [], []
    current_y, last_ns, GAP = 0, None, 1.5

    for _, row in data.iterrows():
        if last_ns is not None and row['nennstrom'] != last_ns: current_y += GAP
        y_labels.append(f"{row['hersteller']} {row['modell']} | {row['nennstrom']} A")
        colors.append(row['color'])
        values.append(row[value_col])
        geometries.append(str(row.get('geometrie', '')))
        y_positions.append(current_y)
        last_ns = row['nennstrom']
        current_y += 1

    calc_height, calc_bottom = calculate_layout_adjustments(data, 10, ncol=2)
    final_height = max(calc_height, current_y * 0.6 + 4)

    plt.figure(figsize=(20, final_height))
    ax = plt.gca()
    
    bars = ax.barh(y_positions, values, color=colors, edgecolor="black", height=0.7)
    for bar, geo, col in zip(bars, geometries, colors):
        if "dreieck" in geo.lower():
            bar.set_hatch('///')
            if is_dark_color(col): bar.set_edgecolor('white')

    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=16, fontweight='bold')
    ax.set_xlabel(x_label, fontsize=FONT_AXIS_LABEL)
    ax.set_title(title, fontsize=FONT_TITLE, fontweight='bold', pad=20)
    
    max_val = max(values) if values else 1
    for bar, val in zip(bars, values):
        if pd.isna(val): continue
        label_text = f"{val:.2f} €" if is_cost else format_value(val)
        ax.text(bar.get_width() + (max_val * 0.01), bar.get_y() + bar.get_height()/2, label_text, va='center', fontsize=14, fontweight='bold')

    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    
    handles = create_dynamic_legend_handles(data)
    if handles:
        ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.05), fontsize=14, ncol=2)

    plt.tight_layout()
    plt.subplots_adjust(bottom=calc_bottom * 0.5)
    plt.savefig(filename, dpi=300)
    print(f"Gespeichert {filename}")
    plt.close()

def plot_range_analysis(data):
    """Erstellt gruppierte Balkendiagramme für Nieder-, Nenn- und Überlastfehler."""
    # Wir brauchen die Spalten
    req_cols = ["Nieder_Ges", "Nenn_Ges", "Ueber_Ges"]
    if not all(c in data.columns for c in req_cols):
        print("Spalten für Bereichsanalyse fehlen.")
        return

    unique_currents = sorted(data["nennstrom"].unique(), key=lambda x: int(str(x).replace("A", "").strip()) if str(x).isdigit() else x)

    for current in unique_currents:
        print(f"Erstelle Bereichs-Analyse für {current} A...")
        df_curr = data[data["nennstrom"] == current].copy()
        
        # Sortieren
        if "sort_idx" in df_curr.columns:
            df_curr = df_curr.sort_values(by=["sort_idx", "modell"])
        
        # Layout berechnen
        calc_height, calc_bottom = calculate_layout_adjustments(df_curr, 8, ncol=3)
        plt.figure(figsize=(20, max(10, calc_height)))
        ax = plt.gca()

        y_indices = np.arange(len(df_curr))
        height = 0.25 # Höhe eines Einzelbalkens

        # Daten holen
        v_low = df_curr["Nieder_Ges"].values
        v_nom = df_curr["Nenn_Ges"].values
        v_high = df_curr["Ueber_Ges"].values
        
        # Balken zeichnen (Gruppiert um y_index)
        # Überlast oben, Nenn mitte, Nieder unten (oder umgekehrt, je nach Geschmack)
        # Wir machen: Oben=Nieder, Mitte=Nenn, Unten=Überlast -> Y-Achse ist invertiert, also 0 oben.
        
        rects1 = ax.barh(y_indices - height, v_low, height, label='Niederlast (5-50% In)', color=COLOR_RANGE_LOW, edgecolor='black')
        rects2 = ax.barh(y_indices, v_nom, height, label='Nennlast (80-100% In)', color=COLOR_RANGE_NOM, edgecolor='black')
        rects3 = ax.barh(y_indices + height, v_high, height, label='Überlast (120% In)', color=COLOR_RANGE_HIGH, edgecolor='black')

        # Labels bauen
        y_labels = []
        for _, row in df_curr.iterrows():
             y_labels.append(format_label_text(row))
        
        ax.set_yticks(y_indices)
        ax.set_yticklabels(y_labels, fontsize=16, fontweight='bold')
        ax.set_xlabel("Mittlerer Fehler", fontsize=FONT_AXIS_LABEL)
        ax.set_title(f"Fehleranalyse nach Lastbereich ({current} A)", fontsize=FONT_TITLE, fontweight='bold', pad=20)
        
        # Werte anschreiben
        def label_bars(rects):
            for rect in rects:
                width = rect.get_width()
                if width == 0: continue
                txt = format_value(width)
                x_pos = width + (width*0.01) if width > 0 else width - (abs(width)*0.01)
                if abs(width) < 0.1 and width < 0: x_pos -= 0.02
                ha = 'left' if width > 0 else 'right'
                ax.text(x_pos, rect.get_y() + rect.get_height()/2, txt, ha=ha, va='center', fontsize=12, fontweight='bold')

        label_bars(rects1)
        label_bars(rects2)
        label_bars(rects3)

        ax.invert_yaxis() # Damit erster Eintrag oben ist
        ax.grid(axis="x", linestyle="--", alpha=0.5)
        
        # Legende
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=14)

        plt.tight_layout()
        plt.subplots_adjust(bottom=calc_bottom)
        
        filename = f"fehler_bereiche_{current}A.png"
        plt.savefig(filename, dpi=300)
        plt.close()

def plot_line_curves_presentation(data):
    if data.empty: return
    unique_currents = sorted(data["nennstrom"].unique(), key=lambda x: int(str(x).replace("A", "").strip()) if str(x).isdigit() else x)

    for current in unique_currents:
        print(f"Erstelle Linien-Plot für {current} A...")
        df_curr = data[data["nennstrom"] == current].copy()
        
        fig, axes = plt.subplots(1, 3, figsize=(24, 14), sharey=True)
        # TITEL NEU
        fig.suptitle(f"Genauigkeitsmessung bei {current} A (Klasse {GENAUIGKEITSKLASSE})", fontsize=FONT_TITLE, fontweight='bold', y=0.96)
        phases = ["L1", "L2", "L3"]
        
        for i, ax in enumerate(axes):
            phase = phases[i]
            cols = [f"{c}_{phase}" for c in SPALTEN_NAMEN]
            if not all(c in df_curr.columns for c in cols): continue

            ax.grid(True, which='both', linestyle='--', alpha=0.7)
            ax.axhline(0, color='black', linewidth=1)
            draw_din_limits(ax, GENAUIGKEITSKLASSE)
            
            ax.set_title(f"Phase {phase}", fontsize=22, pad=10)
            ax.set_xlabel("Strom (% Nennstrom)", fontsize=FONT_AXIS_LABEL)
            if i == 0: ax.set_ylabel("Messabweichung (%)", fontsize=FONT_AXIS_LABEL)
            ax.set_xlim(0, 125)

            for _, row in df_curr.iterrows():
                y_vals = pd.to_numeric(row[cols].values, errors='coerce')
                mask = ~np.isnan(y_vals)
                if not np.any(mask): continue
                x_plot = np.array(X_WERTE_LINIE)[mask]
                y_plot = y_vals[mask]
                col = get_custom_color(row)
                geo = str(row.get("geometrie", "")).lower()
                ls, mk = ("--", "^") if "dreieck" in geo else ("-", "o")
                ax.plot(x_plot, y_plot, marker=mk, markersize=10, linestyle=ls, linewidth=3, color=col)
            
            ax.tick_params(labelsize=FONT_TICK_LABEL)

        handles = create_dynamic_legend_handles(df_curr, "color")
        fig.legend(handles=handles, loc='lower center', ncol=4, fontsize=FONT_LEGEND, bbox_to_anchor=(0.5, 0.05))
        plt.tight_layout(rect=[0, 0.18, 1, 0.95])
        plt.savefig(f"verlauf_{current}A_presentation.png", dpi=300)
        plt.close()
        print(f"Gespeichert verlauf_{current}A_presentation.png")

# ==========================================
# HAUPTPROGRAMM
# ==========================================

def lade_und_plotte_alle():
    print(f"Lade Datei {CSV_DATEI} ...")
    if not os.path.exists(CSV_DATEI): return

    df = pd.read_csv(CSV_DATEI, sep=";", decimal=",", thousands=".")
    df.columns = df.columns.str.strip()
    df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")], errors="ignore")
    
    for c in ["hersteller", "modell", "technologie", "geometrie", "nennstrom"]:
        if c in df.columns: df[c] = df[c].astype(str).str.strip()
    
    # Sicherstellen, dass die neuen Spalten numerisch sind
    cols_num = ["Preis (€)", "Gesamtfehler", "Verbesserung Dreick", "Nieder_Ges", "Nenn_Ges", "Ueber_Ges"]
    for c in cols_num:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    
    if "nennstrom" in df.columns:
        df["nennstrom_num"] = pd.to_numeric(df["nennstrom"], errors="coerce")
        df = df.sort_values("nennstrom_num")

    df["color"] = df.apply(get_custom_color, axis=1)

    def get_sort_idx(r):
        h = str(r.get('hersteller','')).lower()
        if "mbs" in h: return 1
        if "celsa" in h: return 2
        if "redur" in h: return 4
        return 99
    df["sort_idx"] = df.apply(get_sort_idx, axis=1)

    print("\n--- Erstelle Plots ---")
    
    # 1. Linienverlauf
    plot_line_curves_presentation(df)

    # 2. Horizontal: Gesamtfehler
    if "Gesamtfehler" in df.columns:
        # TITEL NEU
        plot_horizontal_generic(df, "Gesamtfehler", "Gesamter absoluter Fehler der Messung", "Total Error", "diag0_wahre_fehler.png")

    # 3. Horizontal: Kosten
    if "Preis (€)" in df.columns:
        # TITEL NEU
        plot_horizontal_generic(df, "Preis (€)", "Übersicht der Kosten der Wandler", "Kosten [€]", "diag_kosten.png", is_cost=True)

    # 4. Vertikal: Verbesserung Dreieck
    if "Verbesserung Dreick" in df.columns:
        # TITEL NEU
        plot_unified_bars(df, "nennstrom", "Verbesserung Dreick", "color", 
                          "Parallel vs Dreieck", "Verbesserung [%]", "diag1_dreieck_pct.png")
    
    # 5. NEU: Bereichsanalyse (Nieder, Nenn, Über)
    plot_range_analysis(df)

if __name__ == "__main__":
    lade_und_plotte_alle()