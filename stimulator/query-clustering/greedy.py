#!/usr/bin/python3

from argparse import ArgumentParser
import json, logging, random

'''
def one_hot_encoder(inputs: list, size:int):
    ret_list = [0] * size
    for set_bit in inputs:
        ret_list[int(set_bit)] = 1
    return ret_list
'''
	

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

    batch_size = int(args.query / float(args.cluster))

    aggregated_group = []
    src_queries = []
    overall_cost = 0
    for index, query in enumerate(queries):
        if (index+1) % batch_size == 0:
            for src_query in src_queries:
                overall_cost += ((len(aggregated_group) - len(src_query))/float(args.pod))
                '''
                for entry in aggregated_group:
                    if entry not in src_query:
	                overall_cost += 1
                '''
            aggregated_group = []
            src_queries = []
        else:
            src_queries.append(query["src"])
            for entry in query["src"]:
                if entry not in aggregated_group:
                    aggregated_group.append(entry)

			
    print("Overall cost = %d" % (overall_cost))




	
		


	
