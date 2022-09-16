#!/usr/bin/python3

from argparse import ArgumentParser
import json, logging, csv


def link_interpreter(src: int, dst: int, pod_size: int):
    # determine if it is a link between core and aggr
    if src >= (pod_size ** 2):
    # src is core while dst being aggr
        src_core_idx = src - pod_size ** 2
        dst_pod = dst / pod_size
        dst_aggr_idx = dst % pod_size
        if dst_aggr_idx < (pod_size/2):
            logging.warning("Interprete link with core src but with edge dst")
            return -1
        elif dst >= (pod_size ** 2):
            # dst is core while src being aggr
            dst_core_idx = dst - pod_size ** 2
            src_pod = src / pod_size
            src_aggr_idx = src % pod_size
            if src_aggr_idx < (pod_size/2):
                logging.warning("Interprete link with core dst but with edge src")
                return -1
            else: 
                # both src and dst are within pod
                logging.warning("Unimplemented!")


def writer(data_type, input_data, isFirst: bool):
    with open("emulated_result.csv", "a") as csvfile:
        writer = csv.writer(csvfile)
        if isFirst:
            writer.writerow(['pkt_num', 'type'])
        for data in input_data:
            writer.writerow([data, data_type])

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--pod", help="Number of pod in network topology", dest="pod", type=int, default=32)
    parser.add_argument("-q", "--query", help="Number of overall queries", dest="query", type=int, default=1000)
    parser.add_argument("-s", "--size", help="Number of pod with src pod and dst pod", dest="size", type=int, default=4)
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    # edge <-> aggr switch: (k^3) / 4
    # aggr <-> core switch: (k^3) / 4

    link = [0] * int((args.pod ** 3) / 2)

    # read query from data
    with open("/home/lthpc/git/catchment-basin-seeker/data/queries-v3.json") as inputfile:
        unparsed_queries = inputfile.read()

    queries = json.loads(unparsed_queries)

    # SNMP part evaluation
    # link usage from collector to core switch is fixed no matter the query is 

    for i in range(int(args.pod / 2)):
        link[i] += (args.query * 2 * args.size)

    layer_link_num = int((args.pod ** 3)/4)
    pod_link_num = int((args.pod ** 2)/4)

    starting_idx = layer_link_num
    for i in range(pod_link_num):
        link[starting_idx + i] += (args.query * args.size * 4 / args.pod)

    for query in queries:
        pods = query["src"]
        for pod in pods:
	    # increment edge-aggr link usage
            starting_idx = pod * pod_link_num
            for i in range(pod_link_num):
                link[starting_idx + i] += 2
            
            # increment aggr-core link usage
            starting_idx = layer_link_num + pod * pod_link_num
            for i in range(pod_link_num):
                link[starting_idx + i] += (4 / args.pod)

    # dump results
    writer(data_type="SNMP", input_data=link, isFirst=True)

    link = [0] * int((args.pod ** 3) / 2)
    # MonAggr part
    # worst case: only a single global mcast tree
    for i in range(int(args.pod / 2)):
        link[i] += (args.query * 4 / args.pod)

    starting_idx = layer_link_num
    for i in range(pod_link_num):
        link[starting_idx + i] += (args.query * args.size * 8 / (args.pod ** 2))


    # we assume we adopt a single multicast tree
    for i in range(1, args.pod):
        starting_idx = i * pod_link_num
        for j in range(pod_link_num):
            link[starting_idx + j] += (args.query * 2 / args.pod)
        starting_idx = layer_link_num + i * pod_link_num
        for j in range(pod_link_num):
            link[starting_idx + j] += (args.query * 4 / (args.pod ** 2))

    for query in queries:
        pods = query["src"]
        for pod in pods:
            # increment edge-aggr link usage
            starting_idx = pod * pod_link_num
            for i in range(pod_link_num):
                link[starting_idx + i] += (2 / args.pod)
            # increment aggr-core link usage
            starting_idx = layer_link_num + pod * pod_link_num
            for i in range(pod_link_num):
                link[starting_idx + i] += (4 / (args.pod ** 2))

    writer(data_type="Worst-MonAggr", input_data=link, isFirst=False)
    link = [0] * int((args.pod ** 3) / 2)
    # best case: each query has its own mcast tree, no extra flooding
    for i in range(int(args.pod / 2)):
        link[i] += (args.query * 4 / args.pod)

    starting_idx = layer_link_num
    for i in range(pod_link_num):
        link[starting_idx + i] += (args.query * args.size * 8 / (args.pod ** 2))

    for query in queries:
        pods = query["src"]
        for pod in pods:
            # increment edge-aggr link usage
            starting_idx = pod * pod_link_num
            for i in range(pod_link_num):
                link[starting_idx + i] += (4 / args.pod)
            # increment aggr-core link usage
            starting_idx = layer_link_num + pod * pod_link_num
            for i in range(pod_link_num):
                link[starting_idx + i] += (8 / (args.pod ** 2))

    writer(data_type="Best-MonAggr", input_data=link, isFirst=False)
