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

/* it is better with byte-allignd */
#define PSEUDO_EPOCH_BIT 32
#define EPOCH_BIT 20
#define SLOT_BIT 8
#define SLOT_MASK 0x00FF00000000
#define EPOCH_MASK 0xFF0000000000
#define SLOT_NUM 256
#define uS2S_BIT 20

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

header_type myPoll_t {
    fields {
        slotID        : 16;
        epoch       : 32;
        slot0        : 16;
        // slot1        : 16;
    }
}

/*************************************************************************
 ***********************  M E T A D A T A  *******************************
 *************************************************************************/

/* metadata are always init to zero*/
header_type mdata_t {
    fields {
        data_plane_timestamp: 48;
        data_epoch: PSEUDO_EPOCH_BIT;
        current_epoch: PSEUDO_EPOCH_BIT;
        current_count: 16;
        data_time_zone: 8;
        last_time_zone: 8;
        is_new_snapshot: 8;
        temp_epoch_placeholder: 32;
        temp_slot_placeholder: 32;
        temp_output_placeholder: 16;
        // slot_id_1: SLOT_BIT;
        truncated_slot_id: 8;
        temp_max_slot0: 8;
        is_slot0_invalid: 8;
        // temp_max_slot1: 8;
        // is_slot1_invalid: 8;
        // slot_validation: 8;
    }
}

 /*************************************************************************
 ***********************  P A R S E R  ***********************************
 *************************************************************************/

 header ethernet_t ethernet;
 header ipv4_t ipv4;
 header myPoll_t myPoll;
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
         0x9F : parse_myPoll;
         default: ingress;
     }
 }

 parser parse_myPoll {
     extract(myPoll);
     return ingress;
 }

 /*************************************************************************
 **************  I N G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/

 register value_counts {
     width : 16;
     instance_count : SLOT_NUM;
 }

 register value_epoches {
     width : PSEUDO_EPOCH_BIT;
     instance_count : SLOT_NUM;
 }

 register reg_count_now {
     width: 16;
     instance_count: 1;
 }

 register reg_epoch_now {
     width: PSEUDO_EPOCH_BIT;
     instance_count: 1;
 }

 register reg_start_time {
     width: 48;
     instance_count: 1;
 }
 // ingress_intrinsic_metadata_t.ingress_mac_tstamp: 48

 register reg_last_time_slot {
     width: SLOT_BIT;
     instance_count: 1;
 }

blackbox stateful_alu increase_current_count {
    reg: reg_count_now;

    update_lo_1_value : register_lo + 1;
    output_predicate: true;
    output_dst: mdata.current_count;
    output_value: register_lo;
}

action record_in_current_count3() {
    modify_field(mdata.data_epoch, mdata.temp_epoch_placeholder);
    modify_field(mdata.data_time_zone, mdata.temp_slot_placeholder);
}

table on_receiving_data_packet3 {
    actions {
        record_in_current_count3;
    }
    default_action : record_in_current_count3();
}

action record_in_current_count2() {
    shift_right(mdata.temp_epoch_placeholder, mdata.temp_epoch_placeholder, 4);
    shift_right(mdata.temp_slot_placeholder, mdata.temp_slot_placeholder, 2);
    //modify_field(mdata.data_epoch, mdata.temp_shift_placeholder);
}

table on_receiving_data_packet2 {
    actions {
        record_in_current_count2;
    }
    default_action : record_in_current_count2();
}

action record_in_current_count1() {
    increase_current_count.execute_stateful_alu(0);

    /* update time-related data (including metadata and register) */
    // modify_field(mdata.data_plane_timestamp, ig_intr_md.ingress_mac_tstamp);
    bit_and(mdata.temp_epoch_placeholder, ig_intr_md.ingress_mac_tstamp, EPOCH_MASK);
    bit_and(mdata.temp_slot_placeholder, ig_intr_md.ingress_mac_tstamp, SLOT_MASK);
}

table on_receiving_data_packet1 {
    actions {
        record_in_current_count1;
    }
    default_action : record_in_current_count1();
}

blackbox stateful_alu check_new_epoch {
    reg: reg_epoch_now;

    condition_lo: mdata.data_epoch > register_lo;
    output_predicate: condition_lo;
    output_dst : mdata.is_new_snapshot;

    update_lo_1_predicate : condition_lo;
    update_lo_1_value: mdata.data_epoch;

    initial_register_lo_value :  1;
    output_value : register_lo;
}

blackbox stateful_alu check_new_time_slot {
    reg: reg_last_time_slot;

    condition_lo: mdata.data_time_zone > register_lo;
    output_predicate: condition_lo;
    output_dst : mdata.is_new_snapshot;

    update_lo_1_predicate : condition_lo;
    update_lo_1_value: mdata.data_time_zone;

    initial_register_lo_value :  1;
    output_value : register_lo;
}

