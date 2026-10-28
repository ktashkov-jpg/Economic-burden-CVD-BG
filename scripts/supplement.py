"""Supplementary appendix tables (markdown) from out/."""
import sys
import pandas as pd
O = sys.argv[1]; LK = sys.argv[2]
EUR = 1.95583
f0 = lambda x: f"{x:,.0f}".replace(',', ' ')
L = ['# Supplementary Appendix (for web publication)', '',
     '**Who Pays for Cardiovascular Pharmacotherapy in Bulgaria? Payer and Patient Costs and Treated Prevalence From National Claims Data, 2021–2025**', '']
rec = pd.read_csv(f'{O}/reconciliation_t1_t3.csv')
L += ['## Supplementary Table S1. NHIF reimbursement in Report 1 (product level) and Report 3 (diagnosis level), EUR million', '',
      '| Year | Report 1 | Report 3 | Ratio |', '|---|---|---|---|']
L += [f"| {r.year} | {r.t1/EUR/1e6:.2f} | {r.t3/EUR/1e6:.2f} | {r.ratio:.4f} |" for r in rec.itertuples()] + ['']
lk = pd.read_csv(LK)
GROUP_EN = {'Hypertensive diseases': 'Hypertensive diseases', 'Ischaemic heart diseases': 'Ischaemic heart disease',
            'Pulmonary heart disease and pulmonary circulation': 'Pulmonary embolism and pulmonary hypertension',
            'Other forms of heart disease': 'Arrhythmias and heart failure', 'Cerebrovascular diseases': 'Sequelae of cerebrovascular disease',
            'Diseases of arteries, arterioles and capillaries': 'Arterial disease', 'Diseases of veins, lymphatic vessels and nodes': 'Venous thromboembolism'}
ip = pd.read_csv(f'{O}/treated_prevalence_by_icd.csv'); ip = ip[ip.year == 2025].set_index('icd')
L += ['## Supplementary Table S2. ICD-10 codes observed and disease groups, with treated persons per month in 2025', '',
      '| ICD-10 | Disease group | Treated persons per month, 2025 | Per 100 population |', '|---|---|---|---|']
for r in lk.itertuples():
    pm = ip.mean_monthly_persons.get(r.icd_code); pc = ip.per100.get(r.icd_code)
    L.append(f"| {r.icd_code} | {GROUP_EN[r.proposed_clinical_group]} | {f0(pm) if pm == pm and pm is not None else '–'} | {pc:.3f} |" if pm is not None else f"| {r.icd_code} | {GROUP_EN[r.proposed_clinical_group]} | – | – |")
L += ['', 'ICD-10 code names follow the NHIF reports (Bulgarian). I25.5 is the only I25 code observed in the extract.', '']
lnk = pd.read_csv(f'{O}/product_links.csv')
s = lnk.groupby('tier').agg(n=('nhif', 'size'), reimb=('reimb', 'sum'), packs=('packs', 'sum'))
s['rs'] = 100 * s.reimb / s.reimb.sum(); s['ps'] = 100 * s.packs / s.packs.sum()
names = {'t1_name_str_pack': 'ATC + trade name + strength + pack size', 't2_name2_str_pack': 'ATC + trade name without trailing digits + strength + pack size',
         't3_firstword_str_pack': 'ATC + first word of trade name + strength + pack size', 't4_firstword_pack': 'ATC + first word of trade name + pack size',
         't5_atc_str_pack': 'ATC + strength + pack size', 'unlinked': 'Not linked (ATC-group ratio applied)'}
L += ['## Supplementary Table S3. Linkage of NHIF product codes to Positive Drug List entries, 2021–2025', '',
      '| Linkage step | NHIF products | % of reimbursement | % of packages |', '|---|---|---|---|']
L += [f"| {names[t]} | {int(r.n)} | {r.rs:.1f} | {r.ps:.1f} |" for t, r in s.iterrows()] + ['']
L += ['Co-payments were estimated for 2023–2025. Price source by share of 2023–2025 reimbursement: same-month list 99.4 %, nearest available month 0.2 %, ATC-group imputation 0.4 %.', '']
ip2 = pd.read_csv(f'{O}/treated_prevalence_by_icd.csv'); top = ip2[ip2.year == 2025].sort_values('mean_monthly_persons', ascending=False).head(12)
L += ['## Supplementary Table S4. The 12 most frequent diagnoses, treated persons per month, 2021 and 2025', '',
      '| ICD-10 | 2021 | 2025 | Per 100 population, 2025 |', '|---|---|---|---|']
for r in top.itertuples():
    p21 = ip2[(ip2.year == 2021) & (ip2.icd == r.icd)].mean_monthly_persons
    L.append(f"| {r.icd} | {f0(p21.iloc[0]) if len(p21) else '–'} | {f0(r.mean_monthly_persons)} | {r.per100:.2f} |")
L += ['']
pn = pd.read_csv(f'{O}/payer_cost_eur_nominal.csv', index_col=0); pr = pd.read_csv(f'{O}/payer_cost_eur_2025prices.csv', index_col=0)
L += ['## Supplementary Table S5. NHIF reimbursement by disease group, 2021–2025, EUR million (nominal; 2025 prices in brackets)', '',
      '| Disease group | ' + ' | '.join(str(y) for y in pn.index) + ' |', '|---' * (len(pn.index) + 1) + '|']
