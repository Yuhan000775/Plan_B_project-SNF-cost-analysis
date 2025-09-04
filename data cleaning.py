#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data cleaning

@author: yuhanxu
"""

import os, re, glob
import pandas as pd
import numpy as np

# =========================================
# path
# =========================================
folder_path = "/Users/yuhanxu/Desktop/Skilled Nursing Facility Cost Report/"
input_pattern = os.path.join(folder_path, "SNF_CostReport_*.csv")

# =========================================
# Utility function: Column name standardization mapping
# =========================================
def normalize_col(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r'[\s_]+', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', '', s)  # remove punctuation
    s = re.sub(r'\s+', ' ', s)
    return s

def build_colmap(cols):
    m = {}
    for c in cols:
        k = normalize_col(c)
        if k not in m:
            m[k] = c
    return m

# =========================================
# target（15 variables + Year）
# =========================================
vars_to_keep_target = [
    'Provider CCN',
    'Rural versus Urban',
    'SNF Admissions Total',
    'SNF Days Total',
    'SNF Number of Beds',
    'Total Charges',
    'Total Costs',
    'Total Salaries (adjusted)',
    'Accounts Receivable',
    'Wage-related Costs (core)',
    'Prepaid expenses',
    'Total Assets',
    "Less Contractual Allowance and discounts on patients' accounts",
    'Net Income from service to patients',
    'Net Income',
    'Allowable Bad Debts'
]

# Second cleaning：Redundant/Identifying fields
vars_to_drop_second = [
    'rpt_rec_num', 'Facility Name', 'Street Address', 'City', 'State Code', 'Zip Code', 'County',
    'Medicare CBSA Number', 'Fiscal Year Begin Date', 'Fiscal Year End Date', 'Type of Control',
    'Total Days Title V', 'Total Days Title XVIII', 'Total Days Title XIX', 'Total Days Other', 'Total Days Total',
    'Number of Beds', 'Total Bed Days Available', 'Total Discharges Title V', 'Total Discharges Title XVIII',
    'Total Discharges Title XIX', 'Total Discharges Title Other', 'Total Discharges Total',
    'SNF Average Length of Stay Title V', 'SNF Average Length of Stay Title XVIII',
    'SNF Average Length of Stay Title XIX', 'SNF Average Length of Stay Total',
    'SNF Admissions Title V', 'SNF Admissions Title XVIII', 'SNF Admissions Title XIX', 'SNF Admissions Other',
    'SNF Days Title V', 'SNF Days Title XVIII', 'SNF Days Title XIX', 'SNF Days Other', 'SNF Bed Days Available',
    'SNF Discharges Title V', 'SNF Discharges Title XVIII', 'SNF Discharges Title XIX', 'SNF Discharges Title Other',
    'SNF Discharges Total',
    'NF Number of Beds', 'NF Bed Days Available', 'NF Days Title V', 'NF Days Title XIX', 'NF Days Other', 'NF Days Total',
    'NF Discharges Title V', 'NF Discharges Title XIX', 'NF Discharges Title Other', 'NF Discharges Total',
    'NF Average Length of Stay Title V', 'NF Average Length of Stay Title XIX', 'NF Average Length of Stay Total',
    'NF Admissions Title V', 'NF Admissions Title XIX', 'NF Admissions Other', 'NF Admissions Total',
    'Total RUG Days', 'Total Salaries From Worksheet A', 'Overhead Non-Salary Costs', 'Contract Labor',
    'Cash on hand and in banks', 'Temporary Investments', 'Notes Receivable',
    'Less: Allowances for uncollectible notes and accounts receivable', 'Inventory', 'Other current assets',
    'Total Current Assets', 'Land', 'Land improvements', 'Buildings', 'Leasehold improvements', 'Fixed equipment',
    'Major movable equipment', 'Minor equipment depreciable', 'Total fixed Assets', 'Investments', 'Other Assets',
    'Total other Assets', 'Accounts payable', 'Salaries, wages, and fees payable', 'Payroll taxes payable',
    'Notes and Loans Payable (short term)', 'Deferred income', 'Other current liabilities', 'Total current liabilities',
    'Mortgage payable', 'Notes Payable', 'Unsecured Loans', 'Other long term liabilities', 'Total long term liabilities',
    'Total liabilities', 'General fund balance', 'Total fund balances', 'Total Liabilities and fund balances',
    'Total General Inpatient Care Services Revenue', 'Inpatient Revenue', 'Outpatient Revenue', 'Gross Revenue',
    'Net Patient Revenue', 'Less Total Operating Expense', 'Total Other Income', 'Total Income', 'Inpatient PPS Amount',
    'Nursing and Allied Health Education Activities'
]

MISSING_THRESHOLD = 0.30
type_of_control_key = normalize_col('Type of Control')
drop_norm_set = set(normalize_col(v) for v in vars_to_drop_second)
target_norms = [normalize_col(v) for v in vars_to_keep_target]

# =========================================
# process year
# =========================================
year_pattern = re.compile(r'SNF_CostReport_(\d{4})\.csv')
files = sorted(glob.glob(input_pattern))

per_year_frames = []
log_rows = []

for f in files:
    m = year_pattern.search(os.path.basename(f))
    if not m:
        continue
    year = int(m.group(1))

    df = pd.read_csv(f)
    original_cols = df.columns.tolist()
    colmap = build_colmap(original_cols)

    # Year 列（从文件名）
    df['Year'] = year

    # 3.2.1 First Cleaning：删除缺失≥30%的变量
    high_missing_cols = df.columns[df.isna().mean() >= MISSING_THRESHOLD].tolist()

    # 3.2.2 Second Cleaning：proprietary facilities（3/4/5/6）；and delete coloumn from the list above
    toc_col = colmap.get(type_of_control_key, None)
    if toc_col in df.columns:
        toc_numeric = pd.to_numeric(df[toc_col], errors='coerce')
        mask = toc_numeric.isin([3,4,5,6])
        if mask.sum() == 0:
            mask = df[toc_col].astype(str).str.strip().isin(['3','4','5','6'])
        df = df[mask].copy()

    cols_to_drop_second = [colmap[k] for k in list(drop_norm_set) if k in colmap and colmap[k] in df.columns]

    drop_all = set(high_missing_cols) | set(cols_to_drop_second)
    cols_to_drop_final = [c for c in drop_all if c in df.columns and c != 'Year']
    df = df.drop(columns=cols_to_drop_final, errors='ignore')

    # 3.2.3 Final Cleaning：only left target variables + Year，delete the observations that are missing
    keep_actual = []
    missing_targets = []
    for tnorm, tname in zip(target_norms, vars_to_keep_target):
        if tnorm in colmap and colmap[tnorm] in df.columns:
            keep_actual.append(colmap[tnorm])
        else:
            # substring matching
            found = None
            for nk, orig in colmap.items():
                if tnorm == nk and orig in df.columns:
                    found = orig; break
            if found is None:
                for nk, orig in colmap.items():
                    if tnorm in nk and orig in df.columns:
                        found = orig; break
            if found is not None:
                keep_actual.append(found)
            else:
                missing_targets.append(tname)

    keep_cols = ['Year'] + [c for c in keep_actual if c != 'Year']
    keep_cols = [c for c in keep_cols if c in df.columns]

    df_final = df[keep_cols].dropna(axis=0, how='any').copy()

    # record log
    log_rows.append({
        'year': year,
        'n_rows_original': len(pd.read_csv(f)),
        'n_rows_after_filter': len(df),
        'n_rows_final': len(df_final),
        'n_cols_original': len(original_cols),
        'n_cols_after_drop': df.shape[1],
        'kept_columns_count': len(keep_cols),
        'missing_target_vars_count': len(missing_targets),
        'missing_target_vars': '; '.join(missing_targets) if missing_targets else '',
    })

    # Save for aligning the columns later
    df_final['__year_src'] = year
    per_year_frames.append(df_final)

# =========================================
# combine and spilit（2012–2019）和（2020–2021）
# =========================================
if not per_year_frames:
    raise SystemExit("cannot find SNF_CostReport_*.csv under folder_path")

# Align Column : Take the intersection to ensure the consistency of the training/test columns
col_intersection = set(per_year_frames[0].columns)
for frame in per_year_frames[1:]:
    col_intersection &= set(frame.columns)
common_cols = sorted([c for c in col_intersection if c != '__year_src'])

aligned = [df[common_cols].copy() for df in per_year_frames]
df_all = pd.concat(aligned, ignore_index=True)

train_df = df_all[(df_all['Year'] >= 2012) & (df_all['Year'] <= 2019)].copy()
test_df  = df_all[(df_all['Year'] >= 2020) & (df_all['Year'] <= 2021)].copy()

# output
out_train = os.path.join(folder_path, "Final_SNF_CostReport_Cleaned_2012_2019.csv")
out_test  = os.path.join(folder_path, "Final_SNF_CostReport_Cleaned_2020_2021.csv")
train_df.to_csv(out_train, index=False)
test_df.to_csv(out_test, index=False)

# clean log
log_df = pd.DataFrame(log_rows).sort_values('year')
log_path = os.path.join(folder_path, "SNF_cleaning_log.csv")
log_df.to_csv(log_path, index=False)

print("Done.")
print("Train (2012–2019):", train_df.shape, "->", out_train)
print("Test  (2020–2021):", test_df.shape,  "->", out_test)
print("Log:", log_path)













