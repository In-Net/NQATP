'''
Stubborn seeker borrow the main structure from clever Seeker
However, it insist putting aggregators on controller's ToR,
and also make controller's ToR available for placing monitor
'''


from argparse import ArgumentParser
import json, logging, math

import seeker.podSeeker as Seeker
import judge.simpleJudge as Judge
import updater.simpleUpdater as Updater

class Query():
    def __init__(self, query_id, src_id, dst_id):
        self.query_id = query_id
        self.src_id = src_id
        self.dst_id = dst_id

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

# Python program to illustrate the intersection
# of two lists in most simple way
def intersection(lst1:list, lst2:list):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

def create_env():
    weights = [0] * 20
    queries = [0] * 20
    link_costs = [0] * 20
    for i in range(20):
        queries[i] = []
        # link_costs[src][dst]
        link_costs[i] = [0] * 20
    return weights, queries, link_costs

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-r", "--read", help="Query input file location", dest="query_location", default="./data/queries.json")
    parser.add_argument("-n", "--number", help="Total query number", dest="query_number", type=int, default=250)
    parser.add_argument("-a", "--aggregator", help="Also deploy aggregator", type=str2bool, nargs='?',
const=True, default=True, dest="deploy_aggr")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    weights, switch_queries, link_costs = create_env()

    with open(args.query_location, 'r') as read_queries:
        unparsed_queries = read_queries.read()

    input_queries = json.loads(unparsed_queries)


    if args.query_number <= 0:
        logging.error("Query number should be a positive integer !")
        exit()

    # mapping relationship between query and its monitors
    monitors_under_queries = [0] * args.query_number
    for i in range(args.query_number):
        monitors_under_queries[i] = []

    # we first place all query only to edge sw
    # also consider load balance among edge sw
    # but never place monitor on controller's edge sw
    # and always place aggregator on controller's edge sw
    for input_query in input_queries:
        # install monitor for each query
        query = Query(query_id=input_query['query_id'],
            src_id=input_query['src_host_id'],
            dst_id=input_query['dst_host_id'])
        edge_sw1, edge_sw2 = Seeker.find_edge_switch_on_path(
            switch_id1=query.src_id,
            switch_id2=query.dst_id,
            pod_scale=4)
        if edge_sw1 == 0:
            switch_queries[edge_sw2].append(query)
            monitors_under_queries[input_query['query_id']].append(edge_sw2)
            weights[edge_sw2] += 1
        elif edge_sw2 == 0:
            switch_queries[edge_sw1].append(query)
            monitors_under_queries[input_query['query_id']].append(edge_sw1)
            weights[edge_sw1] += 1
        elif weights[edge_sw1] > weights[edge_sw2]:
            switch_queries[edge_sw2].append(query)
            monitors_under_queries[input_query['query_id']].append(edge_sw2)
            weights[edge_sw2] += 1
        else:
            switch_queries[edge_sw1].append(query)
            monitors_under_queries[input_query['query_id']].append(edge_sw1)
            weights[edge_sw1] += 1

    # currently we got the lowest overall tasks
    # since there will only be one monitor for each query entry
    # every query entry on monitor/aggregator is counted as task
    # we take a conservative method, keep most queries far from controller
    if args.deploy_aggr:
        overall_task_count = len(input_queries) + args.query_number
    else:
        overall_task_count = len(input_queries)

    # sandhills are edge monitors awaits to push their task to center sws
    sandhills = sorted(range(len(weights)), key=lambda k: weights[k], reverse=True)

    for sandhill in sandhills:
        if sandhill == 0 or sandhill > 7:
            continue

        # [(entry id, [sw_id1, ...]), (...)]
        swap_out_list = []
        for index, switch_query in enumerate(switch_queries[sandhill]):
            # find victim
            aggr_sws = Seeker.find_single_aggr(edge_id=sandhill, pod_scale=4)
            aggr_cost = (weights[aggr_sws[0]] + weights[aggr_sws[1]]) / 2
            hybrid_cost_with_0, hybrid_cost_with_1, core_cost = weights[aggr_sws[0]], weights[aggr_sws[1]], 0
            core_replace_1 = Seeker.find_single_core(aggr_id=aggr_sws[1], pod_scale=4)
            core_replace_0 = Seeker.find_single_core(aggr_id=aggr_sws[0], pod_scale=4)
            for core_sw in core_replace_1:
                hybrid_cost_with_0 += weights[core_sw]
                core_cost += weights[core_sw]
            for core_sw in core_replace_0:
                hybrid_cost_with_1 += weights[core_sw]
                core_cost += weights[core_sw]

            chosen_pos = Judge.find_lowest_cost_node(
                [weights[sandhill], aggr_cost, (hybrid_cost_with_0 / 3), (hybrid_cost_with_1 / 3), (core_cost / 4)],
                [[sandhill], aggr_sws, [aggr_sws[0]] + core_replace_1, [aggr_sws[1]] + core_replace_0, core_replace_0 + core_replace_1])

            if sandhill in chosen_pos:
                    break
            else:
                weights[sandhill] -= 1
                for sw in chosen_pos:
                    weights[sw] += 1
                swap_out_list.append((index, chosen_pos))

        for swap_out_item in reversed(swap_out_list):
            query = switch_queries[sandhill].pop(swap_out_item[0])
            monitors_under_queries[query.query_id].remove(sandhill)
            for victim_sw in swap_out_item[1]:
                monitors_under_queries[query.query_id].append(victim_sw)
                switch_queries[victim_sw].append(query)

    # place all aggregator on controller's ToR
    weights[0] += args.query_number

    total_link_cost = 0
    # finally, try to move edge aggregator out if available
    for idx, monitors_under_query in enumerate(monitors_under_queries):
        # only try if edge aggregator is flooded
        if weights[0] > overall_task_count / 20:
            # we try to spread aggregator's load as long as we can
            # and try not consider load balance
            # TODO: might consider though
            aggr_candidates = []
            swap_id = -1
            for monitor in monitors_under_query:
                if len(aggr_candidates) <= 0:
                    aggr_candidates = Seeker.find_route_to_controller(monitor)
                else:
                    aggr_candidates = intersection(aggr_candidates, Seeker.find_route_to_controller(monitor))
                # if there is only one pos available (should be controller's ToR)
                # we give up searching
                if len(aggr_candidates) <= 1:
                    break

            if len(aggr_candidates) > 1:
                logging.info("Query %d got to swap out its aggregator !" % (idx))
                current_min = math.inf
                elected = 0
                for candidate in aggr_candidates:
                    if candidate != 0:
                        # find lowest weight
                        if weights[candidate] < current_min:
                            elected = candidate
                            current_min = weights[candidate]
                # swap out edge aggregator
                weights[0] -= 1
                weights[elected] += 1
                swap_id = elected

        for monitor in monitors_under_query:
            routes_back_to_controller = Seeker.find_route_to_controller(monitor)
            total_link_cost += (len(routes_back_to_controller) - 1)
            routes = [monitor] + routes_back_to_controller
            prev_node = -1
            for node in routes:
                if prev_node >= 0:
                    link_costs[prev_node][node] += 1
                prev_node = node

        if swap_id > 0:
            routes_back_to_controller = Seeker.find_route_to_controller(swap_id)
            total_link_cost -= (len(routes_back_to_controller) - 1) * (len(monitors_under_query) - 1)
            routes = [swap_id] + routes_back_to_controller
            prev_node = -1
            for node in routes:
                if prev_node >= 0:
                    link_costs[prev_node][node] -= (len(monitors_under_query) - 1)
                prev_node = node

    # dump simple debug result
    for idx, weight in enumerate(weights):
        print("Switch %d weight = %d" % (idx, weight))
    mean = sum(weights) / len(weights)
    std_err = (sum((i - mean) ** 2 for i in weights) / len(weights)) ** 0.5
    print("Overall task number = %d, avg task = %.2f, std error = %.2f" % (sum(weights), mean, std_err))
    print("link cost = %d" % (total_link_cost))
    Seeker.dump_link_info(link_costs=link_costs)
