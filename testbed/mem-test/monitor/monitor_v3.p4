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

#define TTL_BIT 16
#define BITMAP_BIT 16
#define COUNT_WIDTH 16
#define EPOCH_WIDTH 16
#define TSTAMP_WIDTH 16
#define FLAG_WIDTH 16
#define QUERY_SIZE 65536
#define INSTANCE_SIZE 131072
#define SLOT_WIDTH 4

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
        qID: 16;
        index: 16;
        epoch: EPOCH_WIDTH;
        flowcount: COUNT_WIDTH;
        bitmap: BITMAP_BIT;
    }
}

/*************************************************************************
 ***********************  M E T A D A T A  *******************************
 *************************************************************************/

header_type mdata_t {
    fields {
        tstamp_epoch: EPOCH_WIDTH;
        tstamp_index: 16;
        snapshot_epoch: EPOCH_WIDTH;
        flowcount: 16;
        is_newcomer_epo: 16;
        is_newcomer_idx: 16;
        is_newcomer: 16;
        qID: 16;
        snapshot_index: 16;
    }
}

metadata mdata_t mdata;
/*************************************************************************
***********************  P A R S E R  ***********************************
*************************************************************************/

header ethernet_t ethernet;
header ipv4_t ipv4;
header myforward_t myforward;

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
    return ingress;
}

parser parse_ipv4 {
    extract(ipv4);
    return ingress;
}

/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

register value_counts {
     width : COUNT_WIDTH;
     instance_count : INSTANCE_SIZE;
 }

register value_epoches {
      width : EPOCH_WIDTH;
      instance_count : INSTANCE_SIZE;
  }

register last_indice {
    // tofino don't allow width != 1, 8, 16, 32
    width : 16;
    instance_count: QUERY_SIZE;
}

register last_epoches {
    width: TSTAMP_WIDTH;
    instance_count: QUERY_SIZE;
}

register flowcounts {
    width: COUNT_WIDTH;
    instance_count: QUERY_SIZE;
}

table record_control_tstamp {
    actions {
        do_record_control_tstamp;
    }
    default_action: do_record_control_tstamp();
    size: 1;
}

table record_data_tstamp {
    actions {
        do_record_data_tstamp;
    }
    default_action: do_record_data_tstamp();
    size: 1;
}

table truncate_index {
    actions {
        do_truncate_index;
    }
    default_action: do_truncate_index();
    size: 1;
}

table move_into_snapshot_index {
    actions {
        do_move_into_snapshot_index;
    }
    default_action: do_move_into_snapshot_index();
    size: 1;
}

table shift_index {
    actions {
        do_shift_index;
    }
    default_action: do_shift_index();
    size: 1;
}

table get_snapshot_index {
    actions {
        do_get_snapshot_index;
    }
    default_action: do_get_snapshot_index();
    size: 1;
}

@pragma stage 9
table read_snapshot_cnt {
    actions {
        do_read_snapshot_cnt;
    }
    default_action: do_read_snapshot_cnt();
    size: 1;
}


table check_snapshot_epoch {
    actions {
        do_check_snapshot_epoch;
    }
    default_action: do_check_snapshot_epoch();
    size: 1;
}


table response_with_value {
    reads {
        myforward.qID: exact;
    }
    actions {
        do_response_with_value;
        NoAction;
    }
    default_action: NoAction();
    size: QUERY_SIZE;
}

table correct_qid {
    reads {
        ipv4.srcAddr: exact;
        ipv4.dstAddr: exact;
    }
    actions {
        do_correct_qid;
        NoAction;
    }
    default_action: NoAction();
    size: QUERY_SIZE;
}

table record_data_flow {
    actions {
        do_record_data_flow;
    }
    default_action: do_record_data_flow();
    size: 1;
}

table check_newcomer_epoch {
    actions {
        do_check_newcomer_epoch;
    }
    default_action: do_check_newcomer_epoch();
    size: 1;
}

table check_newcomer_index {
    actions {
        do_check_newcomer_index;
    }
    default_action: do_check_newcomer_index();
    size: 1;
}

table check_newcomer {
    actions {
        do_check_newcomer;
    }
    default_action: do_check_newcomer();
    size: 1;
}

table update_snapshot_epo {
    actions {
        do_update_snapshot_epo;
    }
    default_action: do_update_snapshot_epo();
    size: 1;
}

@pragma stage 9
table update_snapshot_cnt {
    actions {
        do_update_snapshot_cnt;
    }
    default_action: do_update_snapshot_cnt();
    size: 1;
}

action NoAction() {

}

action do_record_control_tstamp() {
    modify_field(mdata.tstamp_epoch, myforward.epoch);
    modify_field(mdata.tstamp_index, myforward.index);
    modify_field(mdata.qID, myforward.qID);
}