blackbox stateful_alu read_current_epoch {
    reg: reg_count_now;

    output_predicate : true;
    output_dst : mdata.current_epoch;
    output_value : register_lo;
}

blackbox stateful_alu read_last_time_slot {
    reg: reg_last_time_slot;

    output_predicate : true;
    output_dst : mdata.last_time_zone;
    output_value : register_lo;
}

blackbox stateful_alu take_snapshot_on_count {
    reg: value_counts;
    /*
    condition_lo: mdata.is_new_snapshot == 1;
    update_lo_1_predicate: condition_lo;
    */
    update_lo_1_value: mdata.current_count;
}

blackbox stateful_alu take_snapshot_on_epoch {
    reg: value_epoches;
    /*
    condition_lo: mdata.is_new_snapshot == 1;
    update_lo_1_predicate: condition_lo;
    */
    update_lo_1_value: mdata.data_epoch;
}

action read_to_mdata2() {
    /* read time reg data to metadata */
    // read_current_epoch.execute_stateful_alu(0);
    read_last_time_slot.execute_stateful_alu(0);
}

@pragma stage 3
table on_receiving_new_data2 {
    actions {
        read_to_mdata2;
    }
    default_action : read_to_mdata2();
}

action read_to_mdata1() {
    /* read time reg data to metadata */
    read_current_epoch.execute_stateful_alu(0);
    // read_last_time_slot.execute_stateful_alu(0);
    modify_field(mdata.truncated_slot_id, myPoll.slotID);
}

/* Check if recieves the first data plane packet within time slot */
table on_receiving_new_data1 {
    actions {
        read_to_mdata1;
    }
    default_action : read_to_mdata1();
}

action do_check_mdata2() {
    // check_new_time_slot.execute_stateful_alu(0);
    check_new_epoch.execute_stateful_alu(0);
}

table check_first_packet2 {
    actions {
        do_check_mdata2;
    }
    default_action : do_check_mdata2();
}

action do_check_mdata1() {
    check_new_time_slot.execute_stateful_alu(0);
    // check_new_epoch.execute_stateful_alu(0);
}

table check_first_packet1 {
    actions {
        do_check_mdata1;
    }
    default_action : do_check_mdata1();
}

action try_snapshot2() {
    // take_snapshot_on_count.execute_stateful_alu(mdata.data_time_zone);
    take_snapshot_on_epoch.execute_stateful_alu(mdata.data_time_zone);
    /* finally we drop every data plane packets */
    modify_field(ig_intr_md_for_tm.drop_ctl, 1);
}

table check_if_need_snapshot2 {
    actions {
        try_snapshot2;
    }
    default_action : try_snapshot2();
}

action try_snapshot1() {
    take_snapshot_on_count.execute_stateful_alu(mdata.data_time_zone);
    // take_snapshot_on_epoch.execute_stateful_alu(mdata.data_time_zone);
    /* finally we drop every data plane packets */
    // modify_field(ig_intr_md_for_tm.drop_ctl, 1);
}

@pragma stage 6
table check_if_need_snapshot1 {
    actions {
        try_snapshot1;
    }
    default_action : try_snapshot1();
}

blackbox stateful_alu read_snapshot_slot_0 {
    reg: value_counts;

    // condition_lo: myPoll.slotID <= mdata.last_time_zone;
    output_predicate: true;
    // output_dst: myPoll.slot0;
    output_dst: mdata.temp_output_placeholder;
    output_value: register_lo;
}

