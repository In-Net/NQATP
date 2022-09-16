import math, logging

'''
Find edge switches (ToR switches) along assigned routing from switch_id1
to switch_id2
- pod_scale: overall pod number in the topology, should be 2's multiples
'''
def find_edge_switch_on_path(switch_id1: int, switch_id2: int, pod_scale: int):
    if pod_scale % 2 != 0:
        logging.error("Wrong input in find_edge_switch_on_path: pod_scale should be even")
        return
    else:
        server_within_the_same_edge_sw = float(pod_scale / 2)
        # Edge switch id = ⌈server_id /  server_within_the_same_edge_sw⌉
        return [math.floor(switch_id1 / server_within_the_same_edge_sw),
            math.floor(switch_id2 / server_within_the_same_edge_sw)]

'''
Find aggr switches along assigned routing from edge_id1 to edge_id2
- pod_scale: overall pod number in the topology, should be 2's multiples
'''
def find_aggr_switch_on_path(edge_id1: int, edge_id2: int, pod_scale: int):
    if pod_scale % 2 != 0:
        logging.error("Wrong input in find_aggr_switch_on_path: pod_scale should be even")
        return
    total_edge_sw_number = pod_scale * (int(pod_scale / 2))
    aggr_sw_within_the_same_pod = int(pod_scale / 2)
    edge_sw_within_the_same_pod = int(pod_scale / 2)
    pod1 = math.floor(edge_id1 / edge_sw_within_the_same_pod)
    pod2 = math.floor(edge_id2 / edge_sw_within_the_same_pod)
    starting_aggr_id1 = total_edge_sw_number + pod1 * aggr_sw_within_the_same_pod
    starting_aggr_id2 = total_edge_sw_number + pod2 * aggr_sw_within_the_same_pod
    aggr_id1 = []
    aggr_id2 = []
    for i in range(int(edge_sw_within_the_same_pod)):
        aggr_id1.append(starting_aggr_id1 + i)
        aggr_id2.append(starting_aggr_id2 + i)
    return [aggr_id1, aggr_id2]

def find_single_aggr(edge_id:int, pod_scale:int):
    if pod_scale % 2 != 0:
        logging.error("Wrong input in find_aggr_switch_on_path: pod_scale should be even")
        return
    total_edge_sw_number = pod_scale * (int(pod_scale / 2))
    aggr_sw_within_the_same_pod = int(pod_scale / 2)
    edge_sw_within_the_same_pod = int(pod_scale / 2)
    pod_num = math.floor(edge_id / edge_sw_within_the_same_pod)
    starting_aggr_id = total_edge_sw_number + pod_num * aggr_sw_within_the_same_pod
    aggr_id = []
    for i in range(int(edge_sw_within_the_same_pod)):
        aggr_id.append(starting_aggr_id + i)
    return aggr_id
'''
Find core switches along assigned routing from switch_id1 to switch_id2
- pod_scale: overall pod number in the topology, should be 2's multiples
'''
def find_core_switch_on_path(pod_scale: int):
    if pod_scale % 2 != 0:
        logging.error("Wrong input in find_core_switch_on_path: pod_scale should be even")
        return
    total_pod_switch_number = pod_scale ** 2
    # total_server_number = (pod_scale ** 2) / 2
    total_core_switch_number = (pod_scale / 2) ** 2
    core_id = []
    for i in range(int(total_core_switch_number)):
        core_id.append(total_pod_switch_number + i)
    return core_id

def find_single_core(aggr_id:int, pod_scale:int):
    if pod_scale % 2 != 0:
        logging.error("Wrong input in find_core_switch_on_path: pod_scale should be even")
        return
    total_pod_switch_number = pod_scale ** 2
    total_edge_sw_number = pod_scale * (int(pod_scale / 2))
    aggr_sw_within_the_same_pod = int(pod_scale / 2)
    core_sw_within_the_same_pod = int(pod_scale / 2)
    core_num = (aggr_id - total_edge_sw_number) % aggr_sw_within_the_same_pod
    starting_core_id = total_pod_switch_number + core_num * core_sw_within_the_same_pod
    core_id = []
    for i in range(core_sw_within_the_same_pod):
        core_id.append(starting_core_id + i)
    return core_id

