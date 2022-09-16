/* -*- P4_14 -*- */

#ifdef __TARGET_TOFINO__
#include <tofino/constants.p4>
#include <tofino/intrinsic_metadata.p4>
#include <tofino/primitives.p4>
#if !defined(BMV2TOFINO)
#include <tofino/stateful_alu_blackbox.p4>
#endif
#else
#error This program is intended to compile for Tofino P4 architecture only
#endif

#define TTL_BIT 8
#define BITMAP_BIT 8
#define COUNT_WIDTH 16
#define SEQ_WIDTH 16
#define QUERY_WIDTH 16
#define INSTANCE_SIZE 65536

/*************************************************************************
 ***********************  H E A D E R S  *********************************
 *************************************************************************/
header_type ethernet_t {
    fields {
        dstAddr   : 48;
        srcAddr   : 48;
        etherType : 16;
    }
}

header_type ipv4_t {
    fields {
        version        : 4;
        ihl            : 4;
        diffserv       : 8;
        totalLen       : 16;
        identification : 16;
        flags          : 3;
        fragOffset     : 13;
        ttl            : 8;
        protocol       : 8;
        hdrChecksum    : 16;
        srcAddr        : 32;
        dstAddr        : 32;
    }
}

header_type myforward_t {
    fields {
        srcID  : QUERY_WIDTH;
        dstID  :  QUERY_WIDTH;
        ttl : TTL_BIT;
        bitmap : BITMAP_BIT;
        seq  : SEQ_WIDTH;
        flowcount: COUNT_WIDTH;
        hop_cnt  :  8;
    }
}

header_type backward_route_t {
    fields {
        bos  : 7;
        nexthop: 9;
    }
}

/*************************************************************************
 ***********************  M E T A D A T A  *******************************
 *************************************************************************/

header_type mdata_t {
    fields {
        last_seq : SEQ_WIDTH;
        seq_order: SEQ_WIDTH;
        order8: 8;
        flowcount: COUNT_WIDTH;
        aggr_bitmap: BITMAP_BIT;
        aggr_complete_flag: BITMAP_BIT;
    }
}

metadata mdata_t mdata;

/*************************************************************************
***********************  P A R S E R  ***********************************
*************************************************************************/

header ethernet_t ethernet;
header ipv4_t ipv4;
header myforward_t myforward;
header backward_route_t backward_route[5];

parser start {
    extract(ethernet);
    return select(ethernet.etherType) {
        0x0800 : parse_ipv4;
        0x1234 : parse_myforward;
        default: ingress;
    }
}

parser parse_myforward {
    extract(myforward);
    return select(myforward.hop_cnt) {
        0: ingress;
        default: parse_backward_routes;
    }
}

parser parse_backward_routes {
    extract(backward_route[next]);
    return select(latest.bos) {
        1: ingress;
        default: parse_backward_routes;
    }
}

parser parse_ipv4 {
    extract(ipv4);
    return ingress;
}

/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

 register last_seqs {
     width: SEQ_WIDTH;
     instance_count: INSTANCE_SIZE;
 }

 register aggr_bitmaps {
     width : BITMAP_BIT;
     instance_count : INSTANCE_SIZE;
 }

 register counts {
    width : COUNT_WIDTH;
    instance_count : INSTANCE_SIZE;
 }

action do_drop_packet() {
    drop();
}

table drop_packet {
    actions {
        do_drop_packet;
    }
    default_action : do_drop_packet();
    size: 1;
}

action do_gather_aggregation_result() {
    modify_field(myforward.flowcount, mdata.flowcount);
    modify_field(ig_intr_md_for_tm.ucast_egress_port, backward_route[0].nexthop);
    pop(backward_route, 1);
    add_to_field(myforward.hop_cnt, -1);
}

table gather_aggregation_result {
    actions {
        do_gather_aggregation_result;
    }
    default_action : do_gather_aggregation_result();
    size: 1;
}

action do_check_aggregation_completion(bitmap) {
    bit_xor(mdata.aggr_complete_flag, bitmap, mdata.aggr_bitmap);
}

table check_aggregation_completion {
    reads {
        myforward.srcID: exact;
    }
    actions {
        do_check_aggregation_completion;
    }
    default_action : do_check_aggregation_completion(1);
    size: 65536;
}

blackbox stateful_alu exec_update_monitor_count {
    reg: aggr_bitmaps;

    condition_lo: mdata.order8 > 0;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: 1;
    update_lo_2_predicate: not condition_lo;
    update_lo_2_value: register_lo + 1;

    output_predicate: true;
    output_dst: mdata.aggr_bitmap;
    output_value: alu_lo;
}

action do_update_monitor_count() {
    exec_update_monitor_count.execute_stateful_alu(myforward.srcID);
}

table update_monitor_count {
    actions {
        do_update_monitor_count;
    }
    default_action : do_update_monitor_count();
    size: 1;
}

blackbox stateful_alu exec_update_flow_count {
    reg: counts;

    condition_lo: mdata.seq_order > 0;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: myforward.flowcount;
    update_lo_2_predicate: not condition_lo;
    update_lo_2_value: register_lo + myforward.flowcount;

    output_predicate: true;
    output_dst: mdata.flowcount;
    output_value: alu_lo;
}

action do_update_flow_count() {
    exec_update_flow_count.execute_stateful_alu(myforward.srcID);
    modify_field(mdata.order8, mdata.seq_order);
}

table update_flow_count {
    actions {
        do_update_flow_count;
    }
    default_action : do_update_flow_count();
    size: 1;
}

action do_check_seq_order() {
    subtract(mdata.seq_order, myforward.seq, mdata.last_seq);
}

table check_seq_order {
    actions {
        do_check_seq_order;
    }
    default_action : do_check_seq_order();
    size: 1;
}

blackbox stateful_alu exec_read_then_update_last_seq {
    reg: last_seqs;

    condition_lo: myforward.seq > register_lo;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: myforward.seq;

    output_predicate: true;
    output_dst: mdata.last_seq;
    output_value: register_lo;
}

action do_update_last_seq() {
    exec_read_then_update_last_seq.execute_stateful_alu(myforward.srcID);
}

table update_last_seq {
    actions {
        do_update_last_seq;
    }
    default_action: do_update_last_seq;
    size: 1;
}

control ingress {
    if (valid(myforward)) {
        apply(update_last_seq);
        apply(check_seq_order);
        apply(update_flow_count);
        apply(update_monitor_count);
        apply(check_aggregation_completion);

        /* on aggregation completion*/
        if (mdata.aggr_complete_flag == 0) {
            apply(gather_aggregation_result);
        } else {
            apply(drop_packet);
        }
    }
}

/*************************************************************************
 ****************  E G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/
control egress {
}
