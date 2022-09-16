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
#define INSTANCE_SIZE 1048576
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
        srcID  : 16;
        dstID  :  16;
        // in a time unit of 0.268 sec
        tstamp: TSTAMP_WIDTH;
        seq  : 16;
        flowcount: COUNT_WIDTH;
        bitmap : BITMAP_BIT;
        // use to indicate if monitor contains desiring snapshot
        // could be indicated by bitmap
        // flags: FLAG_WIDTH;
        ttl : TTL_BIT;
        hop_cnt  :  16;
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
        // ingress_tstamp_epoch: 48;
        tstamp_index : SLOT_WIDTH;
        tstamp_epoch: TSTAMP_WIDTH;
        fetched_epoch: TSTAMP_WIDTH;
        snapshot_index: 32;
        // it's required to used aligned mem in add_to_field
        index_adder_buffer: 32;
        aligned_index: 8;
        is_latest_index: 8;
        is_latest_epoch: TSTAMP_WIDTH;
        flowcount: COUNT_WIDTH;
    }
}

metadata mdata_t mdata;
/*************************************************************************
***********************  P A R S E R  ***********************************
*************************************************************************/

header ethernet_t ethernet;
header ipv4_t ipv4;
@pragma pa_no_tagalong ingress myforward.hop_cnt
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
    width : 8;
    instance_count: QUERY_SIZE;
}

register last_epoches {
    width: TSTAMP_WIDTH;
    instance_count: QUERY_SIZE;
}

// this only used to transform 48 tstamp to 32 bit slice in p4_14
register tstamp_slicer {
    width : 32;
    instance_count: 1;
}

register flowcounts {
    width: COUNT_WIDTH;
    instance_count: QUERY_SIZE;
}

blackbox stateful_alu update_and_retrieve_flowcount {
    reg: flowcounts;

    update_lo_1_predicate: true;
    update_lo_1_value: register_lo + 1;

    output_predicate: true;
    output_dst: mdata.flowcount;
    output_value: register_lo;
}

action do_increment_flowcount() {
    update_and_retrieve_flowcount.execute_stateful_alu(mdata.index_adder_buffer);
}

table increment_flowcount {
    actions {
        do_increment_flowcount;
    }
    default_action: do_increment_flowcount();
    size: 1;
}

action do_response_with_count() {
    fetch_snapshot_value.execute_stateful_alu(mdata.snapshot_index);
}

table response_with_count {
    actions {
        do_response_with_count;
    }
    default_action: do_response_with_count();
    size: 1;
}

action do_response(bitmap) {
    modify_field(myforward.bitmap, bitmap);
    // modify_field(ig_intr_md_for_tm.ucast_egress_port, ig_intr_md.ingress_port);
    swap(myforward.srcID, myforward.dstID);
}

table response {
    reads {
        myforward.dstID: exact;
    }
    actions {
        do_response;
    }
    default_action: do_response(0);
    size: QUERY_SIZE;
}

blackbox stateful_alu fetch_snapshot_epoch {
    reg: value_epoches;

    output_predicate: true;
    output_dst: mdata.fetched_epoch;
    output_value: register_lo;
}

blackbox stateful_alu fetch_snapshot_value {
    reg: value_counts;

    output_predicate: true;
    output_dst: myforward.flowcount;
    output_value: register_lo;
}

action do_translate_control_tstamp() {
    modify_field(mdata.tstamp_index, myforward.tstamp);
    shift_right(mdata.tstamp_epoch,  myforward.tstamp, 4);
}

table translate_control_tstamp {
    actions {
        do_translate_control_tstamp;
    }
    default_action: do_translate_control_tstamp();
    size: 1;
}

action do_make_tstamp_index() {
    modify_field(mdata.tstamp_index, mdata.snapshot_index);
}

table make_tstamp_index {
    actions {
        do_make_tstamp_index;
    }
    default_action: do_make_tstamp_index();
    size: 1;
}

action do_prepare_data_index(qid) {
    shift_right(mdata.snapshot_index, mdata.snapshot_index, 28);
    modify_field(mdata.index_adder_buffer, qid);
}

table prepare_data_index {
    reads {
        ipv4.dstAddr: exact;
    }
    actions {
        do_prepare_data_index;
    }
    default_action: do_prepare_data_index(1);
    size: QUERY_SIZE;
}

@pragma stateful_field_slice ig_intr_md.ingress_mac_tstamp 47 32
blackbox stateful_alu transformer {
    reg: tstamp_slicer;

    output_predicate: true;
    output_value : ig_intr_md.ingress_mac_tstamp;
    output_dst : mdata.tstamp_epoch;
}

action do_translate_data_tstamp() {
    // we have to first recieve as 48 bit, since this is the only API to take in a 48 bits input
    // modify_field(mdata.ingress_tstamp_epoch, ig_intr_md.ingress_mac_tstamp);
    modify_field(mdata.snapshot_index,  ig_intr_md.ingress_mac_tstamp);
    transformer.execute_stateful_alu(0);
}

table translate_data_tstamp {
    actions {
        do_translate_data_tstamp;
    }
    default_action: do_translate_data_tstamp();
    size: 1;
}


action do_get_snapshot_index2() {
    add_to_field(mdata.snapshot_index, mdata.index_adder_buffer);
}


table get_snapshot_index2 {
    actions {
        do_get_snapshot_index2;
    }
    default_action: do_get_snapshot_index2();
    size: 1;
}

action do_get_snapshot_index1() {
    add_to_field(mdata.snapshot_index, mdata.index_adder_buffer);
}

table get_snapshot_index1 {
    actions {
        do_get_snapshot_index1;
    }
    default_action: do_get_snapshot_index1();
    size: 1;
}


