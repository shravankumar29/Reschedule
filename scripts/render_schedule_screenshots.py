import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path

ARTIFACT_DIR = os.environ.get("ARTIFACT_DIR", os.path.join(os.path.dirname(__file__), "..", "artifacts"))
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# Color palettes matching ReSchedule design system
BG_COLOR = "#f5f6f4"
PANEL_BG = "#ffffff"
BORDER_COLOR = "#e1e6e3"
PRIMARY_COLOR = "#365c55"
TEXT_COLOR = "#25343b"
MUTED_TEXT = "#78838a"
GRID_COLOR = "#edf0ee"

JOB_COLORS = {
    'J-101': {'bg': '#2b6cb0', 'border': '#2c5282', 'text': '#ffffff'},
    'J-102': {'bg': '#b7791f', 'border': '#975a16', 'text': '#ffffff'},
    'J-103': {'bg': '#2c7a7b', 'border': '#234e52', 'text': '#ffffff'},
    'J-104': {'bg': '#6b46c1', 'border': '#553c9a', 'text': '#ffffff'},
    'J-105': {'bg': '#365c55', 'border': '#284640', 'text': '#ffffff'},
    'J-106': {'bg': '#2b6cb0', 'border': '#2c5282', 'text': '#ffffff'},
    'J-107': {'bg': '#b7791f', 'border': '#975a16', 'text': '#ffffff'},
    'J-108': {'bg': '#2c7a7b', 'border': '#234e52', 'text': '#ffffff'},
    'J-109': {'bg': '#6b46c1', 'border': '#553c9a', 'text': '#ffffff'},
    'J-110': {'bg': '#365c55', 'border': '#284640', 'text': '#ffffff'},
}

MACHINES = [
    ('CNC-1', 'CNC Turning Cell · 5-Axis', 'Running'),
    ('CNC-2', 'CNC Lathe Dual Spindle', 'Running'),
    ('MILL-1', 'Vertical Machining Center', 'Available'),
    ('MILL-2', 'Horizontal Milling 4-Axis', 'Running'),
    ('GRIND-1', 'Surface Precision Grinder', 'Running'),
]

WEEK1_DAYS = [
    ('Tue', '03 Nov', '2026-11-03'),
    ('Wed', '04 Nov', '2026-11-04'),
    ('Thu', '05 Nov', '2026-11-05'),
    ('Fri', '06 Nov', '2026-11-06'),
    ('Sat', '07 Nov', '2026-11-07'),
    ('Sun', '08 Nov', '2026-11-08'),
    ('Mon', '09 Nov', '2026-11-09'),
]

WEEK2_DAYS = [
    ('Tue', '10 Nov', '2026-11-10'),
    ('Wed', '11 Nov', '2026-11-11'),
    ('Thu', '12 Nov', '2026-11-12'),
    ('Fri', '13 Nov', '2026-11-13'),
    ('Sat', '14 Nov', '2026-11-14'),
    ('Sun', '15 Nov', '2026-11-15'),
    ('Mon', '16 Nov', '2026-11-16'),
]

WEEK1_OPS = [
    # Sat 07 Nov (index 4)
    ('CNC-1', 'J-101', 'Rough Turn', 4, 6.0, 9.0),
    ('CNC-1', 'J-101', 'Finish Turn', 4, 9.0, 11.0),
    ('CNC-2', 'J-102', 'Thread Cut', 4, 6.0, 10.0),
    ('CNC-2', 'J-102', 'Groove Cut', 4, 10.0, 12.5),
    ('MILL-1', 'J-104', 'Face Mill', 4, 6.0, 8.5),
    ('MILL-1', 'J-104', 'Side Slot', 4, 8.5, 10.0),
    ('MILL-2', 'J-103', 'End Mill Cavity', 4, 6.0, 9.5),
    ('GRIND-1', 'J-104', 'Base Polish', 4, 10.0, 11.0),
    ('GRIND-1', 'J-101', 'O.D. Grinding', 4, 11.0, 12.5),
    ('GRIND-1', 'J-102', 'Flat Grinding', 4, 12.5, 13.5),
    # Sun 08 Nov (index 5)
    ('MILL-2', 'J-105', 'Pocket Milling', 5, 6.0, 10.0),
    ('CNC-2', 'J-105', 'Bore Drilling', 5, 10.0, 12.0),
    ('GRIND-1', 'J-105', 'Surface Finish', 5, 12.0, 13.5),
    ('CNC-1', 'J-103', 'Contour Profile', 5, 10.5, 12.5),
    # Mon 09 Nov (index 6)
    ('GRIND-1', 'J-103', 'Final Micro-Lap', 6, 6.5, 8.5),
]

