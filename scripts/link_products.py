"""Link NHIF Table 1 products (NHIF code) to PDL Annex 1 rows (national number) by
ATC + normalised name + strength + pack size, with fallbacks. Writes the link table."""
import re, sys
import pandas as pd
T1, PANEL, OUT = sys.argv[1:4]

def norm(s): return re.sub(r'[^A-Z0-9]', '', str(s).upper())
def nums(s): return tuple(re.findall(r'\d+(?:[.,]\d+)?', str(s).replace(',', '.')))
def first_word(s):
    w = re.findall(r'[A-Za-zА-Яа-я]+', str(s)); return w[0].upper() if w else ''
def packn(s):
    m = re.search(r'(\d+)', str(s)); return int(m.group(1)) if m else None

t1 = pd.read_csv(T1)
t1.columns = ['file','month','atc','atc_name','nhif','name','form','conc','count','icd','icd_name','persons','packs','reimb']
prod = t1.groupby(['nhif','atc','name','conc','count'], dropna=False).agg(packs=('packs','sum'), reimb=('reimb','sum')).reset_index()
p = pd.read_csv(PANEL, dtype={'nat_no': str})
pp = p.drop_duplicates('nat_no', keep='last')[['nat_no','atc','name','strength','unit','pack']].copy()
for d, nm, st, pk in [(prod,'name','conc','count'), (pp,'name','strength','pack')]:
    d['k_name'] = d[nm].map(norm); d['k_fw'] = d[nm].map(first_word)
    d['k_str'] = d[st].map(nums); d['k_pack'] = d[pk].map(packn)
# names in PDL sometimes embed strength ("Trifas 10"); strip trailing digits for the name key
for d in (prod, pp): d['k_name2'] = d.k_name.str.replace(r'\d+$', '', regex=True)
tiers = [('t1_name_str_pack', ['atc','k_name','k_str','k_pack']),
         ('t2_name2_str_pack', ['atc','k_name2','k_str','k_pack']),
         ('t3_firstword_str_pack', ['atc','k_fw','k_str','k_pack']),
         ('t4_firstword_pack', ['atc','k_fw','k_pack']),
         ('t5_atc_str_pack', ['atc','k_str','k_pack'])]
links = []; left = prod.copy()
for tier, keys in tiers:
    m = left.merge(pp[keys + ['nat_no']], on=keys, how='inner')
    m = m.groupby('nhif').nat_no.apply(lambda s: ';'.join(sorted(set(s)))).reset_index()
    m['tier'] = tier; links.append(m)
    left = left[~left.nhif.isin(m.nhif)]
links = pd.concat(links)
out = prod.merge(links, on='nhif', how='left')
out['tier'] = out.tier.fillna('unlinked')
out.drop(columns=[c for c in out if c.startswith('k_')]).to_csv(OUT, index=False)
s = out.groupby('tier').agg(n=('nhif','size'), reimb=('reimb','sum'), packs=('packs','sum'))
s['reimb_share'] = s.reimb / s.reimb.sum(); s['pack_share'] = s.packs / s.packs.sum()
print(s.round(4).to_string(), file=sys.stderr)
