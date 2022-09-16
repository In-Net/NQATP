import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

data = pd.read_csv('./data.csv')
markers = ['X', 'D', 'o', 'x']

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

pallete = sns.color_palette("husl", 8)
my_pal = {"LP": pallete[0], "Random": pallete[5]}

'''
lpc = data[data["type"]=="LP"]
rndc = data[data["type"]=="Random"]

print(np.percentile(lpc["hamming distance"], 90))
print(np.percentile(rndc["hamming distance"], 90))
'''

data["hamming distance"] = data["hamming distance"] / 10

fig, ax = plt.subplots(1, 1, figsize=(4.5,3))
plt.grid(color='#605B56', linestyle='dotted', linewidth=1, alpha=0.8)

variance = sns.lineplot(data=data, x="centralized percentage", y="hamming distance", hue="type", palette=my_pal, style="type", markers=True, ax=ax)
'''
for i, line in enumerate(ax.get_lines()):
  if i >= len(markers):
    break
  line.set_marker(markers[i])
'''

# ax.set_ylabel("load variance")
variance.tick_params(left=False, bottom=False, labelsize=14)
ax.yaxis.set_ticks(np.arange(5, 85, 15))
ax.set_ylabel("Extra MCast\nTarget(%)", fontsize=12)
ax.set_xlabel("Imbalanced Query Flow Space\nPercentage(%)", fontsize=12)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

# legend = plt.legend(prop={'size': 6}, frameon=False, labels=["K-means Clustering", "Random Clustering"])
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles=handles, labels=["K-means Clustering", "Random Clustering"], bbox_to_anchor=(0.5,1.1), loc='center', frameon=False, fontsize=12, ncol=2, columnspacing=0.5, handletextpad=0.3, handlelength=1.5)
'''
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
'''
# Finalize the plot
# sns.despine(bottom=True)
# plt.setp(f.axes, yticks=[])
plt.tight_layout()

fig.savefig("cluster-centralized-v2.pdf", bbox_inches='tight', pad_inches=0)


