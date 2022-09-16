## Testing parameter
1000 query tasks, 32 pods, a percentage of queries are spanned by all-to-all query
And an all-to-all query is involved with 5 sources. And we only want 5 final multicast group.
We varies the percentage rate from 80% to 20% in this experiment.

## Results

Notice that every average task load is the same in following exp while being 125 ALWAYS,
so I just ignore it and instead of focus on the variance on switch loads.

### Gurobi

%,std_err
80,92.96
75,91.80
70,91.48
65,88.90
60,86.72
55,87.68
50,82.44
45,80.54
40,77.93
35,73.25
30,70.40
25,66.08
20,54.41

### Baseline

%,std_err
80,144.36
75,143.72
70,141.51
65,142.47
60,140.77
55,138.62
50,138.16
45,134.68
40,135.00
35,127.75
30,125.79
25,119.02
20,118.15
