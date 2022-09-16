import pandas as pd
import seaborn as sns

time_data = pd.read_csv('./exec_robust.csv')
time_plot = sns.boxplot(data=time_data, palette="colorblind")
time_plot.set(xlabel="Inbalance between queries (%)", ylabel = "Standard error among all switch jobs", title="Linear programming placer could mitigate 40% of inbalanced queries")
time_fig = time_plot.get_figure()
time_fig.savefig("./robust.png")
