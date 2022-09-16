'''
Choose lowest cost node(s), some placement preference is applied here
'''

# add no location preference on node position
def find_lowest_cost_node(costs: list, nodes: list):
    return nodes[costs.index(min(costs))]
