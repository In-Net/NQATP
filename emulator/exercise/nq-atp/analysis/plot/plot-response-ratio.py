import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

data_e2 = pd.read_csv('./response-e2-ratio.csv')
data_e3 = pd.read_csv('./response-e3-ratio.csv')
data_e4 = pd.read_csv('./response-e4-ratio.csv')

# plt.grid(color='#605B56', linestyle='dotted', linewidth=1, alpha=0.8)
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

pallete = sns.color_palette("husl", 8)
my_pal = {"MonAggr": pallete[0], "SNMP": pallete[4]}

f, axs = plt.subplots(1, 3, figsize=(8,3))

axs[0].grid(color='#605B56', linestyle='dotted', linewidth=1, alpha=0.8)
axs[1].grid(color='#605B56', linestyle='dotted', linewidth=1, alpha=0.8)
axs[2].grid(color='#605B56', linestyle='dotted', linewidth=1, alpha=0.8)

plot0 = sns.ecdfplot(data_e2, x="Ratio", hue="Type", palette=my_pal, linewidth=2, ax=axs[0])
plot1 = sns.ecdfplot(data_e3, x="Ratio", hue="Type", palette=my_pal, linewidth=2, ax=axs[1])
plot2 = sns.ecdfplot(data_e4, x="Ratio", hue="Type", palette=my_pal, linewidth=2, ax=axs[2])


plot0.lines[0].set_linestyle("-.")
plot1.lines[0].set_linestyle("-.")
plot2.lines[0].set_linestyle("-.")


axs[1].legend(handles=axs[1].lines, labels=["3 Tier Polling","NQ/ATP"], frameon=False, loc="center",  bbox_to_anchor=(0.5,1.2), fontsize=14,  ncol=2, columnspacing=2, handletextpad=0.3, handlelength=1.5)
# ax.legend(handles=handles, labels=["MonAggr", "SNMP"], bbox_to_anchor=(0.5,1.1), loc='center', frameon=False, fontsize=16, ncol=2, columnspacing=0.5, handletextpad=0.3, handlelength=1.5)

plot0.tick_params(left=False, bottom=False, labelsize=10)
plot1.tick_params(left=False, bottom=False, labelsize=10)
plot2.tick_params(left=False, bottom=False, labelsize=10)

axs[0].xaxis.set_ticks(np.arange(0, 2.4, 0.4))
axs[1].xaxis.set_ticks(np.arange(0, 3.4, 0.8))
axs[2].xaxis.set_ticks(np.arange(0, 5, 1))

'''
axs[0].set_ylim(0.4,1)
axs[1].set_ylim(0.4,1)
axs[2].set_ylim(0.4,1)
'''

axs[0].yaxis.set_ticks(np.arange(0, 1.1, 0.2))
axs[1].yaxis.set_ticks(np.arange(0, 1.1, 0.2))
axs[2].yaxis.set_ticks(np.arange(0, 1.1, 0.2))

axs[0].set_title("Query Size = 2", fontsize=10)
axs[1].set_title("Query Size = 3", fontsize=10)
axs[2].set_title("Query Size = 4", fontsize=10)

axs[0].set_xlabel("")
axs[0].set_ylabel("CDF", fontsize=14)
axs[1].set_xlabel("Response Traffic Volume (No. of Packets)", fontsize=14)
axs[1].set_ylabel("")
axs[2].set_xlabel("")
axs[2].set_ylabel("")

axs[0].get_legend().remove()
axs[2].get_legend().remove()

'''
axs[0].spines['top'].set_visible(False)
axs[0].spines['right'].set_visible(False)
axs[0].spines['bottom'].set_visible(False)
axs[0].spines['left'].set_visible(False)

axs[1].spines['top'].set_visible(False)
axs[1].spines['right'].set_visible(False)
axs[1].spines['bottom'].set_visible(False)
axs[1].spines['left'].set_visible(False)

axs[2].spines['top'].set_visible(False)
axs[2].spines['right'].set_visible(False)
axs[2].spines['bottom'].set_visible(False)
axs[2].spines['left'].set_visible(False)
'''

plt.tight_layout()
plt.subplots_adjust(wspace=0.2)
f.savefig("./bmv2-link-response-ratio.pdf", bbox_inches='tight', pad_inches=0)
