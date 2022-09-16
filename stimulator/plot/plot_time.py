import pandas as pd
import seaborn as sns

time_data = pd.read_csv('./exec_time.csv')
time_plot = sns.boxplot(data=time_data, palette="colorblind")
time_plot.set(xlabel="# of queries (each with 4 entries)", ylabel = "solving time (sec)", title="Linear solving time with increasing query size")
time_fig = time_plot.get_figure()
time_fig.savefig("./time.png")
