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

import json

# total_query_number = 100
# entry_within_query = 2

# Enumerate Possible Switch Set List
# edge switches
# 0 : (s0)
# 1 : (s1)
# 2 : (s2)
# 3 : (s3)
# 4 : (s4)
# 5 : (s5)
# 6 : (s6)
# 7 : (s7)
# 8 : (s8, s9)
# 9 : (s10, s11)
# 10: (s12, s13)
# 11: (s14, s15)
# 12: (s8, s18, s19)
# 13: (s9, s16, s17)
# 14: (s10, s18, s19)
# 15: (s11, s16, s17)
# 16: (s12, s18, s19)
# 17: (s13, s16, s17)
# 18: (s14, s18, s19)
# 19: (s15, s16, s17)
# 20: (s16, s17, s18, s19)

with open("/home/lthpc/git/catchment-basin-seeker/data/queries.json") as input:
    unparsed_queries = input.read()

queries = json.loads(unparsed_queries)

edges_within_switches = [0] * 8
for i in range(8):
    edges_within_switches[i] = []

try:

    # Create a new model
    m = gp.Model("bipartite-tor")

    # Create variables for switch weights
    w0 = m.addVar(vtype=GRB.INTEGER, name="w0")
    w1 = m.addVar(vtype=GRB.INTEGER, name="w1")
    w2 = m.addVar(vtype=GRB.INTEGER, name="w2")
    w3 = m.addVar(vtype=GRB.INTEGER, name="w3")
    w4 = m.addVar(vtype=GRB.INTEGER, name="w4")
    w5 = m.addVar(vtype=GRB.INTEGER, name="w5")
    w6 = m.addVar(vtype=GRB.INTEGER, name="w6")
    w7 = m.addVar(vtype=GRB.INTEGER, name="w7")
    '''
    w8 = m.addVar(vtype=GRB.INTEGER, name="w8")
    w9 = m.addVar(vtype=GRB.INTEGER, name="w9")
    w10 = m.addVar(vtype=GRB.INTEGER, name="w10")
    w11 = m.addVar(vtype=GRB.INTEGER, name="w11")
    w12 = m.addVar(vtype=GRB.INTEGER, name="w12")
    w13 = m.addVar(vtype=GRB.INTEGER, name="w13")
    w14 = m.addVar(vtype=GRB.INTEGER, name="w14")
    w15 = m.addVar(vtype=GRB.INTEGER, name="w15")
    w16 = m.addVar(vtype=GRB.INTEGER, name="w16")
    w17 = m.addVar(vtype=GRB.INTEGER, name="w17")
    w18 = m.addVar(vtype=GRB.INTEGER, name="w18")
    w19 = m.addVar(vtype=GRB.INTEGER, name="w19")
    '''

    # Create variables for entry candidates
    for index, entry in enumerate(queries):
        # Edge 0~3 is for first switch, 4~7 is for second, and 8 is shared by both (core sws)
        e_ = m.addVars(range(2), vtype=GRB.BINARY, name='e_')
        # Add constraint: ΣE_k = 1 for edges within the same entry
        m.addConstr(gp.quicksum(e_[i] for i in range(2)) == 1)

        '''
        edges_within_switches[16].append(e_[8])
        edges_within_switches[17].append(e_[8])
        edges_within_switches[18].append(e_[8])
        edges_within_switches[19].append(e_[8])
        '''

        # Distribute influence factor from edges to switches
        pod_1 = int(entry['src_host_id']) / 4
        pod_2 = int(entry['dst_host_id']) / 4

        edges_within_switches[int(entry['src_host_id'] / 2)].append(e_[0])
        # edges_within_switches[8 + pod_1 * 2].append(e_[1])
        # edges_within_switches[9 + pod_1 * 2].append(e_[1])
        # edges_within_switches[8 + pod_1 * 2].append(e_[2])
        # edges_within_switches[18].append(e_[2])
        # edges_within_switches[19].append(e_[2])
        # edges_within_switches[9 + pod_1 * 2].append(e_[3])
        # edges_within_switches[16].append(e_[3])
        # edges_within_switches[17].append(e_[3])

        edges_within_switches[int(entry['dst_host_id'] / 2)].append(e_[1])
        # edges_within_switches[8 + pod_2 * 2].append(e_[5])
        # edges_within_switches[9 + pod_2 * 2].append(e_[5])
        # edges_within_switches[8 + pod_2 * 2].append(e_[6])
        # edges_within_switches[18].append(e_[6])
        # edges_within_switches[19].append(e_[6])
        # edges_within_switches[9 + pod_2 * 2].append(e_[7])
        # edges_within_switches[16].append(e_[7])
        # edges_within_switches[17].append(e_[7])

        '''
        edges_within_switches[16].append(e_[8])
        edges_within_switches[17].append(e_[8])
        edges_within_switches[18].append(e_[8])
        edges_within_switches[19].append(e_[8])
        '''

    # Set objective
    m.setObjective(8 * (w0 ** 2 + w1 ** 2 + w2 ** 2 + w3 ** 2 + w4 ** 2 + w5 ** 2 + w6 ** 2 + w7 ** 2) - (w0 + w1 + w2 + w3 + w4 + w5 + w6 + w7) ** 2, GRB.MINIMIZE)

    # Add constraint: W_i = ΣE_j for j in edges involves in target switch
    m.addConstr(gp.quicksum(edges_within_switches[0]) == w0)
    m.addConstr(gp.quicksum(edges_within_switches[1]) == w1)
    m.addConstr(gp.quicksum(edges_within_switches[2]) == w2)
    m.addConstr(gp.quicksum(edges_within_switches[3]) == w3)
    m.addConstr(gp.quicksum(edges_within_switches[4]) == w4)
    m.addConstr(gp.quicksum(edges_within_switches[5]) == w5)
    m.addConstr(gp.quicksum(edges_within_switches[6]) == w6)
    m.addConstr(gp.quicksum(edges_within_switches[7]) == w7)
    '''
    m.addConstr(gp.quicksum(edges_within_switches[8]) == w8)
    m.addConstr(gp.quicksum(edges_within_switches[9]) == w9)
    m.addConstr(gp.quicksum(edges_within_switches[10]) == w10)
    m.addConstr(gp.quicksum(edges_within_switches[11]) == w11)
    m.addConstr(gp.quicksum(edges_within_switches[12]) == w12)
    m.addConstr(gp.quicksum(edges_within_switches[13]) == w13)
    m.addConstr(gp.quicksum(edges_within_switches[14]) == w14)
    m.addConstr(gp.quicksum(edges_within_switches[15]) == w15)
    m.addConstr(gp.quicksum(edges_within_switches[16]) == w16)
    m.addConstr(gp.quicksum(edges_within_switches[17]) == w17)
    m.addConstr(gp.quicksum(edges_within_switches[18]) == w18)
    m.addConstr(gp.quicksum(edges_within_switches[19]) == w19)
    '''

    # Optimize model
    m.optimize()

    weights = []
    for v in m.getVars():
        if v.varName[0] == 'w':
            print('%s %g' % (v.varName, v.x))
            weights.append(v.x)

    print('Obj: %g' % m.objVal)
    mean = sum(weights) / len(weights)
    std_dev = (sum((i - mean) ** 2 for i in weights) / len(weights)) ** 0.5
    print('Weight mean = %g, variance = %g' % (mean, std_dev))
    # print(edges_within_switches[10])

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')
