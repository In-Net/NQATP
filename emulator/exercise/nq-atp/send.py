#!/usr/bin/env python2
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
import time
import struct
from argparse import ArgumentParser

TYPE_MYMCAST = 0x1234

class Mymcast_t(Packet):
    name = "Mymcast_t "
    fields_desc = [
        ShortField("qID", 0),
        XByteField("ttl", 0),
        XByteField("hop_count", 0),
        XByteField("bitmap", 0),
         ShortField("round", 0),
         ShortField("count", 0)
]

'''
class MyAggr_t(Packet):
    name = "MyAggr_t"
    fields_desc = [
        ShortField("round", 0),
        XByteField("bitmap", 0),
        ShortField("count", 0)
]
'''

class Mybackwardroute_t(Packet):
    name = "Mybackwardroute_t "
    fields_desc = [
        XByteField("hop1", 0),
        XByteField("hop2", 0),
        XByteField("hop3", 0),
        XByteField("hop4", 0),
        XByteField("hop5", 0)
]

class Aggr_mask_number_t(Packet):
    name = "Aggr_mask_number_t "
    fields_desc = [
        XByteField("bitmap_num", 0)
]

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-e", "--entry", help="Number of entry per query", type=int, dest="entries", default=2)
    args = parser.parse_args()
    if args.entries == 2:
        repoll_times = 4
        query_start = 1
        query_end = 16
    elif args.entries == 3:
        repoll_times = 3
        query_start = 16
        query_end = 36
    elif args.entries == 4:
        repoll_times = 4
        query_start = 36
        query_end = 51
    ## ttl = ttl | (1 << 7)
    print("query start = %d, end = %d" % (query_start, query_end))
    for i in range(repoll_times):
        for qid in range(query_start, query_end):
            # pkt = Ether(type=TYPE_MYMCAST)/Mymcast_t(qID=1, ttl=132, round=i)/Mybackwardroute_t()
            pkt = Ether(type=TYPE_MYMCAST)/Mymcast_t(qID=qid, ttl=132, round=i)/Aggr_mask_number_t()
            reply = srp1(pkt, timeout=1, verbose=0)
            if not (Ether in reply):
                print("Error at qid = %d !" % (qid))
                exit()

    '''
    pkt = Ether(type=TYPE_MYMCAST)/Mymcast_t(srcID=0, dstID=1, seq=2)
    reply = srp1(pkt)
    if Ether in reply:
        print("Hi")
    '''
