import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator

# --- KONFIGURATION ---
CSV_DATEI = "2026-02-11T11-12_export_ohne_5000A.csv"
SPALTEN_NAMEN = ["5% In", "20% In", "50% In", "80% In", "90% In", "100% In", "120% In"]
# X-Werte für die Linien-Plots
X_WERTE_LINIE = [5, 20, 50, 80, 90, 100, 120]

# --- STYLE KONSTANTEN (Allgemein) ---
FONT_TITLE = 24
FONT_AXIS_LABEL = 18
FONT_TICK_LABEL = 16
FONT_BAR_LABEL = 16

# --- STYLE KONSTANTEN (Für Linien-Plots Präsentation) ---
FIG_SIZE_LINE = (20, 12) 
FONT_SUBTITLE_LINE = 20
FONT_LEGEND_LINE = 16
LINE_WIDTH = 3
MARKER_SIZE = 10

# --- STYLE KONSTANTEN (Für Balken-Plots) ---
FIG_SIZE_BAR = (18, 10) # Etwas höher für bessere Lesbarkeit
FIXED_BAR_WIDTH = 0.3    
BAR_SPACING = 0.02       

# --- FARB DEFINITIONEN (Global) ---
COLOR_MBS_STD = "#d62728"    # Rot
COLOR_CELSA_STD = "#2366fc"  # Hellblau (Royal Blue)
COLOR_CELSA_KOMP = "#071080" # Dunkelblau (Navy)
COLOR_REDUR_FFP = "#1CAB10"  # Grün 

def get_custom_color(row):
    """
    Bestimmt die Basisfarbe basierend auf Hersteller und Technologie.
    """
    hersteller = str(row.get("hersteller", "")).lower()
    tech = str(row.get("technologie", "")).lower()
    
    if "mbs" in hersteller:
        if "standard" in tech: return COLOR_MBS_STD
            
    if "celsa" in hersteller:
        if "standard" in tech: return COLOR_CELSA_STD
        if "kompensiert" in tech: return COLOR_CELSA_KOMP
            
    if "redur" in hersteller: return COLOR_REDUR_FFP
    if "ffp" in tech: return COLOR_REDUR_FFP

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

# ==========================================
# TEIL 1: BALKEN DIAGRAMME (Dia 1 & 2)
# ==========================================

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
        
    plt.figure(figsize=FIG_SIZE_BAR)
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
        Patch(facecolor=COLOR_MBS_STD, edgecolor='black', label='MBS (Standard)'),
        Patch(facecolor=COLOR_CELSA_STD, edgecolor='black', label='Celsa (Standard)'),
        Patch(facecolor=COLOR_CELSA_KOMP, edgecolor='black', label='Celsa (Kompensiert)'),
        Patch(facecolor=COLOR_REDUR_FFP, edgecolor='black', label='Redur (FFP)'),
    ]
    ax.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1, 1), 
              fontsize=FONT_TICK_LABEL, title="Legende", title_fontsize=FONT_TICK_LABEL)

    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"Gespeichert {filename}")
    plt.close()

# ==========================================
# TEIL 2: HORIZONTALE FEHLER & KOSTEN
# ==========================================

