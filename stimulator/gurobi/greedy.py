#!/usr/bin/python3

from argparse import ArgumentParser
from sklearn.cluster import KMeans
from scipy.spatial import distance
import json, logging, random

def one_hot_encoder(inputs: list, size:int):
    ret_list = [0] * size
    for set_bit in inputs:
        ret_list[int(set_bit)] = 1
    return ret_list
	

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--pod", help="Number of pod in network topology", dest="pod", type=int, default=32)
    parser.add_argument("-q", "--query", help="Number of overall queries", dest="query", type=int, default=1000)
    parser.add_argument("-c", "--cluster", help="Number of query cluster", dest="cluster", type=int, default=20)

    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)
        
    with open("/home/lthpc/git/catchment-basin-seeker/data/queries-v3.json") as input:
        unparsed_queries = input.read()

    # TODO: ADD support for multiple imbalanced sources in gen_query module
    queries = json.loads(unparsed_queries)

    random.shuffle(queries)

    logging.info("Done preprocess.")

    switch_load = [0] * args.pod

    for query in queries:
        # estimate cost in each side
        src_cost, dst_cost = 0, 0
        for src_entry in query["src"]:
            src_cost += switch_load[src_entry]
        for dst_entry in query["dst"]:
            dst_cost += switch_load[dst_entry]
        monitor_placement = []
        if src_cost > dst_cost:
            monitor_placement = query["src"]
        elif src_cost < dst_cost:
            monitor_placement = query["dst"]
        else:
            if random.random() < 0.5:
                monitor_placement = query["src"]
            else: 
                monitor_placement = query["dst"]

        for entry in monitor_placement:
            switch_load[entry] += 1

    logging.info("Done Load Balance.")
    '''
    for i in range(32):
        print(switch_load[i])
    '''
    
    # Evaluate objective performance
    avg_switch_load = sum(switch_load) / len(switch_load)
    variance = (sum((item - avg_switch_load) ** 2 for item in switch_load) / len(switch_load)) ** 0.5
			
    print("Avg switch load = %f, std_err = %f" % (avg_switch_load, variance))




	
		


	
