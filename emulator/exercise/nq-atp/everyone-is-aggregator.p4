/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_MyMcast = 0x1234;

#define BITMAP_SIZE 8
#define QUERY_BIT 16
#define TTL_BIT 7
#define QUERY_SIZE 65536
#define MAX_HOPS 5

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header backward_route_t {
    // bos is a signal that indicates it is the last route entry
    bit<1> bos;
    bit<7> nexthop;
}

header aggr_mask_number_t {
    bit<BITMAP_SIZE> bitmap_num;
}

header aggr_mask_t {
    bit<BITMAP_SIZE> bitmap;
}

header mymcast_t {
    bit<16> qID;
    // 0 for response, 1 for request
    bit<1> direction;
    bit <TTL_BIT> ttl;
    bit<8> hop_count;
    bit<BITMAP_SIZE> bitmap;
    bit<16> round;
    bit<16> count;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

struct parser_metadata_t {
    bit<BITMAP_SIZE> remaining_mask_num;
}

struct metadata {
    bit<16> tmpID;
    // monitor use this to buffer bitmap, aggregator use this to determine
    // forward threshold
    bit<BITMAP_SIZE> shared_bitmap;
    bit<16> last_round;
    bit<BITMAP_SIZE> intermediate_bitmap;
    bit<16> intermediate_count;
    bit<BITMAP_SIZE> downsteam_vine_bitmap;
    bit<BITMAP_SIZE> core_bitmap;
    bit<BITMAP_SIZE> upstream_vine_bitmap;
    bit<BITMAP_SIZE> upstream_leaf_bitmap;
    bit<16> mcast_grp;
    parser_metadata_t parser_metadata;
}

struct headers {
    ethernet_t    ethernet;
    mymcast_t    mymcast;
    backward_route_t[MAX_HOPS]    backward_route;
    aggr_mask_number_t    aggr_mask_number;
    aggr_mask_t[MAX_HOPS]    aggr_mask;
    ipv4_t    ipv4;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {


    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_MyMcast: parse_mymcast;
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_mymcast {
        packet.extract(hdr.mymcast);
        transition select(hdr.mymcast.hop_count) {
            0: parse_aggr_mask_number;
            default: parse_backward_routes;
        }
    }

    state parse_backward_routes {
        packet.extract(hdr.backward_route.next);
        transition select(hdr.backward_route.last.bos) {
            1: parse_aggr_mask_number;
            default: parse_backward_routes;
        }
    }

    state parse_aggr_mask_number {
        packet.extract(hdr.aggr_mask_number);
        meta.parser_metadata.remaining_mask_num = hdr.aggr_mask_number.bitmap_num;
        transition select(hdr.aggr_mask_number.bitmap_num) {
            0: accept;
            default: parse_aggr_masks;
        }
    }

    state parse_aggr_masks {
        packet.extract(hdr.aggr_mask.next);
        meta.parser_metadata.remaining_mask_num = meta.parser_metadata.remaining_mask_num - 1;
        transition select(meta.parser_metadata.remaining_mask_num) {
            0: accept;
            default: parse_aggr_masks;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition accept;
    }
}


/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    register <bit<BITMAP_SIZE>> (QUERY_SIZE) bitmaps;
    register <bit<16>> (QUERY_SIZE) last_rounds;
    register <bit<16>> (QUERY_SIZE) counts;

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    // mark monitor only, others (by default) will be aggregator
    // TODO: this is under the condition that "all monitors are on ToR" (so that there will be 4 hops)
    action mark_character(bit<BITMAP_SIZE> bitmap, bit<BITMAP_SIZE> downsteam_vine_bitmap, 
                                                    bit<BITMAP_SIZE> core_bitmap, bit<BITMAP_SIZE> upstream_vine_bitmap, bit<BITMAP_SIZE> upstream_leaf_bitmap) {
        hdr.mymcast.bitmap = bitmap;
        hdr.aggr_mask_number.bitmap_num = 4;
        hdr.aggr_mask.push_front(1);
        hdr.aggr_mask[0].setValid();
        hdr.aggr_mask[0].bitmap = upstream_leaf_bitmap;

        hdr.aggr_mask.push_front(1);
        hdr.aggr_mask[0].setValid();
        hdr.aggr_mask[0].bitmap = upstream_vine_bitmap;

        hdr.aggr_mask.push_front(1);
        hdr.aggr_mask[0].setValid();
        hdr.aggr_mask[0].bitmap = core_bitmap;

        hdr.aggr_mask.push_front(1);
        hdr.aggr_mask[0].setValid();
        hdr.aggr_mask[0].bitmap = downsteam_vine_bitmap;
    }

    table check_my_char {
        key = {
            hdr.mymcast.qID: exact;
        }
        actions = {
            mark_character;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    apply {
        if (hdr.ipv4.isValid()) {
            ipv4_lpm.apply();
        } else if (hdr.mymcast.isValid()) {
            if (check_my_char.apply().hit) {
                // if I am a monitor
                standard_metadata.egress_spec=standard_metadata.ingress_port;
                hdr.mymcast.direction = 0;
                hdr.mymcast.count = 2;
            } else {
                // then I must be an "aggregator"
                if (hdr.mymcast.direction == 1) {
                    if (hdr.mymcast.ttl > 0) {
                        // TODO: if we want multiple spanning tree, specify here
                        meta.mcast_grp = (hdr.mymcast.qID & 3) + 1;
                        standard_metadata.mcast_grp = meta.mcast_grp;
                        hdr.mymcast.ttl = hdr.mymcast.ttl - 1;
                        // Also record ingress port for later responses' backward  routes
                        hdr.mymcast.hop_count = hdr.mymcast.hop_count + 1;
                        hdr.backward_route.push_front(1);
                        hdr.backward_route[0].setValid();
                        if (hdr.mymcast.hop_count == 1) {
                            hdr.backward_route[0].bos = 1;
                        } else {
                            hdr.backward_route[0].bos = 0;
                        }
                        hdr.backward_route[0].nexthop = (bit<7>)standard_metadata.ingress_port;
                    } else {
                        drop();
                    }
                } else {
                    // this is the response direction
                    // route backward as response
                    standard_metadata.egress_spec = (egressSpec_t)hdr.backward_route[0].nexthop;
                    hdr.backward_route.pop_front(1);
                    hdr.mymcast.hop_count = hdr.mymcast.hop_count - 1;

                    // read aggregation bitmap
                    meta.shared_bitmap = hdr.aggr_mask[0].bitmap;
                    hdr.aggr_mask.pop_front(1);
                    hdr.aggr_mask_number.bitmap_num = hdr.aggr_mask_number.bitmap_num - 1;

                    if (hdr.mymcast.bitmap != meta.shared_bitmap) {
                        // we only aggregates those in need, forward the rest
                        last_rounds.read(meta.last_round, (bit<32>)hdr.mymcast.qID);
                        bitmaps.read(meta.intermediate_bitmap, (bit<32>)hdr.mymcast.qID);
                        counts.read(meta.intermediate_count, (bit<32>)hdr.mymcast.qID);
                        meta.intermediate_bitmap = meta.intermediate_bitmap | hdr.mymcast.bitmap;
                        meta.intermediate_count = meta.intermediate_count + hdr.mymcast.count;
                        if (meta.last_round > hdr.mymcast.round) {
                            drop();
                        } else  {
                            if (meta.last_round < hdr.mymcast.round) {
                                last_rounds.write((bit<32>)hdr.mymcast.qID, hdr.mymcast.round);
                                meta.intermediate_count = hdr.mymcast.count;
                                meta.intermediate_bitmap = hdr.mymcast.bitmap;
                            }
                            bitmaps.write((bit<32>)hdr.mymcast.qID, meta.intermediate_bitmap);
                            counts.write((bit<32>)hdr.mymcast.qID, meta.intermediate_count);
                            if (meta.intermediate_bitmap == meta.shared_bitmap) {
                                hdr.mymcast.bitmap = meta.intermediate_bitmap;
                                hdr.mymcast.count = meta.intermediate_count;
                            } else {
                                drop();
                            }
                        }
                    }
                }
            }
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {  }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.mymcast);
        packet.emit(hdr.backward_route);
        packet.emit(hdr.aggr_mask_number);
        packet.emit(hdr.aggr_mask);
        packet.emit(hdr.ipv4);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
