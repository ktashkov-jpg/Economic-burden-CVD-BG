"""Run the full economic-burden analysis from the bundle root, in order.
Reads source_data/ only; overwrites output/ and figures/. Building the price panel reads 60 Excel files and takes about 5 minutes."""
import shutil, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
S, D, O = ROOT / 'scripts', ROOT / 'source_data', ROOT / 'output'
T1 = D / 'nhif' / 'nhif_table_1_cvd_2021_2025.csv'
O.mkdir(exist_ok=True); (ROOT / 'figures').mkdir(exist_ok=True)
steps = [
    ['build_price_panel_all.py', D / 'pdl', O],
    ['link_products.py', T1, O / 'pdl_panel_all.csv', O / 'product_links.csv'],
    ['patient_copay.py', T1, O / 'pdl_panel_all.csv', O / 'product_links.csv', O],
    ['econ_burden.py', D / 'nhif', O, D / 'reference' / 'observed_icd_lookup.csv', D / 'reference' / 'population_BG.csv'],
    ['figures.py', O],
    ['supplement.py', O, D / 'reference' / 'observed_icd_lookup.csv', O / 'supplement_tables.md'],
]
for name, *args in steps:
    print(f'--- {name}', flush=True)
    subprocess.run([sys.executable, str(S / name), *map(str, args)], check=True)
for png in O.glob('figure*.png'):
    shutil.move(str(png), ROOT / 'figures' / png.name)
print('done')
