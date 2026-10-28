# Economic burden of cardiovascular pharmacotherapy in Bulgaria: reproducibility bundle

Code, source data and derived outputs for:

> Tachkov K. *Who Pays for Cardiovascular Pharmacotherapy in Bulgaria? Payer and Patient Costs and Treated Prevalence From National Claims Data, 2021–2025.* Manuscript v4, 28 October 2026 (target journal: Value in Health Regional Issues).

Contact: Konstantin Tachkov, Faculty of Pharmacy, Medical University of Sofia. ktashkov@pharmfac.mu-sofia.bg, ORCID 0000-0002-3961-7556.

## Layout

```
Economic-burden-CVD-BG/
├── README.md
├── requirements.txt
├── source_data/
│   ├── nhif/                         NHIF monthly reports, cardiovascular ICD codes (I00–I99), Jan 2021–Dec 2025
│   │   ├── nhif_table_1_cvd_2021_2025.csv   product × ICD × month (282 801 rows)
│   │   ├── nhif_table_3_cvd_2021_2025.csv   ICD × month (1 963 rows)
│   │   ├── nhif_table_4_cvd_2021_2025.csv   regional fund (RZOK) × ICD × month (49 141 rows)
│   │   └── SHA256SUMS.txt
│   ├── pdl/                          Positive Drug List snapshots (NCPR)
│   │   ├── appendix_1/               Annex 1, reimbursement terms, monthly Jan 2021–Dec 2025 + Jan 2026 (61 files)
│   │   └── appendix_4/               Annex 4, maximum prices, monthly Jan 2021–Jan 2023 and Jan 2024–Dec 2025 (49 files)
│   └── reference/
│       ├── observed_icd_lookup.csv   ICD-10 codes observed in the extract and their disease group
│       ├── population_BG.csv         Eurostat demo_pjangroup, population on 1 January, Bulgaria 2020–2025
│       ├── rzok_ref.csv              NHIF regional fund (RZOK) numbering, 1–28
│       └── nsi_ekatte_ek_obl.json    NSI EKATTE oblast table with NUTS-3 codes
├── scripts/
│   ├── run_all.py                    runs the steps below in order with bundle paths
│   ├── build_price_panel_all.py      1. PDL Annex 1 (all ATC) × month panel with Annex 4 maximum retail price
│   ├── link_products.py              2. NHIF product code → PDL national number(s), five matching steps
│   ├── patient_copay.py              3. co-payment per Table 1 row = PDL price − observed NHIF amount per pack
│   ├── econ_burden.py                4. treated prevalence, payer and patient cost, cost per person, ATC drivers, regional, scenarios
│   ├── figures.py                    5. Figures 1–2
│   ├── supplement.py                 6. Supplementary Tables S1–S7 (markdown)
│   ├── inputs_external.py            Eurostat NUTS-3 population 2024 (total, 65+), RZOK → NUTS-3 map, HICP, EUR rate
│   ├── md2docx.py                    manuscript .md → journal-format .docx (pandoc + python-docx)
│   └── sql/                          extraction queries for NHIF Tables 1, 3 and 4
├── output/                           all derived tables (see below)
├── figures/                          figure1_monthly_payer_patient.png, figure2_regional_hypertension.png (300 dpi)
└── manuscript/                       submitted manuscript (v4) and supplementary appendix (v3), .md and .docx
```

## How to run

```
pip install -r requirements.txt
PYTHONIOENCODING=utf-8 python scripts/run_all.py
```

`run_all.py` locates the bundle root from its own path, reads `source_data/` only and overwrites `output/` and `figures/`. The price panel step reads 110 Excel files and takes about 8 minutes; the whole run takes about 9 minutes.

Reproducibility check (28 October 2026, after adding the 2021–2022 price lists): a clean run from this bundle reproduced every table in `output/` byte for byte, including `pdl_panel_all.csv`, `product_links.csv` and the co-payment file. Figure 1 was pixel-identical. In Figure 2 only the placement of the region labels can differ between runs (adjustText); the points and fitted line are identical. The figures in `figures/` are the ones submitted with the manuscript.

## Where each manuscript result comes from

