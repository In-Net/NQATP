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

#define MONITOR_NUMBER 2
#define COUNT_WIDTH 16
#define QUERY_WIDTH 16
/* Normally INSTANCE_SIZE will be 2 ** QUERY_WIDTH */
#define INSTANCE_SIZE 65536
#define SEQ_WIDTH 16
#define MONITOR_SCALE_BIT 16
#define CONTROL_EGRESS_SPEC 56

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

header_type myControl_t {
    fields {
        dummy  : 32;
        queryID    :  16;
        flowCount        : COUNT_WIDTH;
        seq        : SEQ_WIDTH;
    }
}

/*************************************************************************
 ***********************  M E T A D A T A  *******************************
 *************************************************************************/

/* metadata are always init to zero*/
header_type mdata_t {
    fields {
        aggregated_monitor_number : MONITOR_SCALE_BIT;
        last_seen_seq: SEQ_WIDTH;
        flow_count: COUNT_WIDTH;
        aggr_complete_flag: MONITOR_SCALE_BIT;
        is_new_seq: SEQ_WIDTH;
    }
}

 /*************************************************************************
 ***********************  P A R S E R  ***********************************
 *************************************************************************/

 header ethernet_t ethernet;
 header ipv4_t ipv4;
 header myControl_t myControl;
 metadata mdata_t mdata;

 parser start {
     extract(ethernet);
     return select(ethernet.etherType) {
         0x0800 : parse_ipv4;
         default: ingress;
     }
 }

 parser parse_ipv4 {
     extract(ipv4);
     return select(ipv4.protocol) {
         0x9F : parse_myControl;
         default: ingress;
     }
 }

 parser parse_myControl {
     extract(myControl);
     return ingress;
 }

 /*************************************************************************
 **************  I N G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/

 register query_counters {
     width : COUNT_WIDTH;
     instance_count : INSTANCE_SIZE;
 }

 register acked_monitor_numbers {
     width : MONITOR_SCALE_BIT;
     instance_count : INSTANCE_SIZE;
 }

 register last_seen_seqs {
     width: SEQ_WIDTH;
     instance_count: INSTANCE_SIZE;
 }

 action nop() {

 }

table check_flow_direction {
    reads {
        ipv4.dstAddr: exact;
    }
    actions {
        nop;
    }
}

table read_then_update_last_seen_seq {
    actions {
        do_read_then_update_last_seen_seq;
    }
    default_action : do_read_then_update_last_seen_seq();
}

action do_read_then_update_last_seen_seq() {
    exec_read_then_update_last_seen_seq.execute_stateful_alu(myControl.queryID);
}

blackbox stateful_alu exec_read_then_update_last_seen_seq {
    reg: last_seen_seqs;

    condition_lo: myControl.seq > register_lo;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: myControl.seq;

    output_predicate: true;
    output_dst: mdata.last_seen_seq;
    output_value: register_lo;
}

table update_flow_count {
    actions {
        do_update_flow_count;
    }
    default_action : do_update_flow_count();
}

action do_update_flow_count() {
    exec_rupdate_flow_count.execute_stateful_alu(myControl.queryID);
}

blackbox stateful_alu exec_rupdate_flow_count {
    reg: query_counters;

    condition_lo: mdata.is_new_seq > 0;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: myControl.flowCount;
    update_lo_2_predicate: not condition_lo;
    update_lo_2_value: register_lo + myControl.flowCount;

    output_predicate: true;
    output_dst: mdata.flow_count;
    output_value: alu_lo;
}

table update_monitor_count {
    actions {
        do_update_monitor_count;
    }
    default_action : do_update_monitor_count();
}

action do_update_monitor_count() {
    exec_update_monitor_count.execute_stateful_alu(myControl.queryID);
}

blackbox stateful_alu exec_update_monitor_count {
    reg: acked_monitor_numbers;

    condition_lo: mdata.is_new_seq > 0;
    update_lo_1_predicate: condition_lo;
    update_lo_1_value: 1;
    update_lo_2_predicate: not condition_lo;
    update_lo_2_value: register_lo + 1;

    output_predicate: true;
    output_dst: mdata.aggregated_monitor_number;
    output_value: alu_lo;
}

table check_aggregation_completion {
    actions {
        do_check_aggregation_completion;
    }
    default_action : do_check_aggregation_completion();
}

action do_check_aggregation_completion() {
    subtract(mdata.aggr_complete_flag, MONITOR_NUMBER, mdata.aggregated_monitor_number);
}

table gather_aggregation_result {
    actions {
        do_gather_aggregation_result;
    }
    default_action : do_gather_aggregation_result();
}

action do_gather_aggregation_result() {
    modify_field(myControl.flowCount, mdata.aggregated_monitor_number);
    modify_field(ig_intr_md_for_tm.ucast_egress_port, CONTROL_EGRESS_SPEC);
}

table drop_packet {
    actions {
        do_drop_packet;
    }
    default_action : do_drop_packet();
}

action do_drop_packet() {
    drop();
}

table check_newer_seq_or_not {
    actions {
        do_check_newer_seq_or_not;
    }
    default_action : do_check_newer_seq_or_not();
}

action do_check_newer_seq_or_not() {
    subtract(mdata.is_new_seq, myControl.seq, mdata.last_seen_seq);
}

 control ingress {
     if (valid(myControl)) {
         apply(check_flow_direction) {
             hit {
                 apply(read_then_update_last_seen_seq);
                 apply(check_newer_seq_or_not);
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
     }
 }

/*************************************************************************
 ****************  E G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/
control egress {
}