/*
blackbox stateful_alu read_snapshot_slot_1 {
    reg: value_counts;

    // condition_lo: mdata.slot_id_1 <= mdata.last_time_zone;
    output_predicate: true;
    // output_dst: myPoll.slot1;
    output_dst: mdata.temp_output_placeholder;
    output_value: register_lo;
}

blackbox stateful_alu read_snapshot_slot_2 {
    reg: value_counts;

    condition_lo: mdata.slot_id_2 <= mdata.last_time_zone;
    output_predicate: condition_lo;
    output_dst: myPoll.slot2;
    output_value: register_lo;
}


blackbox stateful_alu read_snapshot_slot_3 {
    reg: value_counts;

    condition_lo: mdata.slot_id_3 <= mdata.last_time_zone;
    output_predicate: condition_lo;
    output_dst: myPoll.slot3;
    output_value: register_lo;
}

blackbox stateful_alu read_snapshot_slot_4 {
    reg: value_counts;

    condition_lo: mdata.slot_id_4 <= mdata.last_time_zone;
    output_predicate: condition_lo;
    output_dst: myPoll.slot4;
    output_value: register_lo;
}

blackbox stateful_alu read_snapshot_slot_5 {
    reg: value_counts;

    condition_lo: mdata.slot_id_5 <= mdata.last_time_zone;
    output_predicate: condition_lo;
    output_dst: myPoll.slot5;
    output_value: register_lo;
}

blackbox stateful_alu read_snapshot_slot_6 {
    reg: value_counts;

    condition_lo: mdata.slot_id_6 <= mdata.last_time_zone;
    output_predicate: condition_lo;
    output_dst: myPoll.slot6;
    output_value: register_lo;
}

blackbox stateful_alu read_snapshot_slot_7 {
    reg: value_counts;

    condition_lo: mdata.slot_id_7 <= mdata.last_time_zone;
    output_predicate: condition_lo;
    output_dst: myPoll.slot7;
    output_value: register_lo;
}
*/
action set_response_snapshot_ids() {
    // read_last_time_slot.execute_stateful_alu(0);
    // read_current_epoch.execute_stateful_alu(0);
    modify_field(myPoll.epoch, mdata.current_epoch);
    /*
    add(mdata.slot_id_1, myPoll.slotID, 0x01);
    bit_or(mdata.slot_id_2, myPoll.slotID, 0x02);
    bit_or(mdata.slot_id_3, myPoll.slotID, 0x03);
    bit_or(mdata.slot_id_4, myPoll.slotID, 0x04);
    bit_or(mdata.slot_id_5, myPoll.slotID, 0x05);
    bit_or(mdata.slot_id_6, myPoll.slotID, 0x06);
    bit_or(mdata.slot_id_7, myPoll.slotID, 0x07);
    */
}

table on_receiving_control_packet {
    actions {
        set_response_snapshot_ids;
    }
    default_action : set_response_snapshot_ids();
}
/*
action copy_snapshots_to_response7() {
    read_snapshot_slot_7.execute_stateful_alu(mdata.slot_id_7);
}

table gather_snapshot_to_response7 {
    actions {
        copy_snapshots_to_response7;
    }
    default_action : copy_snapshots_to_response7();
}

action copy_snapshots_to_response6() {
    read_snapshot_slot_6.execute_stateful_alu(mdata.slot_id_6);
}

table gather_snapshot_to_response6 {
    actions {
        copy_snapshots_to_response6;
    }
    default_action : copy_snapshots_to_response6();
}

action copy_snapshots_to_response5() {
    read_snapshot_slot_5.execute_stateful_alu(mdata.slot_id_5);
}

table gather_snapshot_to_response5 {
    actions {
        copy_snapshots_to_response5;
    }
    default_action : copy_snapshots_to_response5();
}

action copy_snapshots_to_response4() {
    read_snapshot_slot_4.execute_stateful_alu(mdata.slot_id_4);
}

table gather_snapshot_to_response4 {
    actions {
        copy_snapshots_to_response4;
    }
    default_action : copy_snapshots_to_response4();
}

action copy_snapshots_to_response3() {
    read_snapshot_slot_3.execute_stateful_alu(mdata.slot_id_3);
}

table gather_snapshot_to_response3 {
    actions {
        copy_snapshots_to_response3;
    }
    default_action : copy_snapshots_to_response3();
}

action copy_snapshots_to_response2() {
    read_snapshot_slot_2.execute_stateful_alu(mdata.slot_id_2);
}

table gather_snapshot_to_response2 {
    actions {
        copy_snapshots_to_response2;
    }
    default_action : copy_snapshots_to_response2();
}
*/

/*
action copy_snapshots_to_response1() {
    read_snapshot_slot_1.execute_stateful_alu(mdata.slot_id_1);
}

@pragma stage 5
table gather_snapshot_to_response1 {
    actions {
        copy_snapshots_to_response1;
    }
    default_action : copy_snapshots_to_response1();
}
*/

action copy_snapshots_to_response0() {
    read_snapshot_slot_0.execute_stateful_alu(myPoll.slotID);
    // read_snapshot_slot_1.execute_stateful_alu(mdata.slot_id_1);
    // read_snapshot_slot_2.execute_stateful_alu(mdata.slot_id_2);
    // read_snapshot_slot_3.execute_stateful_alu(mdata.slot_id_3);
    // read_snapshot_slot_4.execute_stateful_alu(mdata.slot_id_4);
    // read_snapshot_slot_5.execute_stateful_alu(mdata.slot_id_5);
    // read_snapshot_slot_6.execute_stateful_alu(mdata.slot_id_6);
    // read_snapshot_slot_7.execute_stateful_alu(mdata.slot_id_7);
}

table gather_snapshot_to_response0 {
    actions {
        copy_snapshots_to_response0;
    }
    default_action : copy_snapshots_to_response0();
}

