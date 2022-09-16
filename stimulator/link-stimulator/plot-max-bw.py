import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

data = pd.read_csv('./max-query.csv')
markers = ['X', 'D', 'o']
'''
x = np.arange(8, 25, 1)
y_noaggr = (10000 / 24.0 / x)
y_aggr = np.linspace(10000 / 24.0, 10000 / 24.0, 17)
'''

'''
x_val, y_noaggr, y_aggr = [], [], []
for i in range(8, 25):
  x_val.append(i)
  y_noaggr.append(10000 / 24.0 / i)
  y_aggr.append(10000 / 24.0)
'''

fig, ax = plt.subplots(1, 1, figsize=(4,2))

plot_aggr = sns.lineplot(data=data, x="query size", y="max query", palette="colorblind", hue="type", ax=ax)

for i, line in enumerate(ax.get_lines()):
  if i >= len(markers):
    break
  line.set_marker(markers[i])

ax.yaxis.set_ticks(np.arange(100, 500, 100))

ax.set_ylabel("Max Query Per Sec (kilo-)", fontsize=8)
ax.set_xlabel("Task Size", fontsize=8)

legend = plt.legend(prop={'size': 8}, frameon=False, labels=["MonAggr", "SNMP"])
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)

# Finalize the plot
# sns.despine(bottom=True)
# plt.setp(f.axes, yticks=[])
plt.tight_layout()

fig.savefig("max-query.png")
