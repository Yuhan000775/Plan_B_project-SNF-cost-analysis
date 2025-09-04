import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------
# 0) Read and merge the two cleaned files
# ---------------------------
p1 = r"/Users/yuhanxu/Desktop/Skilled Nursing Facility Cost Report/Final_SNF_CostReport_Cleaned_2012_2019.csv"
p2 = r"/Users/yuhanxu/Desktop/Skilled Nursing Facility Cost Report/Final_SNF_CostReport_Cleaned_2020_2021.csv"

df = pd.concat([pd.read_csv(p1), pd.read_csv(p2)], ignore_index=True)

# ---------------------------
# Define variables to keep (exclude 'Provider CCN')
# ---------------------------
all_vars = [
    "Rural versus Urban",
    "SNF Admissions Total",
    "SNF Days Total",
    "SNF Number of Beds",
    "Total Charges",
    "Total Costs",
    "Total Salaries (adjusted)",
    "Accounts Receivable",
    "Wage-related Costs (core)",
    "Prepaid Expenses",
    "Total Assets",
    "Less Contractual Allowance and Discounts on Patients' Accounts",
    "Net Income from Service to Patients",
    "Net Income",
]

assert "Year" in df.columns, "Column 'Year' is required but not found."

# ---------------------------
# 1) Boxplot: Net Income by Rural vs Urban
# ---------------------------
plt.figure(figsize=(7,5))
# Drop rows with missing group or target
tmp = df[["Rural versus Urban", "Net Income"]].dropna()
sns.boxplot(x="Rural versus Urban", y="Net Income", data=tmp)
plt.title("Net Income by Rural vs Urban")
plt.xlabel("Rural vs Urban (U/R)")
plt.ylabel("Net Income")
plt.tight_layout()
plt.show()

# ---------------------------
# 2) Correlation Heatmap (exclude Provider CCN)
# ---------------------------
plt.figure(figsize=(12,10))
corr = df.drop(columns=["Year","Rural versus Urban","Provider CCN"]).corr()
sns.heatmap(corr, annot=False, cmap="coolwarm", center=0)
plt.title("Correlation Heatmap of Variables")
plt.show()

# ---------------------------
# 3) Pairwise: Net Income vs Top-5 correlated variables (matplotlib subplots)
# ---------------------------
# Compute absolute correlation with "Net Income" and pick top-5 (excluding itself)
target = "Net Income"
corr_to_target = corr[target].drop(labels=[target]).abs().sort_values(ascending=False)
top5 = corr_to_target.head(5).index.tolist()
print("Top-5 variables most correlated with Net Income:", top5)

fig, axes = plt.subplots(2, 3, figsize=(15,10))
axes = axes.flatten()

for i, var in enumerate(top5):
    # Scatter plot with alpha for readability
    axes[i].plot(df[var], df[target], 'o', alpha=0.4, markersize=4)
    axes[i].set_xlabel(var)
    axes[i].set_ylabel(target)
    axes[i].set_title(f"{target} vs {var}")

# Remove any unused subplot (if fewer than 5 found)
for j in range(len(top5), len(axes)):
    fig.delaxes(axes[j])

fig.suptitle("Net Income and Top-5 Correlated Variables", fontsize=14)
plt.tight_layout()
plt.show()

# ---------------------------
# 4) Yearly line plots for ALL variables (pre- vs during-COVID)
#    Groups: Operational // Revenue & Cost // Asset & Liability // Profitability
# ---------------------------
groups = {
    "Operational Variables over Time": [
        "SNF Admissions Total",
        "SNF Days Total",
        "SNF Number of Beds",
    ],
    "Revenue and Cost Variables over Time": [
        "Total Charges",
        "Total Costs",
        "Total Salaries (adjusted)",
        "Wage-related Costs (core)",
        "Less Contractual Allowance and Discounts on Patients' Accounts",
    ],
    "Asset and Liability Variables over Time": [
        "Accounts Receivable",
        "Prepaid Expenses",
        "Total Assets",
    ],
    "Profitability Outcomes over Time": [
        "Net Income from Service to Patients",
        "Net Income",
    ],
}

def plot_group_lines(df, group_title, columns):
    """Plot yearly means for a list of columns on a single figure."""
    plt.figure(figsize=(10,6))
    for col in columns:
        if col in df.columns:
            df.groupby("Year")[col].mean().plot(marker="o", label=col)
    # Mark the start of COVID period
    plt.axvline(x=2020, color="tab:blue", linestyle="--", linewidth=1.5, label="COVID start (2020)")
    plt.title(group_title)
    plt.xlabel("Year")
    plt.ylabel("Yearly Mean")
    plt.legend(loc="best", fontsize=9)
    plt.tight_layout()
    plt.show()

for title, cols in groups.items():
    plot_group_lines(df, title, cols)
