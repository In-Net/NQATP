# catchment-basin-seeker
Find monitor and aggregator placement in a pod topology

A control plane simple algorithm(?) to discover lowest cost monitor &
aggregator placement in datacenter pod topology network.

![Pod Topo](/image/pod-topo.png)

In a pod topo, each host (server) is connected to a destinated edge switch (ToR), while
it can latter choose from (k/2) aggregation switch, and then a destinated core switch
for routing to destinated host once aggregation switch is chosen. See []() for more
details.

We thus, label the switch with int ids. Starting from 0 in the first edge switch ("first"
here correspond to host order), then iterates through all k<sup>2</sup>/2 edge
switches, then we move on to iteration of k<sup>2</sup>/2 aggregation switches,
finally k<sup>2</sup>/4 iteration of core switches

As a result, we unfold the tree operation to an array operation, so there won't be any
tree data structure, just 2D array look up.

### Seekers
Actually, it would be naive and rather simple if we only have to consider monitor
placement only. However, with the introduction of aggregator, which is build upon
monitor placement, while easily mess the balance established by monitor arrangment.

As a basic insight, aggregator placement is basically another monitor placement,
however, this time on each query entry there is always be a controller in one side.
This means the controller side switches has a higher chance of being picked.

Also, if we really spread out monitors among all available switches evenly, then those
put closer to controller (i.e. core switches) will has very limited choices of aggregator
placement, which might flood controller's ToR since it is always an available choice.

This is actually a very multi-dimenional problem. The matrix could include task balance,
overall task amout, and remaining incast flows.

Last but not the least, the ratio between query and its entry number matters a lot in
the importance of aggregator's impact on inbalanceness. For more entry number, since
each entry will span at least one task, so it will increase the importance of monitor
placement. However, since we need at least an aggregator for each query. As a result,
if the query entry ratio is pretty high (entry >>  query) then we could maybe ignore
the impact from aggregator. Otherwise, we will have to real consideration for aggregator
placement.

As a result, we come out a simple (un-optimized) method of placing monitors ...

> since I am still working on enhancing the performance and demo current problem to
my boss (in brief, we are still iterating the solutions). The explaination of alg will be
offered once it is relatively stable.

#### Types

1. Stubborn
Sandhill base approach (conflicted sandhill height is determined by avg)
2. Clever (Conservative)
Reservoir base approach (conflicted sandhill height is determined by min)
3. Aggressive
 Reservoir base approach (conflicted sandhill height is determined by avg)

#### Others

TODO:
1. Probabilistic sandhill swap-int-and-out

Currently we will start by pushing down the highest sandhill till it is down to average
(an underestimate water level, which will dicuss later). However, this will make its neighbor
edge monitor hard to spread any query in the deeper network latter, which will lead to
a serious unbalance.
As a result, we should make every sandhill probabilistically be pushed according to their
weight maybe (or a weighted round-robin to ensure fairness).
2. Estimation of future water level

The water level of overall task will be monotonically increasing, however, we can't be sure
about the final water level. As a result, the first sandhill to be pushed will suffer the most
from the inaccruacy.
It would be better to add a decading function to the water level as an estimation.

## Environment Requirement
1. python verion >= 3.6.9 (Tested under 3.6.9)

## Quick start
1. Generate queries
```sh
cd data/
python3 gen_query.py [-s] [-m 1]
```

[-s] is optional, it randomly shuffle the output queries (doesn't mean much in clever
seeker though, since it will first aggregate each query)

[-m 1] is optional too, by default the generator generates a randomly distributed queries
spread though all hosts (yes, it includes controller, since we don't place monitor on
controller's ToR, all queries related will be flooded into the other side of query)
However, by specifying [-m 1], it generates a centrialized distribution of queries that
mainly between two specific pod.

2. Run clever seeker
```
cd ..
python3 clever_seeker.py [-n 250]
```

[-n 250] is used to tell the seeker there will be 250 queries, by default it will be 250