WEEK2_OPS = [
    # Tue 10 Nov (index 0)
    ('CNC-1', 'J-107', 'Shaft Turn', 0, 6.0, 8.0),
    ('CNC-2', 'J-106', 'Flange Face', 0, 6.0, 9.0),
    ('CNC-2', 'J-106', 'Internal Bore', 0, 9.0, 10.5),
    ('MILL-2', 'J-107', 'Keyway Slot', 0, 8.0, 10.5),
    ('GRIND-1', 'J-107', 'Shaft Journal', 0, 10.5, 11.5),
    # Wed 11 Nov (index 1)
    ('CNC-2', 'J-108', 'Spindle Sleeve', 1, 6.0, 8.5),
    ('MILL-2', 'J-109', 'Bracket Face', 1, 6.0, 7.5),
    ('MILL-2', 'J-109', 'Drill Hole Matrix', 1, 7.5, 8.5),
    ('GRIND-1', 'J-108', 'Cylindrical Grind', 1, 8.5, 10.5),
    # Thu 12 Nov (index 2)
    ('CNC-2', 'J-110', 'Housing Rough', 2, 6.0, 9.5),
    ('CNC-2', 'J-110', 'Housing Finish', 2, 9.5, 11.5),
    ('GRIND-1', 'J-110', 'Seal Face Grind', 2, 11.5, 13.0),
]

