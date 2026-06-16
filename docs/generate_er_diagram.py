
"""
generate_er_diagram.py
Draws a clean ER diagram for the Bus Pass Management System
and saves it to docs/screenshots/er_diagram.png
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "screenshots", "er_diagram.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

fig, ax = plt.subplots(figsize=(22, 16))
ax.set_xlim(0, 22)
ax.set_ylim(0, 16)
ax.axis("off")
ax.set_facecolor("#f8f9fa")
fig.patch.set_facecolor("#f8f9fa")

# ── colour palette ──────────────────────────────────────────────────────────
C_HDR  = "#1a237e"   # dark navy – header bg
C_ROW  = "#e8eaf6"   # light lavender – row bg
C_ROW2 = "#c5cae9"   # slightly darker – alternate row
C_LINE = "#1a237e"   # relationship lines
C_PK   = "#b71c1c"   # primary key text
C_FK   = "#1b5e20"   # foreign key text
C_TEXT = "#212121"
C_WHT  = "#ffffff"

# ── entity definitions  (x, y, width, height, name, [(col, type, pk/fk/-)]) ─
entities = [
    # x,   y,   w,   h,   name
    (0.4,  10.5, 3.8, 4.8, "Passenger",
     [("passenger_id","INT","PK"),
      ("full_name",   "VARCHAR(100)",""),
      ("email",       "VARCHAR(150)","UQ"),
      ("phone",       "VARCHAR(15)",""),
      ("address",     "TEXT",""),
      ("category",    "ENUM",""),
      ("password",    "VARCHAR(255)",""),
      ("photo",       "LONGTEXT",""),
      ("doc_proof",   "LONGTEXT",""),
      ("doc_status",  "VARCHAR(20)",""),
      ("registered_at","DATETIME","")]),

    (5.2,  10.5, 3.8, 3.0, "Route",
     [("route_id",    "INT","PK"),
      ("source",      "VARCHAR(100)",""),
      ("destination", "VARCHAR(100)",""),
      ("base_fare",   "DECIMAL(10,2)","")]),

    (10.0, 10.5, 4.0, 4.2, "Pass_Application",
     [("application_id","INT","PK"),
      ("passenger_name","VARCHAR(100)","FK"),
      ("route_id",      "INT","FK"),
      ("pass_type",     "ENUM",""),
      ("duration_months","INT",""),
      ("status",        "ENUM",""),
      ("created_at",    "TIMESTAMP","")]),

    (15.2, 10.5, 3.8, 3.4, "Pass",
     [("pass_id",       "INT","PK"),
      ("passenger_name","VARCHAR(100)","FK"),
      ("pass_type",     "ENUM",""),
      ("valid_until",   "DATE",""),
      ("status",        "ENUM",""),
      ("qr_code",       "LONGTEXT","")]),

    (0.4,  4.8,  3.8, 3.0, "Concession_Category",
     [("category_id",   "INT","PK"),
      ("category_name", "VARCHAR(50)","UQ"),
      ("concession_rate","DECIMAL(5,2)",""),
      ("description",   "TEXT","")]),

    (5.2,  4.8,  3.8, 3.0, "Payment",
     [("payment_id",    "INT","PK"),
      ("application_id","INT","FK"),
      ("amount",        "DECIMAL(10,2)",""),
      ("payment_mode",  "ENUM",""),
      ("payment_date",  "DATE","")]),

    (10.0, 4.8,  3.8, 3.0, "Alert",
     [("alert_id",      "INT","PK"),
      ("passenger_name","VARCHAR(100)","FK"),
      ("message",       "TEXT",""),
      ("alert_date",    "DATE",""),
      ("is_read",       "BOOLEAN","")]),

    (15.2, 4.8,  3.8, 3.2, "Feedback",
     [("feedback_id",   "INT","PK"),
      ("passenger_name","VARCHAR(100)","FK"),
      ("message",       "TEXT",""),
      ("submitted_at",  "DATETIME",""),
      ("admin_response","TEXT","")]),
]

def draw_entity(ax, x, y, w, h, name, cols):
    row_h = 0.32
    # header box
    hdr = FancyBboxPatch((x, y + h - 0.5), w, 0.5,
                         boxstyle="round,pad=0.02",
                         linewidth=1.5, edgecolor=C_HDR,
                         facecolor=C_HDR)
    ax.add_patch(hdr)
    ax.text(x + w/2, y + h - 0.25, name,
            ha="center", va="center", fontsize=9,
            fontweight="bold", color=C_WHT, fontfamily="monospace")

    # rows
    for i, (col, typ, flag) in enumerate(cols):
        ry = y + h - 0.5 - (i+1)*row_h
        bg = C_ROW if i % 2 == 0 else C_ROW2
        rect = FancyBboxPatch((x, ry), w, row_h,
                              boxstyle="square,pad=0",
                              linewidth=0.5, edgecolor="#9fa8da",
                              facecolor=bg)
        ax.add_patch(rect)

        # flag icon
        if flag == "PK":
            icon = "[PK] "
            col_color = C_PK
        elif flag == "FK":
            icon = "[FK] "
            col_color = C_FK
        elif flag == "UQ":
            icon = "[UQ] "
            col_color = "#6a1b9a"
        else:
            icon = "     "
            col_color = C_TEXT

        ax.text(x + 0.12, ry + row_h/2,
                f"{icon}{col}",
                ha="left", va="center", fontsize=6.8,
                color=col_color,
                fontweight="bold" if flag in ("PK","FK") else "normal",
                fontfamily="monospace")
        ax.text(x + w - 0.08, ry + row_h/2,
                typ,
                ha="right", va="center", fontsize=6,
                color="#546e7a", fontfamily="monospace")

    # outer border
    border = FancyBboxPatch((x, y), w, h,
                            boxstyle="round,pad=0.02",
                            linewidth=2, edgecolor=C_HDR,
                            facecolor="none")
    ax.add_patch(border)
    return {
        "x": x, "y": y, "w": w, "h": h,
        "cx": x + w/2, "cy": y + h/2,
        "top":    (x+w/2, y+h),
        "bottom": (x+w/2, y),
        "left":   (x,     y+h/2),
        "right":  (x+w,   y+h/2),
    }

# ── draw all entities and collect positions ─────────────────────────────────
positions = {}
for ent in entities:
    x, y, w, h, name, cols = ent
    positions[name] = draw_entity(ax, x, y, w, h, name, cols)

# ── draw relationships ───────────────────────────────────────────────────────
REL_STYLE = dict(arrowstyle="-|>", color=C_LINE,
                 lw=1.4, connectionstyle="arc3,rad=0.0")

def arrow(ax, src, dst, src_side="right", dst_side="left",
          label="", rad=0.0):
    sp = positions[src][src_side]
    dp = positions[dst][dst_side]
    ax.annotate("",
                xy=dp, xytext=sp,
                arrowprops=dict(arrowstyle="-|>", color=C_LINE,
                                lw=1.4,
                                connectionstyle=f"arc3,rad={rad}"))
    if label:
        mx = (sp[0]+dp[0])/2
        my = (sp[1]+dp[1])/2
        ax.text(mx, my+0.15, label, ha="center", va="bottom",
                fontsize=6.5, color="#37474f",
                bbox=dict(boxstyle="round,pad=0.1", fc="#fffde7",
                          ec="#fbc02d", lw=0.8))

# Passenger → Pass_Application  (1:N)
arrow(ax, "Passenger",      "Pass_Application", "right","left",  "1:N applies")
# Route → Pass_Application  (1:N)
arrow(ax, "Route",          "Pass_Application", "right","left",  "1:N used in", rad=0.15)
# Pass_Application → Pass  (1:1 on approve)
arrow(ax, "Pass_Application","Pass",            "right","left",  "1:1 generates")
# Pass_Application → Payment  (1:1)
arrow(ax, "Pass_Application","Payment",         "bottom","top",  "1:1 paid via", rad=-0.1)
# Passenger → Alert  (1:N)
arrow(ax, "Passenger",      "Alert",            "bottom","top",  "1:N alerts",   rad=0.25)
# Passenger → Feedback  (1:N)
arrow(ax, "Passenger",      "Feedback",         "bottom","right","1:N submits",  rad=0.2)
# Concession_Category → Passenger  (1:N category based)
arrow(ax, "Concession_Category","Passenger",    "right","bottom","applies to",   rad=-0.2)

# ── title & legend ───────────────────────────────────────────────────────────
ax.text(11, 15.5,
        "Bus Pass Management System – Entity Relationship Diagram",
        ha="center", va="center", fontsize=14, fontweight="bold",
        color=C_HDR)

ax.text(11, 15.1,
        "BCS403 DBMS Mini Project  |  Bangalore Institute of Technology  |  2025-26",
        ha="center", va="center", fontsize=9, color="#546e7a")

# legend
leg_items = [
    mpatches.Patch(facecolor=C_HDR,   label="Entity / Table"),
    mpatches.Patch(facecolor="#ffcdd2",label="PK  – Primary Key",    edgecolor=C_PK,  lw=1),
    mpatches.Patch(facecolor="#c8e6c9",label="FK  – Foreign Key",    edgecolor=C_FK,  lw=1),
    mpatches.Patch(facecolor="#e1bee7",label="UQ  – Unique",         edgecolor="#6a1b9a",lw=1),
    mpatches.Patch(facecolor="none",   label="——▶  Relationship",
                   edgecolor=C_LINE, lw=1.4),
]
ax.legend(handles=leg_items, loc="lower left",
          fontsize=8, framealpha=0.9,
          edgecolor="#90a4ae", facecolor="#eceff1")

plt.tight_layout(pad=0.5)
plt.savefig(OUT, dpi=180, bbox_inches="tight",
            facecolor=fig.get_facecolor())
plt.close()
print(f"[DONE] ER diagram saved: {OUT}")