def plot_horizontal_generic(data, value_col, title, x_label, filename, is_cost=False):
    """
    Generische Funktion für horizontale Balken (Fehler oder Kosten).
    """
    if data.empty:
        print(f"Keine Daten für {filename}")
        return

    # Sortierung für logische Gruppierung auf der Y-Achse
    # Erst nach Strom, dann Hersteller, dann Geometrie
    data = data.sort_values(by=["nennstrom", "hersteller", "modell", "geometrie"], 
                            ascending=[True, True, True, True])

    y_labels = []
    colors = []
    values = []
    geometries = []
    y_positions = [] 
    
    current_y = 0
    last_nennstrom = None
    GAP_SIZE = 1.5 

    # Iteration durch die Daten
    for _, row in data.iterrows():
        # Füge Abstand ein, wenn sich der Nennstrom ändert (visuelle Trennung)
        if last_nennstrom is not None and row['nennstrom'] != last_nennstrom:
            current_y += GAP_SIZE
        
        # Label bauen.
        # Format: "Hersteller Modell | Strom"
        label = f"{row['hersteller']} {row['modell']} | {row['nennstrom']} A"
        
        y_labels.append(label)
        colors.append(row['color'])
        values.append(row[value_col])
        geometries.append(row['geometrie'])
        
        y_positions.append(current_y)
        
        last_nennstrom = row['nennstrom']
        current_y += 1 

    # Höhe dynamisch anpassen
    dynamic_height = max(10, current_y * 0.5)
    
    plt.figure(figsize=(20, dynamic_height)) # Etwas breiter für lange Labels
    ax = plt.gca()
    
    bars = ax.barh(y_positions, values, color=colors, edgecolor="black", height=0.7)
    
    # Schraffur für Dreieck
    for bar, geo in zip(bars, geometries):
        if "dreieck" in str(geo).lower():
            bar.set_hatch('///')
    
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=16, fontweight='bold')
    ax.set_xlabel(x_label, fontsize=FONT_AXIS_LABEL)
    ax.set_title(title, fontsize=FONT_TITLE, fontweight='bold', pad=20)
    
    # Werte an die Balken schreiben
    max_val = max(values) if len(values) > 0 else 1
    
    for bar, val in zip(bars, values):
        width = bar.get_width()
        if pd.isna(val): continue
        
        if is_cost:
            label_text = f"{val:.2f} €"
        else:
            label_text = format_value(val)
            
        # Positionierung des Textes
        text_x = width + (max_val * 0.01)
        ax.text(text_x, bar.get_y() + bar.get_height()/2, label_text, 
                va='center', fontsize=14, fontweight='bold')

    ax.invert_yaxis() # Oberster Eintrag oben
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    
    # Legende erstellen
    legend_elements = [
        Patch(facecolor=COLOR_CELSA_STD, edgecolor='black', label='Celsa Std (Parallel)'),
        Patch(facecolor=COLOR_CELSA_STD, hatch='///', edgecolor='black', label='Celsa Std (Dreieck)'),
        Patch(facecolor=COLOR_CELSA_KOMP, edgecolor='black', label='Celsa Komp (Parallel)'),
        Patch(facecolor=COLOR_CELSA_KOMP, hatch='///', edgecolor='black', label='Celsa Komp (Dreieck)'),
        Patch(facecolor=COLOR_MBS_STD, edgecolor='black', label='MBS (Parallel)'),
        Patch(facecolor=COLOR_MBS_STD, hatch='///', edgecolor='black', label='MBS (Dreieck)'),
        Patch(facecolor=COLOR_REDUR_FFP, edgecolor='black', label='Redur (Parallel)'),
        Patch(facecolor=COLOR_REDUR_FFP, hatch='///', edgecolor='black', label='Redur (Dreieck)'),
    ]
    
    ax.legend(handles=legend_elements, loc="upper right", fontsize=14, ncol=2)

    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"Gespeichert {filename}")
    plt.close()

# ==========================================
# TEIL 3: LINIE KURVEN (Präsentation)
# ==========================================

def draw_limit_lines(ax):
    x_lims = [5, 20, 120]
    y_upper = [1.5, 1.0, 1.0]
    y_lower = [-1.5, -1.0, -1.0]
    
    ax.plot(x_lims, y_upper, color='black', linestyle='--', linewidth=2.5, alpha=1.0, label='Grenzwert')
    ax.plot(x_lims, y_lower, color='black', linestyle='--', linewidth=2.5, alpha=1.0)

def plot_line_curves_presentation(data):
    if data.empty:
        print("Keine Daten zum Plotten.")
        return

    if "nennstrom" in data.columns:
        unique_currents = data["nennstrom"].unique()
        try:
            unique_currents = sorted(unique_currents, key=lambda x: int(str(x).replace("A", "").strip()))
        except:
            pass
    else:
        return

    phase_col = None
    for col in data.columns:
        if "phase" in col.lower():
            phase_col = col
            break
    
    for current in unique_currents:
        print(f"Erstelle Linien-Plot für {current} A...")
        
        df_curr = data[data["nennstrom"] == current].copy()
        
        fig, axes = plt.subplots(1, 3, figsize=FIG_SIZE_LINE, sharey=True)
        fig.suptitle(f"Fehlerverlauf bei {current} A", fontsize=FONT_TITLE, fontweight='bold', y=0.96)
        
        phases = ["L1", "L2", "L3"]
        
        for i, ax in enumerate(axes):
            phase_name = phases[i]
            
            if phase_col:
                df_phase = df_curr[df_curr[phase_col].astype(str).str.contains(phase_name, case=False, na=False)]
            else:
                df_phase = df_curr
            
            ax.grid(True, which='both', linestyle='--', alpha=0.7)
            ax.axhline(0, color='black', linewidth=1)
            
            draw_limit_lines(ax)
            
            ax.set_title(f"Phase {phase_name}", fontsize=FONT_SUBTITLE_LINE, pad=10)
            ax.set_xlabel("Strom (% Nennstrom)", fontsize=FONT_AXIS_LABEL)
            if i == 0:
                ax.set_ylabel("Messabweichung (%)", fontsize=FONT_AXIS_LABEL)
            
            ax.set_xlim(0, 125)
            
            for idx, row in df_phase.iterrows():
                y_values = row[SPALTEN_NAMEN].values
                y_values = pd.to_numeric(y_values, errors='coerce')
                
                mask = ~np.isnan(y_values)
                if not np.any(mask): continue

                x_plot = np.array(X_WERTE_LINIE)[mask]
                y_plot = y_values[mask]

                color = get_custom_color(row)
                geo = str(row.get("geometrie", "")).lower()
                
                linestyle = "-"  
                marker = "o"     
                if "dreieck" in geo:
                    linestyle = "--" 
                    marker = "^"     
                
                label_txt = f"{row['hersteller']} {row['geometrie']}"
                
                ax.plot(x_plot, y_plot, 
                        marker=marker, markersize=MARKER_SIZE, 
                        linestyle=linestyle, linewidth=LINE_WIDTH, 
                        color=color, label=label_txt)
            
            ax.tick_params(axis='both', which='major', labelsize=FONT_TICK_LABEL)

        handles, labels = axes[0].get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        
        fig.legend(by_label.values(), by_label.keys(), 
                   loc='lower center', 
                   ncol=4, 
                   fontsize=FONT_LEGEND_LINE, 
                   bbox_to_anchor=(0.5, 0.02))
        
        plt.tight_layout(rect=[0, 0.15, 1, 0.95])
        
        filename = f"verlauf_{current}A_presentation.png"
        plt.savefig(filename, dpi=300)
        print(f"Gespeichert {filename}")
        plt.close()

