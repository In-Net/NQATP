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

#define MONITOR_NUMBER 8

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
        queryID        : 16;
        flowCount        : 16;
        seq        : 16;
    }
}

/*************************************************************************
 ***********************  M E T A D A T A  *******************************
 *************************************************************************/

/* metadata are always init to zero*/
header_type mdata_t {
    fields {
        aggregated_monitor_number : 8;
        last_seen_seq: 16;
        is_to_aggregator: 1;
        is_to_controller: 1;
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

 parse_myControl {
     extract(myControl);
     return ingress;
 }

 /*************************************************************************
 **************  I N G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/

 register query_counters {
     width : 16;
     instance_count : 65536;
 }

 register acked_monitor_numbers {
     width : 8;
     instance_count : 65536;
 }

 register last_seen_seqs {
     width: 16;
     instance_count: 65536;
 }

blackbox stateful_alu aggregate_counter {
    reg: query_counters;

    update_lo_1_value : register_lo + myControl.flowCount;
}

blackbox stateful_alu ack_a_monitor {
    reg: acked_monitor_numbers;

    update_lo_1_value : register_lo + 1;
    output_predicate : true;
    output_dst : mdata.aggregated_monitor_number;
    output_value : register_lo + 1;
}

action unpack_poll_request() {
    /* TODO: ignore this part for now*/
}

action aggregate_response() {
    aggregate_counter.execute_stateful_alu(myControl.queryID);
    ack_a_monitor.execute_stateful_alu(myControl.queryID);
}

table aggregator_response {
    actions {
        unpack_poll_request;
    }
}

table aggregate_to_controller {
    actions {
        aggregate_response;
    }
}

action mark_to_aggregator() {
    modify_field(mdata.is_to_aggregator, 1);
}

action mark_to_controller() {
    modify_field(mdata.is_to_controller, 1);
}

table check_destination {
    reads {
        ipv4.dstAddr : exact;
    }
    actions {
        mark_to_aggregator;
        mark_to_controller;
    }
}

/* TODO: should have a READ on mdata.aggregated_monitor_number here 
    However, then control plane config will be lengthy 
    LPM is a work-around, but not elegant */
/*
table check_aggregation_is_satisfied {
    actions {
        do_check_aggregation;
    }
}
*/

blackbox stateful_alu read_last_seen_seq {
    reg: last_seen_seqs;

    output_predicate : true;
    output_dst : mdata.last_seen_seq;
    output_value : register_lo;
}

blackbox stateful_alu cleanup_counter_on_new_seen_seq {
    reg : query_counters;
    condition_lo : mdata.last_seen_seq < myControl.seq;
    update_lo_1_predicate : condition_lo;
    update_lo_1_value : 0;
}

blackbox stateful_alu cleanup_acked_on_new_seen_seq {
    reg : acked_monitor_numbers;
    condition_lo : mdata.last_seen_seq < myControl.seq;
    update_lo_1_predicate : condition_lo;
    update_lo_1_value : 0;
}

blackbox stateful_alu update_seq_on_new_seen_seq {
    reg : last_seen_seqs;
    condition_lo : mdata.last_seen_seq < myControl.seq;
    update_lo_1_predicate : condition_lo;
    update_lo_1_value : myControl.seq;
}

action check_new_seq() {
    read_last_seen_seq.execute_stateful_alu(myControl.queryID);
    cleanup_counter_on_new_seen_seq.execute_stateful_alu(myControl.queryID);
    cleanup_acked_on_new_seen_seq.execute_stateful_alu(myControl.queryID);
    update_seq_on_new_seen_seq.execute_stateful_alu(myControl.queryID);
}

table on_receiving_new_seq {
    actions {
        check_new_seq;
    }
}

blackbox stateful_alu retrieve_aggregation_count {
    reg : query_counters;

    update_lo_1_value : 0;
    output_predicate: true;
    output_dst : myControl.flowCount;
    output_value : register_lo;
}

blackbox stateful_alu cleanup_acked_on_complete {
    reg : acked_monitor_numbers;

    update_lo_1_value : 0;
}

action retrieve_aggregation(egress_spec) {
    retrieve_aggregation_count.execute_stateful_alu(myControl.queryID);
    cleanup_acked_on_complete.execute_stateful_alu(myControl.queryID);
    modify_field(ig_intr_md_for_tm.ucast_egress_port, egress_spec);
}

table forward_aggregation_results {
    reads {
        // useless here, just can't use default action for variable
        myControl.queryID : exact;
    }
    actions {
        retrieve_aggregation;
    }
}

control ingress {
    if (valid(myControl)) {
        apply(check_destination);

        if (mdata.is_to_controller == 1) {
            apply(on_receiving_new_seq);
            apply(aggregate_to_controller);
        } else if (mdata.is_to_aggregator == 1) {
            apply(aggregator_response);
        }
        // TODO: replace it with apply(check_aggregation_is_satisfied);
        // this is a work-around since we don't want to manually config
        // every query with the same monitor number
        if (mdata.aggregated_monitor_number < MONITOR_NUMBER) {
            drop();
        } else {
            apply(forward_aggregation_results);
        }
    }
}

/*************************************************************************
 ****************  E G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/
control egress {
}
