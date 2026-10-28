"""Monthly Positive Drug List (Annex 1) panel for all ATC groups, plus Annex 4 maximum prices.
One row per snapshot month x national number x ICD list (active rows only).
The column layout of both annexes changed several times between 2021 and 2025 (24, 25, 30 or 31 columns in
Annex 1; 24, 25, 27 or 30 in Annex 4), so columns are located by their header text (row 7, sub-headers in row 8).
Files up to January 2022 are .xls, later files .xlsx."""
import re, sys, warnings
from pathlib import Path
import pandas as pd
warnings.filterwarnings('ignore')
SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2])

def num(x):
    try: return float(str(x).replace(',', '.'))
    except (TypeError, ValueError): return None

def month_of(path):
    m = re.search(r'-(\d{2})-(\d{2})-(\d{4})', path.name)
    return f'{m.group(3)}-{m.group(2)}'

def sheet(path):
    d = pd.read_excel(path, header=None, dtype=object)
    d = d.astype(object).where(d.notna(), None)
    return d.iloc[6].map(lambda x: str(x or '').strip()).tolist(), d.iloc[7].map(lambda x: str(x or '').strip()).tolist(), d.iloc[8:].values.tolist()

def col(head, prefix, last=False):
    hits = [i for i, h in enumerate(head) if h.startswith(prefix)]
    if not hits: raise KeyError(prefix)
    return hits[-1] if last else hits[0]

def files(d):
    return sorted(d.glob('*.xls*'), key=lambda f: month_of(f) + f.name)

a1 = []
for f in files(SRC / 'appendix_1'):
    m = month_of(f); h, s, data = sheet(f)
    c = dict(atc=col(h, 'Анатомо'), inn=col(h, 'Международно'), name=col(h, 'Наименование'), strength=col(h, 'Количество'),
             pack=col(h, 'Окончателна опаковка'), holder=col(h, 'Притежател'), whole=col(s, 'Търговец на едро'),
             retail=col(s, 'Търговец на дребно'), value=col(h, 'Стойност за опаковка'), level=col(h, 'Ниво на заплащане (%)'),
             nhif=col(h, 'Ниво на заплащане (стойност)'), icd=col(h, 'МКБ'), status=col(h, 'Статус'),
             nat=next(i for i, x in enumerate(h) if x.startswith('Национален номер') or x.startswith('Идентификатор')))
    for r in data:
        if not (r[c['atc']] and r[c['name']] and r[c['pack']] is not None): continue
        if str(r[c['status']]).strip() != 'Активен' or r[c['nat']] is None: continue
        try: nn = str(int(float(r[c['nat']])))
        except ValueError: continue
        a1.append(dict(month=m, nat_no=nn, atc=str(r[c['atc']]).strip(), inn=str(r[c['inn']]).strip(),
            name=str(r[c['name']]).strip(), strength=r[c['strength']], unit=r[c['strength'] + 1], pack=r[c['pack']], holder=r[c['holder']],
            price_wholesale_a1=num(r[c['whole']]), price_retail_a1=num(r[c['retail']]), pack_value=num(r[c['value']]),
            level=str(r[c['level']]).strip(), nhif_amount=num(r[c['nhif']]), icd=str(r[c['icd']] or ''), file=f.name))
a1 = pd.DataFrame(a1).drop_duplicates(['month', 'nat_no', 'icd'], keep='last')
a4 = []
for f in files(SRC / 'appendix_4'):
    m = month_of(f); h, s, data = sheet(f)
    st, nat, retail = col(h, 'Статус'), next(i for i, x in enumerate(h) if x.startswith('Национален номер') or x.startswith('Идентификатор')), col(s, 'общо с ДДС', last=True)
    for r in data:
        if str(r[st]).strip() != 'Активен' or r[nat] is None: continue
        try: nn = str(int(float(r[nat])))
        except ValueError: continue
        a4.append(dict(month=m, nat_no=nn, max_retail=num(r[retail])))
a4 = pd.DataFrame(a4).drop_duplicates(['month', 'nat_no'], keep='last')
p = a1.merge(a4, on=['month', 'nat_no'], how='left')
p['price_a1'] = p.price_retail_a1.fillna(p.price_wholesale_a1)
p.to_csv(OUT / 'pdl_panel_all.csv', index=False, encoding='utf-8')
print('rows', len(p), 'products', p.nat_no.nunique(), 'months', p.month.nunique(), file=sys.stderr)
