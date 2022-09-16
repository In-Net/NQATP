import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

data = pd.read_csv('./data.csv')
hatches = ['-', '\\', 'x', '\\']

fig, ax = plt.subplots(1, 1, figsize=(4,2))
'''
variance = sns.lineplot(data=data, x="centralized percentage", y="load variance", hue="type", palette="colorblind" , marker='o', ax=ax)
'''
std = sns.barplot(data=data, x="centralized percentage", y="std", hue="type", palette="colorblind", ax=ax)

print(len(std.patches))

for i, thisbar in enumerate(std.patches):
  if i%2 == 0:
    thisbar.set_hatch('\\')


# ax.set_ylabel("load variance")
ax.yaxis.set_ticks(np.arange(0, 200, 40))
ax.set_ylabel("Switch Task Load Std-Err", fontsize=8)
ax.set_xlabel("Imbalanced Query Flow Space Percentage(%)", fontsize=8)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)

'''
legend = plt.legend(prop={'size': 8}, frameon=False, labels=["incremental aggregation", "non-incremental aggregation"])
'''
legend = plt.legend(prop={'size': 6}, frameon=False, labels=["0-1 programming", "Greedy"])


# Finalize the plot
# sns.despine(bottom=True)
# plt.setp(f.axes, yticks=[])
plt.tight_layout()

fig.savefig("gurobi-centralized-bar.png")
# rounds_plot.savefig("./rounds_plot.png")