'''
Assume controller being host 1
Also, how source routing did is one concern
'''
def find_route_to_controller(src_addr_id: int):
    if src_addr_id == 0:
        print("Monitor can't be set on controller's ToR !")
        return []
    elif src_addr_id == 1:
        return [9, 0]
    elif src_addr_id == 2:
        return [10, 16, 8, 0]
    elif src_addr_id == 3:
        return [11, 18, 9, 0]
    elif src_addr_id == 4:
        return [12, 17, 8, 0]
    elif src_addr_id == 5:
        return [13, 19, 9, 0]
    elif src_addr_id == 6:
        return [14, 16, 8, 0]
    elif src_addr_id == 7:
        return [15, 18, 9, 0]
    elif src_addr_id == 8:
        return [12, 17, 8, 0]
    elif src_addr_id == 9:
        return [0]
    elif src_addr_id == 10:
        return [17, 8, 0]
    elif src_addr_id == 11:
        return [19, 9, 0]
    elif src_addr_id == 12:
        return [16, 8, 0]
    elif src_addr_id == 13:
        return [18, 9, 0]
    elif src_addr_id == 14:
        return [17, 8, 0]
    elif src_addr_id == 15:
        return [19, 9, 9]
    elif src_addr_id == 16:
        return [8, 0]
    elif src_addr_id == 17:
        return [8, 0]
    elif src_addr_id == 18:
        return [9, 0]
    elif src_addr_id == 19:
        return [9, 0]
    else:
        print("Error: unmatched src addr id in finding route back to controller")
        return []

def dump_link_info(link_costs:list):
    print("########    LINK STATUS    ########")
    print("#####       EDGE - AGGR        ####")
    print("s0-s8 -> %d" % (link_costs[0][8] + link_costs[8][0]))
    print("s0-s9 -> %d" % (link_costs[0][9] + link_costs[9][0]))
    print("s1-s8 -> %d" % (link_costs[1][8] + link_costs[8][1]))
    print("s1-s9 -> %d" % (link_costs[1][9] + link_costs[9][1]))
    print("s2-s10 -> %d" % (link_costs[2][10] + link_costs[10][2]))
    print("s2-s11 -> %d" % (link_costs[2][11] + link_costs[11][2]))
    print("s3-s10 -> %d" % (link_costs[3][10] + link_costs[10][3]))
    print("s3-s11 -> %d" % (link_costs[3][11] + link_costs[11][3]))
    print("s4-s12 -> %d" % (link_costs[4][12] + link_costs[12][4]))
    print("s4-s13 -> %d" % (link_costs[4][13] + link_costs[13][4]))
    print("s5-s12 -> %d" % (link_costs[5][12] + link_costs[12][5]))
    print("s5-s13 -> %d" % (link_costs[5][13] + link_costs[13][5]))
    print("s6-s14 -> %d" % (link_costs[6][14] + link_costs[14][6]))
    print("s6-s15 -> %d" % (link_costs[6][15] + link_costs[15][6]))
    print("s7-s14 -> %d" % (link_costs[7][14] + link_costs[14][7]))
    print("s7-s15 -> %d" % (link_costs[7][15] + link_costs[15][7]))
    print("#####       AGGR - CORE        ####")
    print("s8-s16 -> %d" % (link_costs[8][16] + link_costs[16][8]))
    print("s8-s17 -> %d" % (link_costs[8][17] + link_costs[17][8]))
    print("s9-s18 -> %d" % (link_costs[9][18] + link_costs[18][9]))
    print("s9-s19 -> %d" % (link_costs[9][19] + link_costs[19][9]))
    print("s10-s16 -> %d" % (link_costs[10][16] + link_costs[16][10]))
    print("s10-s17 -> %d" % (link_costs[10][17] + link_costs[17][10]))
    print("s11-s18 -> %d" % (link_costs[11][18] + link_costs[18][11]))
    print("s11-s19 -> %d" % (link_costs[11][19] + link_costs[19][11]))
    print("s12-s16 -> %d" % (link_costs[12][16] + link_costs[16][12]))
    print("s12-s17 -> %d" % (link_costs[12][17] + link_costs[17][12]))
    print("s13-s18 -> %d" % (link_costs[13][18] + link_costs[18][13]))
    print("s13-s19 -> %d" % (link_costs[13][19] + link_costs[19][13]))
    print("s14-s16 -> %d" % (link_costs[14][16] + link_costs[16][14]))
    print("s14-s17 -> %d" % (link_costs[14][17] + link_costs[17][14]))
    print("s15-s18 -> %d" % (link_costs[15][18] + link_costs[18][15]))
    print("s15-s19 -> %d" % (link_costs[15][19] + link_costs[19][15]))

if __name__ == "__main__":
    edge_sw1, edge_sw2 = find_edge_switch_on_path(switch_id1=1, switch_id2=5, pod_scale=4)
    aggr_sw1, aggr_sw2 = find_aggr_switch_on_path(edge_id1=edge_sw1, edge_id2=edge_sw2, pod_scale=4)
    core_sw = find_core_switch_on_path(pod_scale=4)
    print(edge_sw1)
    print(edge_sw2)
    print(aggr_sw1)
    print(aggr_sw2)
    print(core_sw)
