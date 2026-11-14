"""Builds and executes notebooks/01_data_preparation_and_eda.ipynb (outputs saved in the notebook)."""
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
cells = [
    md("# RecoMart - Data Preparation and Exploratory Data Analysis\n"
       "DSE ZG529 Experiential Learning Assignment · Member 2 (Akriti Adarsh)\n\n"
       "This notebook runs the preparation stage on the raw data lake and explores the cleaned data: "
       "interaction distributions, item popularity, sparsity and ratings."),
    code("import sys, json\nsys.path.insert(0, '../src')\nimport pandas as pd, numpy as np, matplotlib.pyplot as plt\n"
         "from recomart import preparation, eda\nfrom recomart.plotting import style, INK, GREY, RUST, OCHRE, OLIVE\n"
         "style(); pd.set_option('display.width', 140)"),
    md("## 1. Cleaning and preprocessing\nDuplicates are dropped, invalid rows are quarantined with a reason code, "
       "missing categoricals are imputed, categories are encoded and numeric columns normalised."),
    code("summary = preparation.prepare()\npd.DataFrame({k: v for k, v in summary.items() if k not in ('quarantine', 'interactions')}).T"),
    code("pd.DataFrame(summary['quarantine']).fillna(0).astype(int)"),
    code("P = '../data/processed/'\nev = pd.read_parquet(P + 'events.parquet'); prod = pd.read_parquet(P + 'products.parquet')\n"
         "inter = pd.read_parquet(P + 'interactions.parquet'); rt = pd.read_parquet(P + 'ratings.parquet')\n"
         "prod[['product_id','category','brand','price','price_minmax','log_price_z','brand_code','cat_Electronics','cat_Fashion']].head()"),
    md("## 2. Interaction distribution"),
    code("fig, ax = plt.subplots(1, 2, figsize=(11, 3.5))\norder = ['view','wishlist','add_to_cart','purchase']\n"
         "ev['event_type'].value_counts().reindex(order).plot.bar(ax=ax[0], color=[GREY, OCHRE, OLIVE, RUST], rot=0)\n"
         "ax[0].set_title('Events by type (funnel)')\nper_user = inter.groupby('user_id')['n_events'].sum()\n"
         "ax[1].hist(per_user, bins=50, color=INK); ax[1].set_yscale('log'); ax[1].set_title('Events per user (log)')\n"
         "plt.show(); per_user.describe().round(1)"),
    md("## 3. Item popularity (long tail)"),
    code("item_cnt = inter.groupby('product_id')['n_events'].sum().sort_values(ascending=False)\n"
         "fig, ax = plt.subplots(figsize=(7, 3.4)); ax.plot(range(1, len(item_cnt)+1), item_cnt.values, color=RUST)\n"
         "ax.set_yscale('log'); ax.set_xlabel('item rank'); ax.set_ylabel('events'); ax.set_title('Item popularity')\nplt.show()\n"
         "print(f'Top 10% of items receive {item_cnt.iloc[:len(item_cnt)//10].sum()/item_cnt.sum():.1%} of interactions; '\n"
         "      f'Gini = {eda.gini(item_cnt.values):.2f}')"),
    md("## 4. Sparsity of the user-item matrix"),
    code("n_u, n_i = inter.user_id.nunique(), inter.product_id.nunique()\n"
         "print(f'{len(inter):,} observed user-item pairs out of {n_u*n_i:,} possible -> sparsity {1-len(inter)/(n_u*n_i):.2%}')\n"
         "print(f'Purchased pairs only -> sparsity {1-inter.purchased.sum()/(n_u*n_i):.2%}')"),
    code("summary_eda = eda.run_eda()\nfrom IPython.display import Image, display\n"
         "for f in ['04_sparsity_heatmap', '06_category_event_heatmap', '05_rating_distribution', '07_daily_activity', '08_price_normalisation']:\n"
         "    display(Image(filename=f'../reports/figures/{f}.png', width=640))"),
    md("## 5. Findings\n"
       "* The funnel is steep: roughly 1 purchase per 7 views, so purchases alone are too sparse to train on - "
       "views, wishlist and cart events are used as weighted implicit feedback.\n"
       "* Activity and popularity are long-tailed: a small share of items gets most interactions, so a popularity "
       "baseline is strong and personalised models must beat it.\n"
       "* The purchase matrix is about 99% empty, which motivates matrix factorisation and co-occurrence features.\n"
       "* Ratings are skewed towards 4-5, so the Bayesian-smoothed rating is used as an item feature."),
    code("{k: v for k, v in summary_eda.items() if k != 'figures'}"),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
out = ROOT / "notebooks" / "01_data_preparation_and_eda.ipynb"
NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(out.parent)}}).execute()
nbf.write(nb, out)
print("wrote", out)
