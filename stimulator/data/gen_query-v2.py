#!/usr/bin/python3

from argparse import ArgumentParser
import json, random, math, logging

def distinct_random_numList_generator(pod_num:int, size:int, isDuplicate=[]):
    numList = []
    data = list(range(0, pod_num))
    random.shuffle(data)
    
    for item in data:
        if item not in isDuplicate:
            numList.append(item)
        if len(numList) >= size:
            break

    return numList


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
    parser.add_argument("-p", "--pod", help="Number of pod in network topology", dest="pod", type=int, default=30)
    parser.add_argument("-q", "--query", help="Number of overall queries", dest="query", type=int, default=1000)
    parser.add_argument("-s", "--size", help="Number of pod with src pod and dst pod", dest="size", type=int, default=4)
    # mode 0 for uniform distribution, mode 1 for src-only imbalance, mode 2 for src and dst imbalance
    parser.add_argument("-m", "--mode", help="Query distribution mode", dest="mode", type=int, default=0)
    # rate render no use when in mode 0
    parser.add_argument("-r", "--rate", help="Query imbalance rate (int in percentage)", dest="rate", type=int, default=50)
    parser.add_argument("-o", "--output", help="Output json location", dest="output", default="/home/lthpc/git/catchment-basin-seeker/data/queries-v2.json")


    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    queries = []

    imbalanced_src = distinct_random_numList_generator(pod_num=args.pod, size=args.size)
    imbalanced_dst = distinct_random_numList_generator(pod_num=args.pod, size=args.size, isDuplicate=imbalanced_src)
    for _ in range(args.query):
        if args.mode == 2 and random.random() * 100 < args.rate:
            queries.append({
                "src": imbalanced_src,
                "dst": imbalanced_dst
            })
        else:
            if args.mode == 1 and random.random() * 100 < args.rate:
                src = imbalanced_src
            else:
                src = distinct_random_numList_generator(pod_num=args.pod, size=args.size)

            dst = distinct_random_numList_generator(pod_num=args.pod, size=args.size, isDuplicate=src)
            queries.append({
                "src": src,
                "dst": dst
            })
            
    with open(args.output, 'w') as json_file:
        json.dump(queries, json_file)