| Manuscript | Output |
|---|---|
| Table 1, Section 3.1 (treated prevalence by group, unique-person bounds) | output/treated_prevalence_by_group.csv, treated_prevalence_all_cvd.csv |
| Supplementary Table S4 (treated prevalence by ICD code) | output/treated_prevalence_by_icd.csv |
| Table 2, Sections 3.2–3.3 (payer, patient, total and per-person cost by group) | output/cost_by_group.csv, payer_cost_eur_nominal.csv, patient_cost_eur_nominal.csv |
| Supplementary Table S5 (payer cost 2021–2025, nominal and 2025 prices) | output/payer_cost_eur_nominal.csv, payer_cost_eur_2025prices.csv |
| Table 3, Section 3.4 (ATC groups, INNs) | output/cost_by_atc4.csv, cost_by_inn_2025.csv |
| Figure 1, April 2024 change, packs without co-payment | output/monthly_payer_patient.csv, share_packs_zero_copay.csv |
| Figure 2, Section 3.5, Supplementary Table S6 (regional, 2024) | output/regional_2024.csv, regional_regressions.txt |
| Section 3.6, Supplementary Table S7 (sensitivity analyses) | output/copay_scenarios_eur.csv, copay_2024_max_retail_check.csv |
| Supplementary Tables S1–S3 (reconciliation, ICD groups, product linkage) | output/reconciliation_t1_t3.csv, product_links.csv |
| Co-payment per dispensing row (2021–2025) | output/table1_copay_2021_2025.csv.gz |

`output/supplement_tables.md` is the generated supplement; the submitted version (`manuscript/SUPPLEMENT2_v3_…`) is the same text.

## Method notes

- **Payer cost** is NHIF reimbursement from Table 3. **Patient cost** (2021–2025) is the PDL Annex 1 price of the row whose ICD list contains the dispensed diagnosis (retail price below 100 % reimbursement, wholesale-based price at 100 %) minus the NHIF amount actually paid per pack in Table 1, bounded at zero. Each month is priced with that month's list. The column layout of the annexes changed several times (2021 files are .xls), so `build_price_panel_all.py` locates columns by header text. The January 2026 list is in EUR and is converted to BGN at 1.95583; it is used only as a nearest-month fallback and in sensitivity analysis (d).
- **Validity checks.** Table 1 and Table 3 reimbursement agree exactly every year. 99.4 % of 2021–2025 reimbursement is linked to a same-month PDL price. The PDL NHIF amount is within 5 % of the observed amount for 99.1 %, 98.8 %, 98.6 %, 97.8 % and 98.1 % of reimbursement in 2021 to 2025.
- **Treated prevalence** is the mean monthly number of insured persons per disease group divided by the population on 1 January. For all diagnoses, unique persons are bounded by the largest group and by the NHIF figure for unique persons on any Annex 1 medicine (1.11 million in 2024, 1.15 million in 2025; hard-coded in econ_burden.py).
- **Regional analysis** uses Table 4 for 2024 (complete; Table 4 lacks July 2023 in this extract). RZOK numbers follow `rzok_ref.csv` (22 = Sofia City, BG411; 23 = Sofia province, BG412), and NUTS-3 codes agree with the NSI EKATTE table.
- **Units.** Source amounts are in BGN; the manuscript reports EUR at the fixed rate of 1.95583 BGN per EUR. Real terms use the Eurostat all-items HICP (annual average), in 2025 prices.

## Source data provenance

- **NHIF Tables 1, 3 and 4.** National Health Insurance Fund monthly public reports for outpatient medicines under Annex 1 of the PDL (https://nhif.bg/bg/nzok/hospital-medicine), harmonised in a PostgreSQL database and exported read-only on 17 October 2026 (extract `extract_20261017T081548Z`, one repeatable-read snapshot). Columns and values are as published. Checksums are in `SHA256SUMS.txt`.
- **PDL snapshots.** Monthly updates of Annex 1 and Annex 4 of the Positive Drug List, National Council on Prices and Reimbursement of Medicinal Products.
- **Population and prices.** Eurostat `demo_pjangroup` (national), `demo_r_pjanaggr3` (NUTS-3, 1 January 2024) and `prc_hicp_aind` (HICP), retrieved 17–27 October 2026; the NUTS-3 and HICP values are in `scripts/inputs_external.py`.
- **Regions.** NSI Unified Classification of Administrative-Territorial and Territorial Units (EKATTE), https://www.nsi.bg/nrnm/ekatte/index.

All source data are aggregate and publicly published, and contain no personal data.

## Notes

- **Large files.** `nhif_table_1_cvd_2021_2025.csv` (65 MB) and `output/pdl_panel_all.csv` are below GitHub's 100 MB file limit. Git LFS is optional.
- **Double-anonymised review.** The manuscript is under double-anonymised review. The title page and cover letter are not included here.
- **Licence.** MIT
