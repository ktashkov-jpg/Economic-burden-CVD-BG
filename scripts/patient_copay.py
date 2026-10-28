"""Estimate patient co-payments for NHIF Table 1 dispensings, Jan 2023-Dec 2025.
co-payment per pack = PDL price (Annex 1 price column used by the NHIF for the row) - NHIF amount actually paid per pack (Table 1).
Prices: same-month snapshot (Feb 2023-Dec 2025); Jan 2023 uses Feb 2023.
The Jan 2026 list (in EUR, converted at 1.95583) is used only as a nearest-month fallback."""
import sys
import numpy as np, pandas as pd
T1, PANEL, LINKS, OUTDIR = sys.argv[1:5]
EUR = 1.95583
t1 = pd.read_csv(T1)
t1.columns = ['file','month','atc','atc_name','nhif','name','form','conc','count','icd','icd_name','persons','packs','reimb']
t1['month'] = t1.month.str[:7]
t1 = t1[t1.month >= '2023-01'].copy()
links = pd.read_csv(LINKS)[['nhif','nat_no','tier']]
p = pd.read_csv(PANEL, dtype={'nat_no': str})
p.loc[p.month == '2026-01', ['price_a1','nhif_amount','price_wholesale_a1','price_retail_a1','max_retail']] *= EUR
p = p[p.price_a1.notna()]

# explode links to nat_no
L = links.dropna(subset=['nat_no']).assign(nat_no=lambda d: d.nat_no.str.split(';')).explode('nat_no')
pl = p.merge(L[['nhif','nat_no']], on='nat_no')   # month x nhif x nat_no x icd-list rows
pl['icds'] = pl.icd.fillna('').str.replace(' ', '').str.split(',')
icd_rows = pl.explode('icds')
icd_rows['icd3'] = icd_rows.icds.str[:3]

def snapshot(month_list):
    """price and NHIF amount per nhif x icd x snapshot month (median over matching rows),
    with an ICD-agnostic fallback per nhif x month"""
    sub = icd_rows[icd_rows.month.isin(month_list)]
    exact = sub.groupby(['month','nhif','icds']).agg(price=('price_a1','median'), pdl_nhif=('nhif_amount','median'), max_retail=('max_retail','median')).reset_index().rename(columns={'icds':'icd'})
    anyicd = pl[pl.month.isin(month_list)].groupby(['month','nhif']).agg(price_any=('price_a1','median'), pdl_nhif_any=('nhif_amount','median'), max_retail_any=('max_retail','median')).reset_index()
    return exact, anyicd

months = sorted(p.month.unique())
exact, anyicd = snapshot(months)
# nearest-month fallback per nhif: last available price before (or first after) the month
nearest = pl.groupby(['nhif','month']).price_a1.median().reset_index().sort_values('month')

def attach(df, snap_month_col):
    d = df.merge(exact.rename(columns={'month': snap_month_col}), on=[snap_month_col,'nhif','icd'], how='left')
    d = d.merge(anyicd.rename(columns={'month': snap_month_col}), on=[snap_month_col,'nhif'], how='left')
    d['price'] = d.price.fillna(d.price_any); d['pdl_nhif'] = d.pdl_nhif.fillna(d.pdl_nhif_any)
    d['max_retail'] = d.max_retail.fillna(d.max_retail_any)
    return d.drop(columns=['price_any','pdl_nhif_any','max_retail_any'])

d = t1.copy()
d['snap'] = d.month.where(d.month != '2023-01', '2023-02')
d = attach(d, 'snap')
# sensitivity: 2025 priced at the December 2024 or January 2026 list
for snap, col in [('2024-12', 'price_dec24'), ('2026-01', 'price_jan26')]:
    alt = attach(t1[['month','nhif','icd']].assign(snap=snap), 'snap').price.values
    d[col] = np.where(d.month >= '2025-01', alt, np.nan)

# nearest available price for rows still missing
d['price_source'] = np.where(d.price.notna(), 'snapshot', 'none')
miss = d.price.isna()
if miss.any():
    nn = nearest.rename(columns={'month':'pm','price_a1':'price_near'})
    tmp = d.loc[miss, ['month','nhif']].reset_index()
    tmp = pd.merge_asof(tmp.assign(_m=pd.to_datetime(tmp.month)).sort_values('_m').drop(columns='_m').assign(mm=lambda x: pd.to_datetime(x.month)), nn.sort_values('pm').assign(mm=lambda x: pd.to_datetime(x.pm)), on='mm', by='nhif', direction='nearest')
    d.loc[tmp['index'], 'price'] = tmp.price_near.values
    d.loc[tmp['index'], 'price_source'] = 'nearest_month'
d['nhif_per_pack'] = d.reimb / d.packs.replace(0, np.nan)
d['copay_pack'] = (d.price - d.nhif_per_pack).clip(lower=0)
d['copay'] = d.copay_pack * d.packs
d['copay_pdl'] = (d.price - d.pdl_nhif).clip(lower=0) * d.packs           # sensitivity: PDL NHIF amount
d['copay_maxretail'] = (d.max_retail - d.nhif_per_pack).clip(lower=0) * d.packs  # sensitivity: Annex 4 max retail (2024)
# validation: PDL NHIF amount vs observed NHIF per pack
d['nhif_match5'] = (abs(d.pdl_nhif - d.nhif_per_pack) <= 0.05 * d.nhif_per_pack)
# impute missing prices by ATC5 then ATC4 copay-to-reimbursement ratio, same year
d['year'] = d.month.str[:4].astype(int)
ok = d.price.notna()
for lvl in [7, 5, 4, 3]:
    k = d.atc.str[:lvl]
    r = (d[ok].groupby([d.year, k]).copay.sum() / d[ok].groupby([d.year, k]).reimb.sum()).rename('ratio')
    need = d.copay.isna()
    if not need.any(): break
    rr = pd.DataFrame({'year': d.loc[need,'year'], 'k': k[need]}).merge(r.reset_index().rename(columns={'atc':'k'}), on=['year','k'], how='left')
    d.loc[need, 'copay'] = (rr.ratio.values * d.loc[need, 'reimb'].values)
    d.loc[need & d.copay.notna(), 'price_source'] = f'imputed_atc{lvl}'
d.to_csv(f'{OUTDIR}/table1_copay_2023_2025.csv.gz', index=False)
v = d[d.pdl_nhif.notna()]
print('NHIF amount within 5 % of PDL, share of reimbursement by year:',
      (v[v.nhif_match5].groupby('year').reimb.sum() / v.groupby('year').reimb.sum()).round(3).to_dict(), file=sys.stderr)
print(d.groupby('price_source').reimb.sum().div(d.reimb.sum()).round(4).to_dict(), file=sys.stderr)
print((d.groupby('year')[['reimb','copay','copay_pdl']].sum() / 1e6).round(1), file=sys.stderr)
