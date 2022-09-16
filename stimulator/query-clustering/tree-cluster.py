#!/usr/bin/python3

from argparse import ArgumentParser
from sklearn.cluster import KMeans
from scipy.spatial import distance
import json, logging, csv

def one_hot_encoder(inputs: list, size:int):
    ret_list = [0] * size
    for set_bit in inputs:
        ret_list[int(set_bit)] = 1
    return ret_list
	
def writer(d_type, input_data, isFirst: bool):
    with open("control-entry-usage.csv", "a") as csvfile:
        writer = csv.writer(csvfile)
        if isFirst:
            writer.writerow(["pkt_num", "type"])
        for data in input_data:
            writer.writerow([data, d_type])

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

    flat_queries = []
    for query in queries:
        flat_queries.append(one_hot_encoder(inputs=query["src"], size=args.pod))

    logging.info("Done preprocess.")

    kmeans = KMeans(n_clusters=args.cluster)
    kmeans.fit(flat_queries)
    # print(kmeans.labels_)
    # y_kmeans = kmeans.predict(X)

    logging.info("Done clustering.")

    # Evaluate objective performance
    products = [0] * args.cluster
    sources = [0] * args.cluster
    for i in range(args.cluster):
        products[i] = []
        sources[i] = []
    for index, label in enumerate(kmeans.labels_):
        if not products[label]:
            products[label] = flat_queries[index]
        else:
            result = list(a|b for a,b in zip(products[label], flat_queries[index]))
            products[label] = result
        sources[label].append(index)

    cost = 0
    for i in range(args.cluster):
        for idx in sources[i]:
            cost += distance.hamming(products[i], flat_queries[idx])
			
    print("Overall Bandwidht cost = %d" % (cost))

    switch_load_wi_cluster = [0] * 512
    switch_load_wo_cluster = [0] * 512
    sw_in_pod = 16

    # print("Len of flat query: %d" % (len(flat_queries)))

    for idx in range(8):
        switch_load_wi_cluster[idx] += (len(sources) * 8)
        switch_load_wi_cluster[256+idx] += len(sources)
        switch_load_wo_cluster[idx] += (args.query * 8)
        switch_load_wo_cluster[256+idx] += args.query
    # With cluster
    for product in products:
        for index, pod in enumerate(product):
            if (pod > 0):
                for aggr_idx in range(8):
                    switch_load_wi_cluster[index*8 + aggr_idx] += 1

    # Without cluster
    for source in flat_queries:
        for index, pod in enumerate(source):
            if (pod > 0):
                for aggr_idx in range(8):
                    switch_load_wo_cluster[index*8 + aggr_idx] += 1

    '''
    avg_wo_cluster = sum(switch_load_wo_cluster) / float(len(switch_load_wo_cluster))
    avg_wi_cluster = sum(switch_load_wi_cluster) / float(len(switch_load_wi_cluster))
    print("Avg wo cluster = %d, wi cluster = %d" % (avg_wo_cluster, avg_wi_cluster))
    '''

    writer(d_type="W/I Cluster", input_data=switch_load_wi_cluster, isFirst=True)
    writer(d_type="W/O Cluster", input_data=switch_load_wo_cluster, isFirst=False)




	
		


	
