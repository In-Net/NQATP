import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

data_vio = pd.read_csv('./data-violin.csv')

# plt.grid(color='#605B56', linestyle='dotted', linewidth=1, alpha=0.8)
plt.rcParams["font.family"] = "Times New Roman"

pallete = sns.color_palette("husl", 8)
my_pal = {"MonAggr": pallete[0], "SNMP": pallete[4]}

f, ax = plt.subplots(figsize=(6,4.5))

ax.grid(color='#605B56', linestyle='dotted', linewidth=1, alpha=0.8)

plot = sns.violinplot(data=data_vio, x="ecnt", y="pcnt", hue="type", linewidth=1, palette=my_pal, split=True, inner="quart", ax=ax)
ax.legend(handles=ax.lines, labels=["3 Tier Polling","DriftSwitch (No Cluster)"], frameon=False, loc="center",  bbox_to_anchor=(0.5,1.2),  ncol=2, columnspacing=2, handletextpad=0.3, handlelength=1.5)

plot.tick_params(left=False, bottom=False, labelsize=10)

ax.set_xlabel("Query Size", fontsize=14)
ax.set_ylabel("One-directional Link Usage (count)", fontsize=14)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)

plt.tight_layout()
plt.subplots_adjust(wspace=0.2)
f.savefig("./origin-bmv2-link-violin.pdf", bbox_inches='tight', pad_inches=0)