action do_record_data_tstamp() {
    /* TODO: fix this workaround, we actually want 32~35 bit as index, 
             36~47 bit as epoch*/
    // modify_field(mdata.tstamp_epoch, ig_intr_md.ingress_mac_tstamp);
}

action do_truncate_index() {
    bit_and(mdata.tstamp_index, mdata.tstamp_epoch, 15);
}

action do_move_into_snapshot_index() {
    modify_field(mdata.snapshot_index, mdata.tstamp_index);
}

action do_shift_index() {
    // TODO: fix workaround from 8 -> 16
    shift_left(mdata.snapshot_index, mdata.snapshot_index, 8);
}

action do_get_snapshot_index() {
    add_to_field(mdata.snapshot_index, mdata.qID);
}

action do_read_snapshot_cnt() {
    exec_response_with_value.execute_stateful_alu(mdata.snapshot_index);
}

action do_check_snapshot_epoch() {
    exec_check_snapshot_epoch.execute_stateful_alu(mdata.snapshot_index);
}

action do_response_with_value(bitmap) {
    // exec_response_with_value.execute_stateful_alu(mdata.snapshot_index);
    modify_field(myforward.flowcount, mdata.flowcount);
    modify_field(myforward.bitmap, bitmap);
}

action do_correct_qid(qid) {
    modify_field(mdata.qID, qid);
    add_to_field(mdata.snapshot_index, qid);
}

action do_record_data_flow() {
    exec_record_data_flow.execute_stateful_alu(mdata.qID);
}

action do_check_newcomer_epoch() {
    exec_check_newcomer_epoch.execute_stateful_alu(mdata.qID);
}

action do_check_newcomer_index() {
    exec_check_newcomer_index.execute_stateful_alu(mdata.qID);
}

action do_check_newcomer() {
    bit_or(mdata.is_newcomer, mdata.is_newcomer_epo, mdata.is_newcomer_idx);
}

action do_update_snapshot_epo() {
    exec_update_snapshot_epo.execute_stateful_alu(mdata.snapshot_index);
}

action do_update_snapshot_cnt() {
    exec_update_snapshot_cnt.execute_stateful_alu(mdata.snapshot_index);
}

blackbox stateful_alu exec_check_snapshot_epoch {
    reg: value_epoches;
    
    output_predicate: true;
    output_dst: mdata.snapshot_epoch;
    output_value: register_lo;
}

blackbox stateful_alu exec_response_with_value {
    reg: value_counts;
    
    output_predicate: true;
    output_dst: mdata.flowcount;
    output_value: register_lo;
}

blackbox stateful_alu exec_record_data_flow {
    reg: flowcounts;
    
    update_lo_1_predicate: true;
    update_lo_1_value: register_lo + 1;

    output_predicate: true;
    output_dst: mdata.flowcount;
    output_value: register_lo;
}

blackbox stateful_alu exec_check_newcomer_epoch {
    reg: last_epoches;
    
    condition_lo: mdata.tstamp_epoch != register_lo;

    update_lo_1_predicate: condition_lo;
    update_lo_1_value: mdata.tstamp_epoch;

    output_predicate: condition_lo;
    output_dst: mdata.is_newcomer_epo;
    initial_register_lo_value: 1;
    output_value: register_lo;
}

blackbox stateful_alu exec_check_newcomer_index {
    reg: last_indice;
    
    condition_lo: mdata.tstamp_index != register_lo;

    update_lo_1_predicate: condition_lo;
    update_lo_1_value: mdata.tstamp_index;

    output_predicate: condition_lo;
    output_dst: mdata.is_newcomer_idx;
    initial_register_lo_value: 1;
    output_value: register_lo;
}

blackbox stateful_alu exec_update_snapshot_epo {
    reg: value_epoches;

    update_lo_1_predicate: true;
    update_lo_1_value: mdata.tstamp_epoch;
}

blackbox stateful_alu exec_update_snapshot_cnt {
    reg: value_counts;

    update_lo_1_predicate: true;
    update_lo_1_value: mdata.flowcount;
}

control ingress {
    if (valid(myforward)) {
        apply(record_control_tstamp);
    } else {
        apply(record_data_tstamp);
    }
    apply(truncate_index);
    apply(move_into_snapshot_index);
    apply(shift_index);
    apply(get_snapshot_index);
    if (valid(myforward)) {
        apply(read_snapshot_cnt);
	apply(check_snapshot_epoch);
        if (mdata.snapshot_epoch == myforward.epoch) {
            apply(response_with_value);
	}
    } else {
        apply(correct_qid);
        apply(record_data_flow);
        apply(check_newcomer_epoch);
        apply(check_newcomer_index);
        apply(check_newcomer);
        if (mdata.is_newcomer == 1) {
            // apply(update_snapshot_epo);
            apply(update_snapshot_cnt);
            apply(update_snapshot_epo);
        }
    }
}

/*************************************************************************
 ****************  E G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/
control egress {
}