action echo_back_control() {
    // modify_field(mdata.temp_ip_placeholder, ipv4.dstAddr);
    // modify_field(ipv4.dstAddr, ipv4.srcAddr);
    // modify_field(ipv4.srcAddr, mdata.temp_ip_placeholder);
    swap(ipv4.dstAddr, ipv4.srcAddr);

    // modify_field(mdata.temp_mac_placeholder, ethernet.dstAddr);
    // modify_field(ethernet.dstAddr, ethernet.srcAddr);
    // modify_field(ethernet.srcAddr,  mdata.temp_mac_placeholder);
    swap(ethernet.dstAddr, ethernet.srcAddr);

    modify_field(ig_intr_md_for_tm.ucast_egress_port, ig_intr_md.ingress_port);
}

table response_back_control_response {
    actions {
        echo_back_control;
    }
    default_action : echo_back_control();
}

/*
action do_copy_to_slot1() {
    modify_field(myPoll.slot1, mdata.temp_output_placeholder);
}

table copy_to_slot1 {
    actions {
        do_copy_to_slot1;
    }
    default_action : do_copy_to_slot1();
}
*/

action do_copy_to_slot0() {
    modify_field(myPoll.slot0, mdata.temp_output_placeholder);
}

table copy_to_slot0 {
    actions {
        do_copy_to_slot0;
    }
    default_action : do_copy_to_slot0();
}

/*
action do_compare_id1_s2() {
    subtract(mdata.is_slot1_invalid, mdata.temp_max_slot1, mdata.last_time_zone);
}

table compare_id1_s2 {
    actions {
        do_compare_id1_s2;
    }
    default_action : do_compare_id1_s2();
}

action do_compare_id1_s1() {
    max(mdata.temp_max_slot1, mdata.slot_id_1, mdata.last_time_zone);
}

table compare_id1_s1 {
    actions {
        do_compare_id1_s1;
    }
    default_action : do_compare_id1_s1();
}
*/

action do_compare_id0_s2() {
    subtract(mdata.is_slot0_invalid, mdata.temp_max_slot0, mdata.last_time_zone);
}

table compare_id0_s2 {
    actions {
        do_compare_id0_s2;
    }
    default_action : do_compare_id0_s2();
}

action do_compare_id0_s1() {
    max(mdata.temp_max_slot0, mdata.truncated_slot_id, mdata.last_time_zone);
}

table compare_id0_s1 {
    actions {
        do_compare_id0_s1;
    }
    default_action : do_compare_id0_s1();
}

/*
action do_compare_valid_bits() {
    bit_or(mdata.slot_validation, mdata.is_slot0_invalid, mdata.is_slot1_invalid);
}

table compare_valid_bits {
    actions {
        do_compare_valid_bits;
    }
    default_action : do_compare_valid_bits();
}
*/

control ingress {
    /* if this is a control plane packet*/
    apply(on_receiving_new_data1);
    // apply(on_receiving_new_data2);
    if (valid(myPoll)) {
        apply(on_receiving_new_data2);
        apply(on_receiving_control_packet);
        /* compare truncated_slot_id and last_time_zone*/
        apply(compare_id0_s1);
        apply(compare_id0_s2);

        // apply(compare_id1_s1);
        // apply(compare_id1_s2);

        if (mdata.is_slot0_invalid == 0) {
            apply(gather_snapshot_to_response0);
            // modify_field(myPoll.slot0, mdata.temp_output_placeholder);
            apply(copy_to_slot0);

            /*
            apply(gather_snapshot_to_response1);
            // modify_field(myPoll.slot1, mdata.temp_output_placeholder);
            apply(copy_to_slot1);
            */
        }
        // apply(compare_id1_s1);
        // apply(compare_id1_s2);
        /*
        if (mdata.is_slot1_invalid == 0) {
            apply(gather_snapshot_to_response1);
            // modify_field(myPoll.slot1, mdata.temp_output_placeholder);
            apply(copy_to_slot1);
        }
        */
        /*
        apply(gather_snapshot_to_response2);
        apply(gather_snapshot_to_response3);
        apply(gather_snapshot_to_response4);
        apply(gather_snapshot_to_response5);
        apply(gather_snapshot_to_response6);
        apply(gather_snapshot_to_response7);
        */
        apply(response_back_control_response);
    /* or a data plane packet*/
    } else {
        apply(on_receiving_data_packet1);
        apply(on_receiving_data_packet2);
        apply(on_receiving_data_packet3);
        // apply(on_receiving_new_data);
        apply(check_first_packet1);
        apply(check_first_packet2);
        if (mdata.is_new_snapshot == 1) {
            apply(check_if_need_snapshot1);
            apply(check_if_need_snapshot2);
        }
    }
}

/*************************************************************************
 ****************  E G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/
control egress {
}
