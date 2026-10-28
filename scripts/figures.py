"""Figures for the economic-burden manuscript (300 dpi PNG, one file per figure)."""
import sys
import pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT = sys.argv[1]
BLUE, ORANGE, INK, MUTED, GRID = '#2a78d6', '#eb6834', '#1f1f1e', '#6b6a63', '#e4e3dc'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK,
                     'xtick.color': MUTED, 'ytick.color': MUTED, 'axes.spines.top': False, 'axes.spines.right': False})

m = pd.read_csv(f'{OUT}/monthly_payer_patient.csv', parse_dates=['month'])
fig, ax = plt.subplots(figsize=(6.5, 3.6))
ax.plot(m.month, m.patient / 1e6, color=ORANGE, lw=2, marker='o', ms=2.5)
ax.plot(m.month, m.payer / 1e6, color=BLUE, lw=2, marker='o', ms=2.5)
ax.axvline(pd.Timestamp('2024-04-01'), color=MUTED, ls=':', lw=1)
ax.text(pd.Timestamp('2024-04-15'), 4.6, 'April 2024: 100 %\nreimbursement for\n407 products', color=MUTED, fontsize=7.5, va='bottom')
ax.text(m.month.iloc[-1] + pd.Timedelta(days=12), m.patient.iloc[-1] / 1e6, 'Patients\n(co-payments)', color=INK, fontsize=8, va='center')
ax.text(m.month.iloc[-1] + pd.Timedelta(days=12), m.payer.iloc[-1] / 1e6, 'NHIF', color=INK, fontsize=8, va='center')
import matplotlib.dates as mdates
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1])); ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.set_ylim(0, 20); ax.set_ylabel('EUR million per month'); ax.grid(axis='y', color=GRID, lw=0.6); ax.set_axisbelow(True)
ax.set_xlim(m.month.iloc[0] - pd.Timedelta(days=15), m.month.iloc[-1] + pd.Timedelta(days=110))
fig.tight_layout(); fig.savefig(f'{OUT}/figure1_monthly_payer_patient.png', dpi=300); plt.close(fig)

r = pd.read_csv(f'{OUT}/regional_2024.csv')
fig, ax = plt.subplots(figsize=(6.5, 4.4))
ax.scatter(100 * r.share65, r.hyp_per100, s=r['pop'] / 4000, color=BLUE, alpha=0.75, edgecolor='white', lw=1.5, zorder=3)
import numpy as np
w = r['pop']; b = np.polyfit(100 * r.share65, r.hyp_per100, 1, w=np.sqrt(w)); xs = np.linspace(18.5, 31.5, 10)
ax.plot(xs, np.polyval(b, xs), color=MUTED, lw=1, ls='--', zorder=2)
from adjustText import adjust_text
texts = [ax.text(100 * row.share65, row.hyp_per100, row.region, fontsize=6.5, color=INK) for _, row in r.iterrows()]
adjust_text(texts, x=list(100 * r.share65), y=list(r.hyp_per100), ax=ax, expand=(1.3, 1.6),
            arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.4))
ax.set_xlabel('Population aged 65 or over, % (1 January 2024)'); ax.set_ylabel('Treated hypertensive disease,\npersons per 100 population')
ax.grid(color=GRID, lw=0.6); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(f'{OUT}/figure2_regional_hypertension.png', dpi=300); plt.close(fig)
print('ok')