action do_shift_snapshot_index2() {
    shift_left(mdata.snapshot_index, mdata.snapshot_index, 16);
}

table shift_snapshot_index2 {
    actions {
        do_shift_snapshot_index2;
    }
    default_action: do_shift_snapshot_index2();
    size: 1;
}

action do_shift_snapshot_index1() {
    shift_left(mdata.snapshot_index, mdata.snapshot_index, 16);
}

table shift_snapshot_index1 {
    actions {
        do_shift_snapshot_index1;
    }
    default_action: do_shift_snapshot_index1();
    size: 1;
}


action do_prepare_index() {
    modify_field(mdata.snapshot_index, mdata.tstamp_index);
    modify_field(mdata.index_adder_buffer, myforward.srcID);
}

table prepare_index {
    actions {
        do_prepare_index;
    }
    default_action: do_prepare_index();
    size: 1;
}

action do_check_snapshot_avail() {
    fetch_snapshot_epoch.execute_stateful_alu(mdata.snapshot_index);
    // this is wrong/not necessary, but as a workaround for PHV access
    // I hate stupid tofino parser (with little support)
    modify_field(myforward.ttl, myforward.bitmap);
}

table check_snapshot_avail {
    actions {
        do_check_snapshot_avail;
    }
    default_action: do_check_snapshot_avail();
    size: 1;
}

blackbox stateful_alu update_last_index {
    reg: last_indice;
    condition_lo: mdata.aligned_index > register_lo;

    output_predicate: condition_lo;
    output_dst: mdata.is_latest_index;

    update_lo_1_predicate: condition_lo;
    update_lo_1_value: mdata.aligned_index;

    initial_register_lo_value: 1;
    output_value: register_lo;
}

blackbox stateful_alu update_last_epoch {
    reg: last_epoches;
    condition_lo: mdata.tstamp_epoch > register_lo;

    output_predicate: condition_lo;
    output_dst: mdata.is_latest_epoch;

    update_lo_1_predicate: condition_lo;
    update_lo_1_value: mdata.tstamp_epoch;

    initial_register_lo_value: 1;
    output_value: register_lo;
}

action do_update_last_index() {
    update_last_index.execute_stateful_alu(mdata.index_adder_buffer);
    // update_last_epoch.execute_stateful_alu(mdata.index_adder_buffer);
}

action do_update_last_epoch() {
    update_last_epoch.execute_stateful_alu(mdata.index_adder_buffer);
}

table update_last_index {
    actions {
        do_update_last_index;
    }
    default_action: do_update_last_index();
    size: 1;
}

table update_last_epoch {
    actions {
        do_update_last_epoch;
    }
    default_action: do_update_last_epoch();
    size: 1;
}

action do_prepare_update_last_info() {
    modify_field(mdata.aligned_index, mdata.tstamp_index);
}

table prepare_update_last_info {
    actions {
        do_prepare_update_last_info;
    }
    default_action: do_prepare_update_last_info();
    size: 1;
}

blackbox stateful_alu update_snapshot_value {
    reg: value_counts;

    update_lo_1_predicate: true;
    update_lo_1_value: mdata.flowcount;
}

blackbox stateful_alu update_snapshot_epoch {
    reg: value_epoches;

    update_lo_1_predicate: true;
    update_lo_1_value: mdata.tstamp_epoch;
}

action do_update_record_value() {
    update_snapshot_value.execute_stateful_alu(mdata.snapshot_index);
    // update_snapshot_epoch.execute_stateful_alu(mdata.snapshot_index);
}

action do_update_record_epoch() {
    update_snapshot_epoch.execute_stateful_alu(mdata.snapshot_index);
}

table update_record_value {
    actions {
        do_update_record_value;
    }
    default_action: do_update_record_value();
    size: 1;
}

table update_record_epoch {
    actions {
        do_update_record_epoch;
    }
    default_action: do_update_record_epoch();
    size: 1;
}

action do_reset_ttl() {
    modify_field(myforward.ttl, 0);
}

table reset_ttl {
    actions {
        do_reset_ttl;
    }
    default_action: do_reset_ttl();
    size: 1;
}

control ingress {
    if (valid(myforward)) {
        apply(translate_control_tstamp);
        // we have to first align mem width due to shift_left API
        apply(prepare_index);
        apply(shift_snapshot_index1);
        apply(get_snapshot_index1);
        apply(check_snapshot_avail);
        apply(response);
        // we had to move out the condition in order to reduce variable usage in stateful alu
        if (mdata.tstamp_epoch == mdata.fetched_epoch) {
            apply(response_with_count);
            // again, this is absolutely wrong/unnecessary, however
            // it all results from stupid tofino parser
            if (myforward.ttl != 0) {
                apply(reset_ttl);
            }
        }
    } else {
        apply(translate_data_tstamp);
        // we have to first align mem width due to shift_left API
        apply(prepare_data_index);
        apply(make_tstamp_index);
        apply(shift_snapshot_index2);
        apply(get_snapshot_index2);
        apply(prepare_update_last_info);
	// tofino don't allow to stateful alu in the same action
	// even if they are independent
	apply(update_last_index);
	apply(update_last_epoch);
        // apply(update_last_index_and_epoch);
        // record flowcount and retrieve flowcount as well
        apply(increment_flowcount);
        if (mdata.is_latest_index != 0) {
            // apply(update_record);
            apply(update_record_value);
            apply(update_record_epoch);
        } else if (mdata.is_latest_epoch != 0) {
            // apply(update_record);
            apply(update_record_value);
            apply(update_record_epoch);
        }
        // TODO: add data plane routing here
    }
}

/*************************************************************************
 ****************  E G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/
control egress {
}
