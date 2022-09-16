#!/usr/bin/python3

from argparse import ArgumentParser
import json, random, math, logging

def distinct_random_numList_generator(pod_num:int, size:int, isGurobi:bool, isDuplicate=[]):
    numList = []
    if isGurobi:
        data = list(range(0, pod_num))
    else:
        data = list(range(1, pod_num))
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
    parser.add_argument("-p", "--pod", help="Number of pod in network topology", dest="pod", type=int, default=32)
    parser.add_argument("-q", "--query", help="Number of overall queries", dest="query", type=int, default=1000)
    parser.add_argument("-s", "--size", help="Number of pod with src pod and dst pod", dest="size", type=int, default=4)
    # mode 0 for uniform distribution, mode 1 for src-only imbalance, mode 2 for src and dst imbalance, mode 3 for all-to-all query, mode 4 for probabal mode 3
    parser.add_argument("-m", "--mode", help="Query distribution mode", dest="mode", type=int, default=0)
    parser.add_argument("-c", "--chance", help="Chance for mode 4 to apply all2all", dest="chance", type=int, default=50)
    parser.add_argument("-a", "--all2all", help="Involved pod within a all2all query", dest="inv_pods", type=int, default=5)
    # rate render no use when in mode 0
    parser.add_argument("-r", "--rate", help="Query imbalance rate (int in percentage)", dest="rate", type=int, default=50)
    parser.add_argument("-o", "--output", help="Output json location", dest="output", default="/home/lthpc/git/catchment-basin-seeker/data/queries-v3.json")
    parser.add_argument("-g", "--gurobi", help="Mode for Gurobi", dest="gurobi", type=str2bool, nargs='?', const=True, default=False)


    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    queries = []

    imbalanced_src = distinct_random_numList_generator(pod_num=args.pod, size=args.size, isGurobi=args.gurobi)
    imbalanced_dst = distinct_random_numList_generator(pod_num=args.pod, size=args.size, isGurobi=args.gurobi, isDuplicate=imbalanced_src)

    inv_pods = [0] * args.inv_pods
    prev_pods = []
    # generate arbitary number of distinct switch sets
    for podsIdx in range(args.inv_pods):
        inv_pods[podsIdx] = distinct_random_numList_generator(pod_num=args.pod, size=args.size, isGurobi=args.gurobi, isDuplicate=prev_pods)
        prev_pods.extend(inv_pods[podsIdx])
    current_qentry_num = 0
    while current_qentry_num < args.query:
        if args.mode == 3 or (args.mode == 4 and current_qentry_num < args.query - ((args.inv_pods * (args.inv_pods - 1))/2) and random.random() * 100 > args.chance):
            if args.inv_pods <= 2:
                logging.error("Invalid parameter: inv_pods when all2all semantic is applied")
                exit()
            else:
                current_qentry_num += ((args.inv_pods * (args.inv_pods - 1))/2)
                # since it is a all to all query, we have to span through every possible query combination
                for idx, srcPodsIdx in enumerate(range(args.inv_pods)):
                    for dstPodsIdx in range(idx+1, args.inv_pods):
                        queries.append({
                            "src": inv_pods[srcPodsIdx],
                            "dst": inv_pods[dstPodsIdx]
                        })
                                        
        elif args.mode == 2 and random.random() * 100 < args.rate:
            queries.append({
                "src": imbalanced_src,
                "dst": imbalanced_dst
            })
            current_qentry_num += 1
        else:
            if args.mode == 1 and random.random() * 100 < args.rate:
                src = imbalanced_src
            else:
                src = distinct_random_numList_generator(pod_num=args.pod, size=args.size, isGurobi=args.gurobi)

            dst = distinct_random_numList_generator(pod_num=args.pod, size=args.size, isGurobi=args.gurobi, isDuplicate=src)
            queries.append({
                "src": src,
                "dst": dst
            })
            current_qentry_num += 1
            
    with open(args.output, 'w') as json_file:
        json.dump(queries, json_file)
