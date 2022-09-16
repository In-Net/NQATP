from argparse import ArgumentParser
import json, logging

import seeker.podSeeker as Seeker
import judge.simpleJudge as Judge
import updater.simpleUpdater as Updater

class installed_query_info():
    def __init__(self, query_id, src_id, dst_id):
        self.query_id = query_id
        self.src_id = src_id
        self.dst_id = dst_id

# initialize switch perference weight
def init_env():
    total_switch_size = 20
    switch_weights = [0] * total_switch_size
    switch_loads = [0] * total_switch_size
    for i in range(total_switch_size):
        switch_loads[i] = []
    return switch_weights, switch_loads

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-q", "--query", help="Query input file location", dest="query_location", default="./data/queries.json")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    switch_weights, switch_loads = init_env()

    with open(args.query_location, 'r') as inputQueries:
        unparsed_queries = inputQueries.read()

    queries = json.loads(unparsed_queries)

    for query in queries:
        edge_sw1, edge_sw2 = Seeker.find_edge_switch_on_path(
            switch_id1=query['src_host_id'],
            switch_id2=query['dst_host_id'],
            pod_scale=4)
        aggr_sw1, aggr_sw2 = Seeker.find_aggr_switch_on_path(
            edge_id1=edge_sw1,
            edge_id2=edge_sw2,
            pod_scale=4)
        core_sws = Seeker.find_core_switch_on_path(pod_scale=4)

        edge_weight_1 = switch_weights[edge_sw1]
        edge_weight_2 = switch_weights[edge_sw2]
        aggr_weight_1, aggr_weight_2, core_weight = 0, 0, 0
        hybrid_weight_1, hybrid_weight_2, hybrid_weight_3, hybrid_weight_4 = 0, 0, 0, 0

        for aggr_sw in aggr_sw1:
            aggr_weight_1 += switch_weights[aggr_sw]
        for aggr_sw in aggr_sw2:
            aggr_weight_2 += switch_weights[aggr_sw]
        for core_sw in core_sws:
            core_weight += switch_weights[core_sw]

        hybrid_sw1 = [aggr_sw1[0], core_sws[0], core_sws[1]]
        hybrid_sw2 = [aggr_sw1[1], core_sws[2], core_sws[3]]
        hybrid_sw3 = [aggr_sw2[0], core_sws[0], core_sws[1]]
        hybrid_sw4 = [aggr_sw2[1], core_sws[2], core_sws[3]]

        for sw_id in hybrid_sw1:
            hybrid_weight_1 += switch_weights[sw_id]

        for sw_id in hybrid_sw2:
            hybrid_weight_2 += switch_weights[sw_id]

        for sw_id in hybrid_sw3:
            hybrid_weight_3 += switch_weights[sw_id]

        for sw_id in hybrid_sw4:
            hybrid_weight_4 += switch_weights[sw_id]

        chosen_pos = Judge.find_lowest_cost_node(
            [edge_weight_1, edge_weight_2, aggr_weight_1, aggr_weight_2, core_weight,
            hybrid_weight_1, hybrid_weight_2, hybrid_weight_3, hybrid_weight_4],
            [edge_sw1, edge_sw2, aggr_sw1, aggr_sw2, core_sws, hybrid_sw1, hybrid_sw2,
            hybrid_sw3, hybrid_sw4])

        Updater.update_weight(weights=switch_weights, pos=chosen_pos)

        installed_query = installed_query_info(query_id=query['query_id'],
            src_id=query['src_host_id'], dst_id=query['dst_host_id'])

        if isinstance(chosen_pos, list):
            for pos in chosen_pos:
                switch_loads[pos].append(installed_query)
        elif isinstance(chosen_pos, int):
            switch_loads[chosen_pos].append(installed_query)

    # print results
    print("####### Control Plane Placement Results #######")
    for index, loads in enumerate(switch_loads):
        if len(loads) > 0:
            print("Switch %d got %d tasks" % (index, len(loads)))
            '''
            for load in loads:
                if isinstance(load, installed_query_info):
                    print("Switch %d install query no.%d, from host %d to host %d" %
                        (index, load.query_id, load.src_id, load.dst_id))
            '''
