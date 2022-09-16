import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

data = pd.read_csv('./control-entry-usage.csv')

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

pallete = sns.color_palette("husl", 8)
my_pal = {"W/I Cluster": pallete[0], "W/O Cluster": pallete[5]}

f, ax = plt.subplots(figsize=(5,3))
plt.grid(color='#605B56', linestyle='dotted', linewidth=1, alpha=0.8)

plot = sns.ecdfplot(data, x="pkt_num", hue="type", palette=my_pal, linewidth=2, ax=ax)

ax.set_xlabel("Number of Forwarding Rules", fontsize=14)
ax.set_ylabel("CDF", fontsize=14)

plot.lines[0].set_linestyle("--")

ax.legend(handles=ax.lines, labels=["W/O Clustering","W/ Clustering"], frameon=False, loc="center", bbox_to_anchor=(0.5,1.1), fontsize=12, ncol=2, columnspacing=1, handletextpad=0.3, handlelength=1.5)

ax.set_ylim(0,1)
ax.set_xscale("log")

plot.tick_params(left=False, bottom=False, labelsize=12)
'''
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
'''
# plot.lines[2].set_linestyle("-.")
# plot1.lines[2].set_linestyle("--")

plt.tight_layout()
f.savefig("./table-entries.pdf", bbox_inches='tight', pad_inches=0)

