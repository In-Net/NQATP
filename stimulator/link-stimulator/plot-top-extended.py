import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

data = pd.read_csv('./emulated_result.csv')

plt.rcParams["font.family"] = "Times New Roman"

pallete = sns.color_palette("husl", 8)
my_pal = {"Best-MonAggr": pallete[0], "Worst-MonAggr": pallete[1], "SNMP": pallete[4]}

f, ax = plt.subplots(figsize=(6,3))
plt.grid(color='#605B56', linestyle='dotted', linewidth=1, alpha=0.8)

plot = sns.ecdfplot(data, x="pkt_num", hue="type", palette=my_pal, linewidth=2, ax=ax)

plot.lines[1].set_linestyle("--")
plot.lines[2].set_linestyle("-.")

ax.set_xlabel("Response Traffic Volume (No. of Packets)", fontsize=16)
ax.set_ylabel("CDF", fontsize=16)
ax.legend(handles=ax.lines, labels=["DriftSwitch\n(No Clustering)","DriftSwitch\n(One Cluster)","3 Tier\nPolling"], frameon=False, loc="center", bbox_to_anchor=(0.5,1.2), fontsize=12, ncol=3, columnspacing=0.5, handletextpad=0.3, handlelength=1.5)

ax.set_ylim(0.95,1)
ax.set_xlim(0,800)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)

plt.tick_params(left=False, bottom=False, labelsize=12)

plt.tight_layout()
f.savefig("./large-scale-emulation-top-extended.pdf", bbox_inches='tight', pad_inches=0)
