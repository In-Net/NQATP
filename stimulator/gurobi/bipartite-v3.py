#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

# Copyright 2020, Gurobi Optimization, LLC

# Solves a quadric objective LP on bipartite matching
# We want the weight of each node to be balanced, so
# we adopt a "lightly twisted" Jain's fairness index
# since Gurobi doesn't support using variables as dividends
#  minimize
#        N * Σ(W_i ** 2) - (Σ(W_i) ** 2) for i in range(n)
#  subject to
#        W_i = ΣE_j for j in edges involves in target switch
#        ΣE_k = 1 for edges within the same entry
#        W_i integer
#        E_j binary

import gurobipy as gp
from gurobipy import GRB
from argparse import ArgumentParser

import json

# total_query_number = 100
# entry_within_query = 2

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-p", "--pod", help="Number of pod in network topology", dest="pod", type=int, default=32)

    args = parser.parse_args()

    # the input format should be [((src1, src2, ...), (dst1, dst2, ...)), (), ...]
    with open("/home/lthpc/git/catchment-basin-seeker/data/queries-v3.json") as input:
        unparsed_queries = input.read()

    queries = json.loads(unparsed_queries)

    tor_edges = [0] * args.pod
    for i in range(args.pod):
        tor_edges[i] = []

    try:

        # Create a new model
        m = gp.Model("bipartite-v3")

        # Create variables for switch weights
        weights = m.addVars(range(args.pod), vtype=GRB.INTEGER, name="weights")

        # Create variables for entry candidates
        for entry in queries:
            # Edge 0~3 is for first switch, 4~7 is for second, and 8 is shared by both (core sws)
            e_ = m.addVars(range(2), vtype=GRB.BINARY, name='e_')
            # Add constraint: ΣE_k = 1 for edges within the same entry
            m.addConstr(gp.quicksum(e_[i] for i in range(2)) == 1)

            for src in entry["src"]:
                tor_edges[src].append(e_[0])

            for dst in entry["dst"]:
                tor_edges[dst].append(e_[1])

        # Set objective
        m.setObjective(args.pod * sum(weights[i] ** 2 for i in range(args.pod)) - weights.sum() ** 2, GRB.MINIMIZE)

        # Add constraint: W_i = ΣE_j for j in edges involves in target switch
        for index in range(args.pod):
            m.addConstr(gp.quicksum(tor_edges[index]) == weights[index])
        
        # Limit its node exploration
        # m.setParam('NodeLimit ', 1000)
        m.setParam('TimeLimit', 180)

        # Optimize model
        m.optimize()

        final_weights = []
        for v in m.getVars():
            if v.varName[0] == 'w':
                print('%s %g' % (v.varName, v.x))
                final_weights.append(v.x)

        print('Obj: %g' % m.objVal)
        mean = sum(final_weights) / len(final_weights)
        std_dev = (sum((i - mean) ** 2 for i in final_weights) / len(final_weights)) ** 0.5
        print('Weight mean = %g, variance = %g' % (mean, std_dev))

    except gp.GurobiError as e:
        print('Error code ' + str(e.errno) + ': ' + str(e))

    except AttributeError:
        print('Encountered an attribute error')
