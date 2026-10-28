"""Economic burden of reimbursed outpatient cardiovascular pharmacotherapy and treated prevalence, Bulgaria 2021-2025.
Inputs: NHIF Tables 1, 3, 4 (raw extract), PDL co-payment estimates (patient_copay.py), Eurostat population and HICP."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, str(Path(__file__).parent))
from inputs_external import NUTS3_POP_2024, RZOK_NUTS3, HICP, EUR
RAW, OUT = Path(sys.argv[1]), Path(sys.argv[2])
ICD_LOOKUP, POP = sys.argv[3], sys.argv[4]
OUT.mkdir(exist_ok=True)
ANNEX1_UNIQUE = {2024: 1.11e6, 2025: 1.15e6}   # unique insured persons per month on any Annex 1 medicine (NHIF)

GROUP_EN = {'Hypertensive diseases': 'Hypertensive diseases (I10–I13)', 'Ischaemic heart diseases': 'Ischaemic heart disease (I20, I25)',
            'Pulmonary heart disease and pulmonary circulation': 'Pulmonary embolism and pulmonary hypertension (I26–I27)',
            'Other forms of heart disease': 'Arrhythmias and heart failure (I44–I50)', 'Cerebrovascular diseases': 'Sequelae of cerebrovascular disease (I69)',
            'Diseases of arteries, arterioles and capillaries': 'Arterial disease (I73–I74)', 'Diseases of veins, lymphatic vessels and nodes': 'Venous thromboembolism (I80)'}
lk = pd.read_csv(ICD_LOOKUP)
grp = dict(zip(lk.icd_code, lk.proposed_clinical_group.map(GROUP_EN)))
pop = pd.read_csv(POP, index_col=0)['TOTAL'].to_dict()

t3 = pd.read_csv(RAW / 'nhif_table_3_cvd_2021_2025.csv'); t3.columns = ['file','month','icd','icd_name','persons','reimb']
t3['year'] = t3.month.str[:4].astype(int); t3['group'] = t3.icd.map(grp)
assert t3.group.notna().all()
t1c = pd.read_csv(OUT / 'table1_copay_2021_2025.csv.gz'); t1c['group'] = t1c.icd.map(grp)
t1 = pd.read_csv(RAW / 'nhif_table_1_cvd_2021_2025.csv')
t1.columns = ['file','month','atc','atc_name','nhif','name','form','conc','count','icd','icd_name','persons','packs','reimb']
t1['year'] = t1.month.str[:4].astype(int)

# reconciliation Table 1 vs Table 3 reimbursement
rec = pd.DataFrame({'t1': t1.groupby('year').reimb.sum(), 't3': t3.groupby('year').reimb.sum()}); rec['ratio'] = rec.t1 / rec.t3
rec.to_csv(OUT / 'reconciliation_t1_t3.csv')

# ---------- 1. Treated prevalence (proxy) ----------
def mean_ci(x):
    x = np.asarray(x, float); m = x.mean(); h = stats.t.ppf(.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)); return m, m - h, m + h
mg = t3.groupby(['year','month','group']).persons.sum().reset_index()
rows = []
for (y, g), d in mg.groupby(['year','group']):
    m, lo, hi = mean_ci(d.persons)
    rows.append(dict(year=y, group=g, months=len(d), mean_monthly_persons=m, ci_lo=lo, ci_hi=hi, max_month=d.persons.max(),
                     patient_months=d.persons.sum(), per100=100 * m / pop[y], per100_lo=100 * lo / pop[y], per100_hi=100 * hi / pop[y],
                     period_10m_per100=100 * d.persons.sum() / 10 / pop[y], period_8m_per100=100 * d.persons.sum() / 8 / pop[y]))
prev = pd.DataFrame(rows); prev.to_csv(OUT / 'treated_prevalence_by_group.csv', index=False)
# all diagnoses: bounds on unique persons
mi = t3.groupby(['year','month']).persons.agg(['sum','max']).reset_index()
allcvd = mi.groupby('year').agg(diag_level=('sum','mean'), largest_single_dx=('max','mean')).reset_index()
gmax = mg.groupby(['year','month']).persons.max().groupby('year').mean().rename('largest_group')
allcvd = allcvd.merge(gmax, on='year')
allcvd['annex1_unique'] = allcvd.year.map(ANNEX1_UNIQUE)
allcvd['upper_unique'] = allcvd[['diag_level','annex1_unique']].min(axis=1)
allcvd['pop'] = allcvd.year.map(pop)
for c in ['diag_level','largest_group','upper_unique']: allcvd[c + '_per100'] = 100 * allcvd[c] / allcvd['pop']
allcvd.to_csv(OUT / 'treated_prevalence_all_cvd.csv', index=False)
icd_prev = t3.groupby(['year','icd','icd_name']).persons.mean().reset_index().rename(columns={'persons':'mean_monthly_persons'})
icd_prev['per100'] = 100 * icd_prev.mean_monthly_persons / icd_prev.year.map(pop); icd_prev['group'] = icd_prev.icd.map(grp)
icd_prev.to_csv(OUT / 'treated_prevalence_by_icd.csv', index=False)

# ---------- 2. Payer cost (Table 3, 2021-2025) ----------
pay = t3.groupby(['year','group']).reimb.sum().unstack()
pay['All cardiovascular diagnoses'] = pay.sum(axis=1)
pay_eur = pay / EUR
pay_eur_real = pay_eur.mul(pd.Series({y: HICP[2025] / HICP[y] for y in pay.index}), axis=0)
pay_eur.to_csv(OUT / 'payer_cost_eur_nominal.csv'); pay_eur_real.to_csv(OUT / 'payer_cost_eur_2025prices.csv')

# ---------- 3. Patient co-payment (Table 1 + PDL, 2021-2025) ----------
scen = {'base': 'copay', 'pdl_nhif_amount': 'copay_pdl'}
t1c['dev'] = (t1c.pdl_nhif - t1c.nhif_per_pack).abs() / t1c.nhif_per_pack
# scenario: replace poorly matched rows (PDL NHIF amount >20 % off observed) by the ATC-level co-payment ratio
good = t1c.dev.le(.2) | t1c.dev.isna()
ratio = (t1c[good].groupby(['year', t1c.atc.str[:5]]).copay.sum() / t1c[good].groupby(['year', t1c.atc.str[:5]]).reimb.sum()).rename('r').reset_index()
tmp = t1c[['year']].assign(atc5=t1c.atc.str[:5]).merge(ratio.rename(columns={'atc':'atc5'}), on=['year','atc5'], how='left')
t1c['copay_goodmatch'] = np.where(good, t1c.copay, tmp.r.values * t1c.reimb)
# scenario: 2025 prices carried forward from Dec 2024 / taken from Jan 2026
for nm, col in [('copay_2025_dec24', 'price_dec24'), ('copay_2025_jan26', 'price_jan26')]:
    alt = (t1c[col] - t1c.nhif_per_pack).clip(lower=0) * t1c.packs
    t1c[nm] = np.where(t1c.year == 2025, alt.fillna(t1c.copay), t1c.copay)
scen.update({'goodmatch_only': 'copay_goodmatch', 'prices_2025_dec2024': 'copay_2025_dec24', 'prices_2025_jan2026': 'copay_2025_jan26'})
sc = pd.DataFrame({k: t1c.groupby('year')[v].sum() for k, v in scen.items()}) / EUR
sc.to_csv(OUT / 'copay_scenarios_eur.csv')
copay_g = t1c.groupby(['year','group']).copay.sum().unstack(); copay_g['All cardiovascular diagnoses'] = copay_g.sum(axis=1)
(copay_g / EUR).to_csv(OUT / 'patient_cost_eur_nominal.csv')
# 2024 Annex 4 maximum retail price scenario (2024 only)
mr = t1c[t1c.year == 2024]; cov = mr.copay_maxretail.notna()
sc24 = dict(base=mr.copay.sum() / EUR, max_retail_rows_covered_share=mr[cov].reimb.sum() / mr.reimb.sum(),
            base_on_covered=mr[cov].copay.sum() / EUR, max_retail_on_covered=mr[cov].copay_maxretail.sum() / EUR)
pd.Series(sc24).to_csv(OUT / 'copay_2024_max_retail_check.csv')

# ---------- 4. Combined cost and cost per treated person ----------
rows = []
for y in range(2021, 2026):
    for g in list(GROUP_EN.values()) + ['All cardiovascular diagnoses']:
        P = pay.loc[y, g] / EUR; C = copay_g.loc[y, g] / EUR
        if g == 'All cardiovascular diagnoses':
            persons = allcvd.set_index('year').loc[y, 'diag_level']
        else:
            persons = prev.set_index(['year','group']).loc[(y, g), 'mean_monthly_persons']
        rows.append(dict(year=y, group=g, payer_eur=P, patient_eur=C, total_eur=P + C, patient_share=C / (P + C),
                         treated_persons=persons, payer_per_person=P / persons, patient_per_person=C / persons, total_per_person=(P + C) / persons))
cost = pd.DataFrame(rows); cost.to_csv(OUT / 'cost_by_group.csv', index=False)

# ---------- 5. Medicines driving cost (2025) ----------
inn = t1c[t1c.year == 2025].groupby(['atc_name']).agg(payer=('reimb','sum'), patient=('copay','sum'), packs=('packs','sum')).div([EUR, EUR, 1])
inn['total'] = inn.payer + inn.patient; inn['patient_share'] = inn.patient / inn.total
inn = inn.sort_values('total', ascending=False); inn.to_csv(OUT / 'cost_by_inn_2025.csv')
atc3 = t1c.assign(atc4=t1c.atc.str[:4]).groupby(['year','atc4']).agg(payer=('reimb','sum'), patient=('copay','sum')).div(EUR)
atc3.to_csv(OUT / 'cost_by_atc4.csv')
# co-payment above the reference: packs with zero co-payment
zero = t1c.groupby('year').apply(lambda d: d[d.copay_pack.fillna(1) < 0.01].packs.sum() / d.packs.sum(), include_groups=False)
zero.to_csv(OUT / 'share_packs_zero_copay.csv')

# ---------- 6. Monthly series ----------
mon = t1c.groupby('month').agg(payer=('reimb','sum'), patient=('copay','sum')).div(EUR)
mon['persons_diag_level'] = t3.groupby('month').persons.sum().values
mon.to_csv(OUT / 'monthly_payer_patient.csv')

# ---------- 7. Regional (Table 4, 2024) ----------
t4 = pd.read_csv(RAW / 'nhif_table_4_cvd_2021_2025.csv'); t4.columns = ['file','month','rz','rz_name','icd','icd_name','persons','reimb']
t4 = t4[t4.month.str[:4] == '2024']; t4['group'] = t4.icd.map(grp); t4['nuts3'] = t4.rz.map(RZOK_NUTS3)
assert t4.month.nunique() == 12 and t4.nuts3.notna().all()
r = t4.groupby('nuts3').agg(persons=('persons','sum'), reimb=('reimb','sum'))
r['hyp_persons'] = t4[t4.group.str.startswith('Hypertensive')].groupby('nuts3').persons.sum()
r['af_hf_persons'] = t4[t4.group.str.startswith('Arrhythmias')].groupby('nuts3').persons.sum()
r['region'] = [NUTS3_POP_2024[k][0] for k in r.index]; r['pop'] = [NUTS3_POP_2024[k][1] for k in r.index]
r['pop65'] = [NUTS3_POP_2024[k][2] for k in r.index]; r['share65'] = r.pop65 / r['pop']
r['diag_level_per100'] = 100 * r.persons / 12 / r['pop']; r['hyp_per100'] = 100 * r.hyp_persons / 12 / r['pop']
r['af_hf_per100'] = 100 * r.af_hf_persons / 12 / r['pop']; r['payer_eur_per_capita'] = r.reimb / EUR / r['pop']
import statsmodels.api as sm
X = sm.add_constant(r.share65 * 100)
fits = {}
for yv in ['hyp_per100', 'diag_level_per100', 'payer_eur_per_capita']:
    f = sm.WLS(r[yv], X, weights=r['pop']).fit(); fits[yv] = f
    r[yv + '_resid'] = r[yv] - f.predict(X)
    r[yv + '_ageadj'] = r[yv] - f.params.iloc[1] * (100 * r.share65 - 100 * r.pop65.sum() / r['pop'].sum())
r.to_csv(OUT / 'regional_2024.csv')
with open(OUT / 'regional_regressions.txt', 'w') as fh:
    for k, f in fits.items():
        fh.write(f'{k}: slope per pp 65+ = {f.params.iloc[1]:.4f} (95% CI {f.conf_int().iloc[1,0]:.4f} to {f.conf_int().iloc[1,1]:.4f}), R2 = {f.rsquared:.3f}\n')
print(rec.round(4)); print(prev[prev.year == 2025].round(2).to_string()); print(allcvd.round(3).to_string())
print((pay_eur / 1e6).round(1)); print((copay_g / EUR / 1e6).round(1)); print(sc.div(1e6).round(1))
print(cost[cost.year == 2025].round(2).to_string()); print(inn.head(12).div([1e6,1e6,1e6,1e6,1]).round(2).to_string())
print(zero.round(3)); print(r[['region','share65','diag_level_per100','hyp_per100','af_hf_per100','payer_eur_per_capita']].sort_values('hyp_per100').round(2).to_string())
print(open(OUT / 'regional_regressions.txt').read()); print(pd.Series(sc24).round(3))
