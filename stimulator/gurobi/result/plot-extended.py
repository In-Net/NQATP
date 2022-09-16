import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

data = pd.read_csv('./data.csv')

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

pallete = sns.color_palette("husl", 8)
my_pal = {"MILP": pallete[0], "LP": pallete[2], "Greedy": pallete[5]}

fig, axs = plt.subplots(1, 2, figsize=(6,3))
axs[0].grid(color='#605B56', linestyle='dotted', linewidth=1, alpha=0.8)
axs[1].grid(color='#605B56', linestyle='dotted', linewidth=1, alpha=0.8)

std = sns.lineplot(data=data[data["eval"] == "imba"], x="xscale", y="std", hue="method", style="method", palette=my_pal, ax=axs[0], markers=True, legend=0)

time = sns.lineplot(data=data[data["eval"] == "scale"], x="xscale", y="time", hue="method", style="method", palette=my_pal, ax=axs[1], markers=True)
'''
for i, line in enumerate(ax.get_lines()):
  if i >= len(markers):
    break
  line.set_marker(markers[i])
'''
std.tick_params(left=False, bottom=False, labelsize=12)
time.tick_params(left=False, bottom=False, labelsize=12)

axs[1].xaxis.set_ticks(np.arange(8, 136, 24))
axs[0].set_ylabel("Switch Task STDEV", fontsize=12)
axs[0].set_xlabel("Query Imbalance (%)", fontsize=12)
axs[1].set_ylabel("Solving Time (s)", fontsize=12)
axs[1].set_xlabel("Network Scale (pod count)", fontsize=12)

plt.xticks(fontsize=10)
plt.yticks(fontsize=10)

handles, labels = axs[1].get_legend_handles_labels()
axs[1].legend(handles=handles, bbox_to_anchor=(-0.2,1.1), labels=["MILP", "LP", "Greedy"], loc='center', frameon=False, fontsize=14, ncol=3, columnspacing=0.5, handletextpad=0.3, handlelength=1.5)

axs[0].yaxis.set_ticks(np.arange(0, 3400, 500))
axs[1].yaxis.set_ticks(np.arange(0, 170, 40))

'''
axs[0].spines['top'].set_visible(False)
axs[0].spines['right'].set_visible(False)
axs[0].spines['bottom'].set_visible(False)
axs[0].spines['left'].set_visible(False)

axs[1].spines['top'].set_visible(False)
axs[1].spines['right'].set_visible(False)
axs[1].spines['bottom'].set_visible(False)
axs[1].spines['left'].set_visible(False)
'''
plt.tight_layout()
plt.subplots_adjust(wspace=0.3)
fig.savefig("gurobi-centralized-monitors.pdf", bbox_inches='tight', pad_inches=0)
# rounds_plot.savefig("./rounds_plot.png")