for g in pn.columns:
    L.append(f"| {g} | " + ' | '.join(f"{pn.loc[y, g]/1e6:.1f} ({pr.loc[y, g]/1e6:.1f})" for y in pn.index) + ' |')
L += ['', 'Deflated with the Bulgarian all-items HICP (annual average, 2015 = 100: 2021 109.30; 2022 123.52; 2023 134.15; 2024 137.63; 2025 142.50).', '']
pc = pd.read_csv(f'{O}/patient_cost_eur_nominal.csv', index_col=0)
L += ['Patient co-payments by disease group, EUR million (nominal):', '', '| Disease group | ' + ' | '.join(str(y) for y in pc.index) + ' |', '|---' * (len(pc.index) + 1) + '|']
for g in pc.columns:
    L.append(f"| {g} | " + ' | '.join(f"{pc.loc[y, g]/1e6:.1f}" for y in pc.index) + ' |')
L += ['']
r = pd.read_csv(f'{O}/regional_2024.csv').sort_values('hyp_per100')
L += ['## Supplementary Table S6. Treated prevalence and NHIF cost per capita by region (NUTS-3), 2024', '',
      '| Region | Population | Aged 65+, % | All diagnoses, diagnosis-level per 100 | Hypertensive diseases per 100 | Age-adjusted hypertensive per 100 | Arrhythmias and heart failure per 100 | NHIF, EUR per capita |',
      '|---|---|---|---|---|---|---|---|']
for x in r.itertuples():
    L.append(f"| {x.region} | {f0(x.pop)} | {100*x.share65:.1f} | {x.diag_level_per100:.1f} | {x.hyp_per100:.1f} | {x.hyp_per100_ageadj:.1f} | {x.af_hf_per100:.1f} | {x.payer_eur_per_capita:.1f} |")
import re
reg = open(f'{O}/regional_regressions.txt').read()
nm = {'hyp_per100': 'Hypertensive diseases per 100', 'diag_level_per100': 'All diagnoses (diagnosis-level) per 100', 'payer_eur_per_capita': 'NHIF EUR per capita'}
L += ['', 'Population-weighted least squares on the percentage of population aged 65 or over (28 regions):', '']
for line in reg.strip().split('\n'):
    k, rest = line.split(': ', 1)
    m = re.search(r'= ([-\d.]+) \(95% CI ([-\d.]+) to ([-\d.]+)\), R2 = ([\d.]+)', rest)
    L.append(f"- {nm[k]}: slope {float(m.group(1)):.2f} per percentage point (95 % CI {float(m.group(2)):.2f} to {float(m.group(3)):.2f}); R² = {float(m.group(4)):.2f}")
L += ['', 'Age-adjusted value: observed value minus slope × (regional − national percentage aged 65 or over).', '']
sc = pd.read_csv(f'{O}/copay_scenarios_eur.csv', index_col=0) / 1e6
lab = {'base': 'Base case', 'pdl_nhif_amount': '(a) PDL NHIF amount instead of observed amount', 'goodmatch_only': '(b) Poorly matched rows replaced by ATC-group ratio',
       'prices_2025_dec2024': '(c) 2025 priced at the December 2024 list', 'prices_2025_jan2026': '(d) 2025 priced at the January 2026 list'}
L += ['## Supplementary Table S7. Sensitivity analyses: patient co-payments, EUR million', '', '| Scenario | 2023 | 2024 | 2025 | 2025 change vs base, % |', '|---|---|---|---|---|']
for k in sc.columns:
    L.append(f"| {lab[k]} | {sc.loc[2023, k]:.1f} | {sc.loc[2024, k]:.1f} | {sc.loc[2025, k]:.1f} | {100*(sc.loc[2025, k]/sc.loc[2025, 'base']-1):+.1f} |")
m = pd.read_csv(f'{O}/copay_2024_max_retail_check.csv', index_col=0).iloc[:, 0]
L += [f"| (e) 2024 priced at the Annex 4 maximum retail price ({100*m['max_retail_rows_covered_share']:.1f} % of 2024 reimbursement covered) | – | {m['max_retail_on_covered']/1e6:.1f} vs {m['base_on_covered']/1e6:.1f} | – | {100*(m['max_retail_on_covered']/m['base_on_covered']-1):+.1f} (2024) |", '']
pv = pd.read_csv(f'{O}/treated_prevalence_by_group.csv'); pv = pv[pv.year == 2025]
L += ['Treated prevalence scenarios, 2025, per 100 population (mean monthly; annual if 10 treated months per person; annual if 8):', '',
      '| Disease group | Mean monthly | 10 months | 8 months |', '|---|---|---|---|']
L += [f"| {x.group} | {x.per100:.2f} | {x.period_10m_per100:.2f} | {x.period_8m_per100:.2f} |" for x in pv.itertuples()] + ['']
open(sys.argv[3], 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