def render_week(week_label, week_days, ops, filename, is_week1=True):
    fig, ax = plt.subplots(figsize=(15, 9.2), dpi=140)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Top App Header
    ax.text(2, 97, "ReSchedule", fontsize=15, fontweight='bold', color=PRIMARY_COLOR)
    ax.text(12, 97.2, "Smart Automation for MSME Job Shops", fontsize=9, color=MUTED_TEXT)
    ax.text(82, 97, "PLANNING / CAPACITY VIEW", fontsize=8.5, fontweight='bold', color="#87928e")
    ax.text(98, 97, "Operational", fontsize=8.5, fontweight='bold', color="#4e7e67", ha='right')

    # Page Header Card
    hdr_box = patches.FancyBboxPatch((2, 88), 96, 7, boxstyle="square,pad=0",
                                    facecolor=PANEL_BG, edgecolor=BORDER_COLOR, linewidth=1)
    ax.add_patch(hdr_box)

    # View toggle buttons
    tg1 = patches.FancyBboxPatch((3.5, 89.5), 10, 4, boxstyle="round,pad=0.2,rounding_size=0.4",
                                facecolor="#f0f3f1", edgecolor=BORDER_COLOR, linewidth=1)
    ax.add_patch(tg1)
    ax.text(8.5, 91.5, "Daily view", fontsize=8.5, color=MUTED_TEXT, ha='center', va='center')

    tg2 = patches.FancyBboxPatch((14.5, 89.5), 11, 4, boxstyle="round,pad=0.2,rounding_size=0.4",
                                facecolor=PRIMARY_COLOR, edgecolor=PRIMARY_COLOR, linewidth=1)
    ax.add_patch(tg2)
    ax.text(20, 91.5, "Weekly view", fontsize=8.5, color="#ffffff", fontweight='bold', ha='center', va='center')

    # Date Navigator Center
    btn_prev = patches.Circle((42, 91.5), 1.8, facecolor="#f0f3f1", edgecolor=BORDER_COLOR, linewidth=1)
    ax.add_patch(btn_prev)
    ax.text(42, 91.5, "<", fontsize=10, fontweight='bold', color=TEXT_COLOR, ha='center', va='center')

    ax.text(50, 91.5, week_label, fontsize=11, fontweight='bold', color=TEXT_COLOR, ha='center', va='center')

    btn_next = patches.Circle((58, 91.5), 1.8, facecolor="#f0f3f1", edgecolor=BORDER_COLOR, linewidth=1)
    ax.add_patch(btn_next)
    ax.text(58, 91.5, ">", fontsize=10, fontweight='bold', color=TEXT_COLOR, ha='center', va='center')

    # Filters Right
    f1 = patches.FancyBboxPatch((72, 89.5), 11.5, 4, boxstyle="round,pad=0.2,rounding_size=0.4",
                               facecolor="#ffffff", edgecolor=BORDER_COLOR, linewidth=1)
    ax.add_patch(f1)
    ax.text(77.5, 91.5, "All machines ▾", fontsize=8, color="#5c6a66", ha='center', va='center')

    f2 = patches.FancyBboxPatch((85, 89.5), 11.5, 4, boxstyle="round,pad=0.2,rounding_size=0.4",
                               facecolor="#ffffff", edgecolor=BORDER_COLOR, linewidth=1)
    ax.add_patch(f2)
    ax.text(90.5, 91.5, "All orders ▾", fontsize=8, color="#5c6a66", ha='center', va='center')

    # Legend strip
    ax.text(3, 85, "LEGEND:", fontsize=7.5, fontweight='bold', color=MUTED_TEXT)
    leg_items = [
        ("#2b6cb0", "Scheduled"),
        ("#60a5fa", "Rescheduled (Alt Machine)"),
        ("#a45e54", "Breakdown / Downtime"),
        ("#4e7e67", "Completed / Frozen"),
    ]
    cur_x = 10
    for col, txt in leg_items:
        patch = patches.Rectangle((cur_x, 84.7), 1.6, 1.2, facecolor=col, edgecolor='none')
        ax.add_patch(patch)
        ax.text(cur_x + 2.2, 85.2, txt, fontsize=7.5, color=TEXT_COLOR, va='center')
        cur_x += len(txt) * 0.7 + 6

    # Gantt Panel Outer Box
    gantt_box = patches.FancyBboxPatch((2, 10), 96, 72, boxstyle="square,pad=0",
                                      facecolor=PANEL_BG, edgecolor=BORDER_COLOR, linewidth=1)
    ax.add_patch(gantt_box)

    # Gantt Header (7 Day Columns)
    m_lane_w = 17.0
    timeline_w = 96.0 - m_lane_w
    day_w = timeline_w / 7.0

    # Machine header
    ax.text(2 + m_lane_w / 2, 80, "MACHINE / 7-DAY HORIZON", fontsize=7.5, fontweight='bold',
            color="#87928e", ha='center', va='center')

    # Day columns headers
    for i, (day_name, date_str, ymd) in enumerate(week_days):
        x_left = 2 + m_lane_w + i * day_w
        # Highlight Friday/Saturday demo day in Week 1 or Tuesday in Week 2
        is_highlight = (is_week1 and i == 4) or (not is_week1 and i == 0)
        hdr_fill = "#f0fdf4" if is_highlight else "#fafbfa"
        day_box = patches.Rectangle((x_left, 77), day_w, 5, facecolor=hdr_fill,
                                    edgecolor=BORDER_COLOR, linewidth=0.8)
        ax.add_patch(day_box)
        ax.text(x_left + day_w / 2, 80.2, day_name, fontsize=8, fontweight='bold',
                color="#166534" if is_highlight else TEXT_COLOR, ha='center')
        ax.text(x_left + day_w / 2, 78.4, date_str, fontsize=7,
                color="#166534" if is_highlight else MUTED_TEXT, ha='center')

    # Horizontal divider under header
    ax.plot([2, 98], [77, 77], color=BORDER_COLOR, linewidth=1)

    # Machine Lanes
    row_h = 13.0
    for idx, (m_id, m_name, m_stat) in enumerate(MACHINES):
        y_bot = 77 - (idx + 1) * row_h
        y_top = y_bot + row_h

        # Machine label column
        ax.text(3.5, y_bot + 8.5, m_id, fontsize=9.5, fontweight='bold', color=PRIMARY_COLOR)
        ax.text(3.5, y_bot + 4.5, m_name, fontsize=6.8, color=MUTED_TEXT)
        # Status pill
        stat_col = "#eaf1ec" if m_stat == "Available" else "#e2edf1"
        stat_txt_col = "#3d6a54" if m_stat == "Available" else "#2b6cb0"
        s_pill = patches.FancyBboxPatch((13, y_bot + 7.5), 5.5, 3.0, boxstyle="round,pad=0.1,rounding_size=0.5",
                                       facecolor=stat_col, edgecolor="none")
        ax.add_patch(s_pill)
        ax.text(15.75, y_bot + 9.0, m_stat, fontsize=6.5, fontweight='bold', color=stat_txt_col, ha='center', va='center')

        # Vertical machine divider
        ax.plot([2 + m_lane_w, 2 + m_lane_w], [y_bot, y_top], color=BORDER_COLOR, linewidth=1)

        # 7 Day Grid vertical lines for this row
        for i in range(7):
            x_line = 2 + m_lane_w + i * day_w
            # Slight tinted column background for active day
            is_highlight = (is_week1 and i == 4) or (not is_week1 and i == 0)
            if is_highlight:
                col_rect = patches.Rectangle((x_line, y_bot), day_w, row_h,
                                            facecolor="#f0fdf4", alpha=0.35, edgecolor="none")
                ax.add_patch(col_rect)
            ax.plot([x_line, x_line], [y_bot, y_top], color=GRID_COLOR, linewidth=0.8)

        # Breakdown on CNC-1 on Friday 07 Nov (Week 1)
        if is_week1 and m_id == 'CNC-1':
            day_idx = 4
            x_day = 2 + m_lane_w + day_idx * day_w
            # 10:00 to 13:00 -> 4h from 6am (10-6=4) to 7h from 6am (13-6=7) out of 16h horizon
            x_dt = x_day + (4.0 / 16.0) * day_w
            w_dt = (3.0 / 16.0) * day_w
            dt_box = patches.FancyBboxPatch((x_dt, y_bot + 2.0), w_dt, 8.8, boxstyle="round,pad=0.1,rounding_size=0.3",
                                           facecolor="#f5e3e0", edgecolor="#c78376", linewidth=1.5, hatch="//")
            ax.add_patch(dt_box)
            ax.text(x_dt + w_dt / 2, y_bot + 6.4, "⚠ DOWNTIME", fontsize=6.2, fontweight='bold',
                    color="#a45e54", ha='center', va='center')
            ax.text(x_dt + w_dt / 2, y_bot + 3.8, "10:00–13:00", fontsize=5.8,
                    color="#a45e54", ha='center', va='center')

        # Scheduled Operations in this machine
        machine_ops = [op for op in ops if op[0] == m_id]
        if not machine_ops and not (is_week1 and m_id == 'CNC-1'):
            ax.text(2 + m_lane_w + 3, y_bot + 6.5, "Available · No operations scheduled",
                    fontsize=7.5, fontstyle='italic', color="#a1aaa7")
        else:
            lane_offsets = {}
            for op in machine_ops:
                _, j_id, op_name, d_idx, s_hr, e_hr = op
                x_day = 2 + m_lane_w + d_idx * day_w
                # relative hour from 06:00
                rel_s = s_hr - 6.0
                rel_e = e_hr - 6.0
                dur = max(0.6, rel_e - rel_s)

                x_op = x_day + (rel_s / 16.0) * day_w
                w_op = max(1.8, min(day_w - (x_op - x_day), (dur / 16.0) * day_w))

                # Stagger lanes if multiple ops in same day/machine
                lane = lane_offsets.get(d_idx, 0)
                lane_offsets[d_idx] = 1 - lane
                y_bar = y_bot + (5.5 if lane == 0 else 1.5)
                h_bar = 5.2

                c = JOB_COLORS.get(j_id, {'bg': '#2b6cb0', 'border': '#2c5282', 'text': '#ffffff'})
                bar = patches.FancyBboxPatch((x_op, y_bar), w_op, h_bar, boxstyle="round,pad=0.1,rounding_size=0.3",
                                            facecolor=c['bg'], edgecolor=c['border'], linewidth=1)
                ax.add_patch(bar)

                # Bar text
                ax.text(x_op + 0.3, y_bar + 3.4, j_id, fontsize=6.8, fontweight='bold', color=c['text'])
                ax.text(x_op + 0.3, y_bar + 1.2, op_name[:9], fontsize=5.8, color="#e2e8f0")

        # Row bottom divider
        ax.plot([2, 98], [y_bot, y_bot], color=BORDER_COLOR, linewidth=1)

    # Footer metrics summary inside schedule page
    ft_y = 5.0
    ax.text(3, ft_y, f"Displaying schedule for horizon: {week_label}", fontsize=8, color=MUTED_TEXT)
    ax.text(97, ft_y, "100% Deterministic CP-SAT Mathematical Model · Zero Unplanned Overlaps",
            fontsize=8, fontweight='bold', color=PRIMARY_COLOR, ha='right')

    plt.tight_layout()
    out_path = os.path.join(ARTIFACT_DIR, filename)
    plt.savefig(out_path, dpi=140, bbox_inches='tight')
    plt.close()
    print(f"Generated: {out_path}")
    return out_path

render_week("03 – 09 November 2026", WEEK1_DAYS, WEEK1_OPS, "schedule_week1_nov03_09.png", is_week1=True)
render_week("10 – 16 November 2026", WEEK2_DAYS, WEEK2_OPS, "schedule_week2_nov10_16.png", is_week1=False)

