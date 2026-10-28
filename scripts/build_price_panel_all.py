"""Monthly Positive Drug List (Annex 1) panel for all ATC groups, plus Annex 4 maximum prices.
One row per snapshot month x national number x ICD list (active rows only)."""
import re, sys, warnings
from pathlib import Path
import openpyxl, pandas as pd
warnings.filterwarnings('ignore')
SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2])

def num(x):
    try: return float(str(x).replace(',', '.'))
    except (TypeError, ValueError): return None

def month_of(path):
    m = re.search(r'-(\d{2})-(\d{2})-(\d{4})', path.name)
    return f'{m.group(3)}-{m.group(2)}'

def rows(path):
    ws = openpyxl.load_workbook(path, read_only=True).worksheets[0]; ws.reset_dimensions()
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i >= 8: yield list(r) + [None] * 35

a1 = []
for f in sorted((SRC / 'appendix_1').glob('*.xlsx')):
    m = month_of(f)
    for r in rows(f):
        if not (r[0] and r[2] and r[6] is not None): continue
        if str(r[27]).strip() != 'Активен' or r[28] is None: continue
        try: nn = str(int(float(r[28])))
        except ValueError: continue
        a1.append(dict(month=m, nat_no=nn, atc=str(r[0]).strip(), inn=str(r[1]).strip(),
            name=str(r[2]).strip(), strength=r[4], unit=r[5], pack=r[6], holder=r[8],
            price_wholesale_a1=num(r[11]), price_retail_a1=num(r[12]), pack_value=num(r[14]),
            level=str(r[15]).strip(), nhif_amount=num(r[16]), icd=str(r[20] or ''), file=f.name))
a1 = pd.DataFrame(a1).drop_duplicates(['month', 'nat_no', 'icd'], keep='last')
a4 = []
for f in sorted((SRC / 'appendix_4').glob('*.xlsx')):
    m = month_of(f)
    for r in rows(f):
        if str(r[24]).strip() != 'Активен' or r[25] is None: continue
        try: nn = str(int(float(r[25])))
        except ValueError: continue
        a4.append(dict(month=m, nat_no=nn, max_retail=num(r[17])))
a4 = pd.DataFrame(a4).drop_duplicates(['month', 'nat_no'], keep='last')
p = a1.merge(a4, on=['month', 'nat_no'], how='left')
p['price_a1'] = p.price_retail_a1.fillna(p.price_wholesale_a1)
p.to_csv(OUT / 'pdl_panel_all.csv', index=False, encoding='utf-8')
print('rows', len(p), 'products', p.nat_no.nunique(), 'months', p.month.nunique(), file=sys.stderr)
