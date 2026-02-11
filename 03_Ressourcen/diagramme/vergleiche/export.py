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
# Damit alle Diagramme gleich dicke Balken haben
FIXED_BAR_WIDTH = 0.3   
BAR_SPACING = 0.02       

def get_custom_color(row):
    hersteller = str(row.get("hersteller", "")).lower()
    tech = str(row.get("technologie", "")).lower()
    
    c_rot = "#d62728"    # MBS Standard
    c_blau = "#1f77b4"   # Celsa Standard
    c_cyan = "#17becf"   # Celsa Kompensiert
    c_orange = "#ff7f0e" # Redur FFP
    c_grau = "#7f7f7f"

    if "mbs" in hersteller:
        if "standard" in tech: return c_rot
    if "celsa" in hersteller:
        if "standard" in tech: return c_blau
        if "kompensiert" in tech: return c_cyan
    if "redur" in hersteller: return c_orange
    if "ffp" in tech: return c_orange

    return c_grau

def format_value(val):
    if pd.isna(val): return ""
    if val == 0: return "0"
    
    abs_val = abs(val)
    
    # Neue Logik für Werte kleiner als 0.1
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

    # Sortierung
    if sort_col and sort_col in data.columns:
        data = data.sort_values(sort_col)
    
    # Gruppen bilden
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

        # --- Feste Breite Logik ---
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

    # --- FEHLER BERECHNUNG NEU ---
    # 1. Schritt: Mittelwert pro Zeile (Phase) über alle Messpunkte (5%...120%)
    # Wir nehmen den Betrag (.abs()), damit sich pos/neg Fehler nicht aufheben
    df["phase_mean_val"] = df[SPALTEN_NAMEN].abs().mean(axis=1)
    
    # 2. Schritt: Aggregation der Gruppen (z.B. L1, L2, L3 zusammenfassen)
    # Hier wird nun der Mittelwert der Phasen-Mittelwerte gebildet ("mean" statt "sum")
    agg_rules = {"phase_mean_val": "mean"}
    
    if "Preis (€)" in df.columns: agg_rules["Preis (€)"] = "first"
    
    df_agg = df.groupby(["nennstrom", "hersteller", "modell", "technologie", "geometrie"]).agg(agg_rules).reset_index()
    
    # Umbenennen für die weitere Verarbeitung (Kompatibilität wahren)
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
    
    # 1) Pivot
    df_pivot = df_agg.pivot(
        index=["nennstrom", "hersteller", "modell", "technologie", "color", "sort_idx"],
        columns="geometrie",
        values=["total_error", "Preis (€)"]
    ).reset_index()
    df_pivot.columns = [f"{c[0]}_{c[1]}" if c[1] else c[0] for c in df_pivot.columns]

    if "total_error_Parallel" in df_pivot.columns and "total_error_Dreieck" in df_pivot.columns:
        df_pivot["imp_pct"] = (1 - (df_pivot["total_error_Dreieck"] / df_pivot["total_error_Parallel"])) * 100
        df_pivot["imp_pct_eur"] = df_pivot["imp_pct"] / df_pivot["Preis (€)_Parallel"]
    else:
        df_pivot = pd.DataFrame()
        
    # 2) Parallel Basis
    df_par = df_agg[df_agg["geometrie"] == "Parallel"].copy()
    df_par["error_per_euro"] = df_par["total_error"] / df_par["Preis (€)"]

    # 3) Tech Agg
    tech_agg = df_par.groupby("technologie")["total_error"].mean().reset_index()
    cols_map = {"Standard": "#d62728", "Kompensiert": "#17becf", "FFP": "#ff7f0e"}
    sort_map = {"Standard": 1, "Kompensiert": 3, "FFP": 4} 
    tech_agg["color"] = tech_agg["technologie"].map(cols_map)
    tech_agg["sort_idx"] = tech_agg["technologie"].map(sort_map)
    
    # --- PLOTTEN ---
    
    plot_unified_bars(df_pivot, x_col="nennstrom", y_col="imp_pct", color_col="color",
                      title="Diagramm 1 Verbesserung Dreiecksanordnung (%)", 
                      ylabel="Verbesserung [%]", 
                      filename="diag1_dreieck_pct.png", sort_col="nennstrom")

    plot_unified_bars(df_pivot, x_col="nennstrom", y_col="imp_pct_eur", color_col="color",
                      title="Diagramm 2 Wirtschaftlichkeit Dreieck (% pro €)", 
                      ylabel="Verbesserung [% / €]", 
                      filename="diag2_dreieck_pct_eur.png", sort_col="nennstrom")

    plot_unified_bars(tech_agg, x_col="technologie", y_col="total_error", color_col="color",
                      title="Diagramm 3 Ø Mittlerer Fehler (Technologie-Vergleich)", 
                      ylabel="Mittlerer Fehler", 
                      filename="diag3_tech_error.png", sort_col="sort_idx")

    plot_unified_bars(df_par, x_col="nennstrom", y_col="total_error", color_col="color",
                      title="Diagramm 4 Mittlerer Gesamtfehler (Parallel)", 
                      ylabel="Mittlerer Fehler", 
                      filename="diag4_parallel_error.png", sort_col="nennstrom")

    plot_unified_bars(df_par, x_col="nennstrom", y_col="error_per_euro", color_col="color",
                      title="Diagramm 5 Mittlerer Fehler pro Euro (Parallel)", 
                      ylabel="Fehler / €", 
                      filename="diag5_parallel_error_eur.png", sort_col="nennstrom")

if __name__ == "__main__":
    lade_und_plotte_alle()