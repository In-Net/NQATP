#!/usr/bin/python3
'''
Generate various input query pattern,
include different distribution
pattern 0:  Normal pattern, random distribution (default)
pattern 1:  90% queries are communicate within the same pod pair
                      Other 10% random distributed
Notice that this script is currently able to handle pod = 4
'''

from argparse import ArgumentParser
import json, random, math, logging

def gen_uniform_random_queries(queries:list, number:int, entry_per_query:int, host:int):
    for query_idx in range(number):
        for entry_idx in range(entry_per_query):
            # we can't have the src/dst in the same pod
            src = random.randint(0, host-1)
            src_pod = math.floor(src / 4)
            dst = random.randint(0, host-1)
            dst_pod = math.floor(dst / 4)
            while dst_pod == src_pod:
                dst = random.randint(0, host-1)
                dst_pod = math.floor(dst / 4)
            queries.append({
                "query_id": query_idx,
                "src_host_id": src,
                "dst_host_id": dst
            })

def gen_centrialized_queries(queries:list, number:int, entry_per_query:int, host:int, percentage: float):
    # we avoid using the first pod as centrialized factor, since it also responsible for controller
    main_src_pod = random.randint(0, 3)
    main_dst_pod = random.randint(0, 3)
    while main_src_pod == main_dst_pod:
        main_dst_pod = random.randint(0, 3)

    logging.info("Main src pod: %d" % (main_src_pod))
    logging.info("Main dst pod: %d" % (main_dst_pod))

    main_num = int(number * percentage / 100.0)
    remain_num = number - main_num

    logging.info("Main num = %d, remains %d" % (main_num, remain_num))

    gen_uniform_random_queries(queries=queries, number=remain_num,
        entry_per_query=entry_per_query, host=host)

    for main_query_idx in range(main_num):
        for entry_idx in range(entry_per_query):
            src_shift = random.randint(0, 3)
            dst_shift = random.randint(0, 3)
            queries.append({
                "query_id": remain_num+ main_query_idx,
                "src_host_id": main_src_pod * 4 + src_shift,
                "dst_host_id": main_dst_pod * 4 + dst_shift
            })

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def restricted_float(x):
    try:
        x = float(x)
    except ValueError:
        raise argparse.ArgumentTypeError("%r not a floating-point literal" % (x,))

    if x < 0.0 or x > 1.0:
        raise argparse.ArgumentTypeError("%r not in range [0.0, 1.0]"%(x,))
    return x

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-m", "--mode", help="Query pattern mode", dest="mode", type=int, default=0)
    parser.add_argument("-n", "--number", help="Total query number", dest="number", type=int, default=250)
    parser.add_argument("-e", "--entry", help="Entry number per query", dest="entry", type=int, default=4)
    parser.add_argument("--host", help="Number of hosts", dest="host", type=int, default=16)
    parser.add_argument("-o", "--output", help="Output json location", dest="output", default="/home/lthpc/git/catchment-basin-seeker/data/queries.json")
    parser.add_argument("-s", "--shuffle", help="Randomly shuffle output json", type=str2bool, nargs='?',
const=True, default=False, dest="shuffle")
    parser.add_argument("-p", "--parameter", help="Supplemental optional parameter for different modes", type=int, default=80, dest="parameter")


    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    queries = []

    if args.mode == 0:
        gen_uniform_random_queries(queries=queries, number=args.number, entry_per_query=args.entry, host=args.host)
    elif args.mode == 1:
        gen_centrialized_queries(queries=queries, number=args.number, entry_per_query=args.entry, host=args.host, percentage=args.parameter)
    else:
        logging.error("Modes other than 0 or 1 is not supported yet !")
        exit()

    if args.shuffle:
        random.shuffle(queries)

    with open(args.output, 'w') as json_file:
        json.dump(queries, json_file)