# ==========================================
# HAUPTFUNKTION
# ==========================================

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
    
    for c in ["hersteller", "modell", "technologie", "geometrie", "nennstrom", "Phase", "phase"]:
        if c in df.columns: df[c] = df[c].astype(str).str.strip()
            
    for c in SPALTEN_NAMEN + ["Preis (€)"]:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")

    # Linien-Diagramme
    print("\n--- Erstelle Linien-Diagramme (Präsentation) ---")
    plot_line_curves_presentation(df)

    # Datenvorbereitung für Balken
    print("\n--- Bereite Daten für Balken-Diagramme vor ---")
    
    df_bar = df.copy()
    if "nennstrom" in df_bar.columns:
        df_bar["nennstrom_num"] = pd.to_numeric(df_bar["nennstrom"], errors="coerce")
        # Optional Filter setzen, falls nötig
        # df_bar = df_bar[df_bar["nennstrom_num"] != 5000]
        df_bar = df_bar.sort_values("nennstrom_num")
        # Wir behalten nennstrom_num für Sortierung
    
    # Aggregation
    df_bar["phase_mean_val"] = df_bar[SPALTEN_NAMEN].abs().mean(axis=1)
    
    agg_rules = {"phase_mean_val": "mean"}
    if "Preis (€)" in df_bar.columns: agg_rules["Preis (€)"] = "first"
    if "nennstrom_num" in df_bar.columns: agg_rules["nennstrom_num"] = "first"
    
    df_agg = df_bar.groupby(["nennstrom", "hersteller", "modell", "technologie", "geometrie"]).agg(agg_rules).reset_index()
    df_agg.rename(columns={"phase_mean_val": "total_error"}, inplace=True)
    df_agg["color"] = df_agg.apply(get_custom_color, axis=1)
    
    # Sortierung sicherstellen über numerischen Nennstrom
    if "nennstrom_num" in df_agg.columns:
        df_agg = df_agg.sort_values(by=["nennstrom_num", "hersteller", "modell", "geometrie"])
    
    # 1. Plot: Wahre Fehler Horizontal
    plot_horizontal_generic(df_agg, value_col="total_error", 
                            title="Wahre Fehler (Parallel vs. Dreieck)",
                            x_label="Mittlerer Fehler (Total Error)",
                            filename="diag0_wahre_fehler_horizontal.png", is_cost=False)

    # 2. Plot: Kosten Horizontal (NEU)
    plot_horizontal_generic(df_agg, value_col="Preis (€)", 
                            title="Kostenübersicht der Wandler",
                            x_label="Kosten [€]",
                            filename="diag_kosten_horizontal.png", is_cost=True)
    
    # 3. & 4. Plot: Verbesserung in % und €
    # Pivotisierung für Vergleich
    def get_sort_idx(r):
        h, t = r['hersteller'].lower(), r['technologie'].lower()
        if "mbs" in h: return 1
        if "celsa" in h and "standard" in t: return 2
        if "celsa" in h and "kompensiert" in t: return 3
        if "redur" in h: return 4
        return 99
    df_agg["sort_idx"] = df_agg.apply(get_sort_idx, axis=1)

    df_pivot = df_agg.pivot(
        index=["nennstrom", "hersteller", "modell", "technologie", "color", "sort_idx"],
        columns="geometrie",
        values=["total_error", "Preis (€)"]
    ).reset_index()
    
    df_pivot.columns = [f"{c[0]}_{c[1]}" if c[1] else c[0] for c in df_pivot.columns]

    if "total_error_Parallel" in df_pivot.columns and "total_error_Dreieck" in df_pivot.columns:
        df_pivot["imp_pct"] = (1 - (df_pivot["total_error_Dreieck"] / df_pivot["total_error_Parallel"])) * 100
        df_pivot["imp_pct_eur"] = df_pivot["imp_pct"] / df_pivot["Preis (€)_Parallel"]
        
        # Sortieren nach Nennstrom für die Ausgabe
        if "nennstrom" in df_pivot.columns:
             # Versuche numerische Sortierung
             try:
                 df_pivot["ns_sort"] = df_pivot["nennstrom"].astype(float)
             except:
                 df_pivot["ns_sort"] = 0
             df_pivot = df_pivot.sort_values("ns_sort")

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