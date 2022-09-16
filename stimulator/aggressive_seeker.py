from argparse import ArgumentParser
import json, logging

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

def create_env():
    weights = [0] * 20
    queries = [0] * 20
    for i in range(20):
        queries[i] = []
    return weights, queries

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-r", "--read", help="Query input file location", dest="query_location", default="./data/queries.json")
    parser.add_argument("-n", "--number", help="Total query number", dest="query_number", type=int, default=250)
    parser.add_argument("-a", "--aggregator", help="Also deploy aggregator", type=str2bool, nargs='?',
const=True, default=True, dest="deploy_aggr")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    weights, switch_queries = create_env()

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
        if weights[sandhill] <= 0:
            break
        victim_available = True
        # [(entry id, [sw_id1, ...]), (...)]
        swap_out_list = []
        for index, switch_query in enumerate(switch_queries[sandhill]):
            # we only push down sandhill once it is over average
            avg_task_count = overall_task_count / 20
            if victim_available and (weights[sandhill] > avg_task_count):
                victim_sws = []
                aggr_sws = Seeker.find_single_aggr(edge_id=sandhill, pod_scale=4)
                if ((weights[aggr_sws[0]] + weights[aggr_sws[1]]) / 2) < avg_task_count:
                    victim_sws += aggr_sws
                else:
                    for aggr_sw in aggr_sws:
                        if weights[aggr_sw] < avg_task_count:
                            victim_sws.append(aggr_sw)
                        else:
                            # aggr sw also has no room for new queries
                            # ask core sw to adopt queries left
                            core_sws = Seeker.find_single_core(aggr_id=aggr_sw, pod_scale=4)
                            core_cost = (weights[core_sws[0]] + weights[core_sws[1]]) / 2
                            if core_cost < avg_task_count:
                                victim_sws += core_sws
                            else:
                                victim_available = False
                                break
                if victim_available:
                    # put the swap-out relationship into a waiting list
                    # we shouldn't modify the list in its own iterator
                    swap_out_list.append((index, victim_sws))
                    # however, we should faithfully update victim weight at real time
                    for victim_sw in victim_sws:
                        weights[victim_sw] += 1
                    overall_task_count += len(victim_sws) - 1
                    weights[sandhill] -= 1
            else:
                # we make the sandhill not greater than avg
                # or we couldn't find any victim to lower the sandhill
                # move on to next edge monitor
                break
        # actually transfer task from edge monitor to victom sws
        for swap_out_item in reversed(swap_out_list):
            query = switch_queries[sandhill].pop(swap_out_item[0])
            monitors_under_queries[query.query_id].remove(sandhill)
            for victim_sw in swap_out_item[1]:
                monitors_under_queries[query.query_id].append(victim_sw)
                switch_queries[victim_sw].append(query)

    # finally, put all aggregator on controller's ToR
    weights[0] += args.query_number

    # dump simple debug result
    for idx, weight in enumerate(weights):
        print("Switch %d weight = %d" % (idx, weight))
    mean = sum(weights) / len(weights)
    std_err = (sum((i - mean) ** 2 for i in weights) / len(weights)) ** 0.5
    print("Overall task number = %d, avg task = %.2f, std error = %.2f" % (sum(weights), mean, std_err))
