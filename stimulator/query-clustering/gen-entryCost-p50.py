#!/usr/bin/python3

import json, logging, random
	

if __name__ == "__main__":
    switch_load_wi_cluster = [0] * 256
    switch_load_wi_cluster = [0] * 256
    # With cluster
    sw_in_pod = 16
    

    # Without cluster

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
