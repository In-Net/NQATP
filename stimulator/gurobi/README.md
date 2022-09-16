# Solve with Gurobi

Gurobi is a mathematical model solver for **L**inear **P**rogramming
(and **Q**uadratic **P**rogramming too). We model the placement problem
as a bipartite graph matching decison problem.

We could model every chosen mapping between entry and monitor sets to a *edge*,
which is a binary variable in Gurobi (similar to **Boolean** in other common language
 ). Once chosen the edge variable will be marked as 1.

However, since in a normal pod topology, there will be **9** possible edge for each
entry, so the variable space will be pretty huge. Precisely speaking, it will be **9 \* (number
  of overall entries) binary variables and 20 integer variables**

## Quick Start

1. Generate query (if needed)
```sh
cd data/
python3 gen_query.py -n [number of query] -e [entry per query] [-m 1]
```

Unlike in other case which might require random shuffle of data, it is almost useless to
do so here.

2. python
```py
python bipartite.py
```

Notice that you have to install Gurobi first (it require paid license, however, if you are a
  student, then you are *free* to go)

## Different version of bipartite
1. Bipartite v1
Query are from host to host, and monitor is allowed to be on not only ToR

2. Bipartite tor(v2)
Query are from host to host, but monitor is only allowed on ToR

3. Bipartite v3
Query are from pod to pod, and monitor is only allowed on ToR