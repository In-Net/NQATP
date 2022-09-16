import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

data = pd.read_csv('./data.csv')
# markers = ['X', 'D', 'o', 'x']
plt.rcParams["font.family"] = "Times New Roman"
pallete = sns.color_palette("husl", 8)
my_pal = {"LP": pallete[0], "Greedy": pallete[5]}

fig, ax = plt.subplots(1, 1, figsize=(4.5,3))
plt.grid(color='#605B56', linestyle='dotted', linewidth=1, alpha=0.8)

std = sns.lineplot(data=data, x="centralized percentage", y="std", hue="type", style="type", palette=my_pal, ax=ax, markers=True)
'''
for i, line in enumerate(ax.get_lines()):
  if i >= len(markers):
    break
  line.set_marker(markers[i])
'''
std.tick_params(left=False, bottom=False, labelsize=14)

ax.yaxis.set_ticks(np.arange(60, 160, 20))
ax.set_ylabel("Switch Task Load Std-Err", fontsize=16)
ax.set_xlabel("Imbalanced Query Flow Space Percentage(%)", fontsize=16)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)


handles, labels = ax.get_legend_handles_labels()
ax.legend(handles=handles, labels=["0-1 programming", "Greedy"], bbox_to_anchor=(0.5,1.1), loc='center', frameon=False, fontsize=14, ncol=2, columnspacing=0.5, handletextpad=0.3, handlelength=1.5)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)

plt.tight_layout()

fig.savefig("gurobi-centralized-v2.pdf", bbox_inches='tight', pad_inches=0)
# rounds_plot.savefig("./rounds_plot.png")
