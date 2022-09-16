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
#define MIN_TABLE_SIZE 1

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
        ttl : TTL_BIT;
        bitmap : BITMAP_BIT;
        seq  : 16;
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
 /*
header_type mdata_t {
    fields {
        hello : 8;
    }
}

metadata mdata_t mdata;
*/
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

action nop() {

}

action discard() {
    modify_field(ig_intr_md_for_tm.drop_ctl, 1);
}

action do_backward_route() {
    modify_field(ig_intr_md_for_tm.ucast_egress_port, backward_route[0].nexthop);
    pop(backward_route, 1);
    add_to_field(myforward.hop_cnt, -1);
}

table route_backward {
    actions {
        do_backward_route;
    }
    default_action : do_backward_route();
    size: MIN_TABLE_SIZE;
}

table stop_mcast {
    actions {
        discard;
    }
    default_action: discard();
    size: MIN_TABLE_SIZE;
}

action do_console() {
    add_to_field(myforward.hop_cnt, 1);
    push(backward_route, 1);
    add_header(backward_route[0]);
    modify_field(backward_route[0].nexthop, ig_intr_md.ingress_port);
    clone_ingress_pkt_to_egress(1);
}

table console_backward_route {
    actions {
        do_console;
    }
    default_action: do_console();
    size: MIN_TABLE_SIZE
}

action do_patch() {
    modify_field(backward_route[0].bos, 1);
}

table patch_cnt {
    actions {
        do_patch;
    }
    default_action: do_patch();
    size: MIN_TABLE_SIZE;
}

control ingress {
    if (valid(myforward)) {
        // forwarder won't have its character set by control plane table
        if (myforward.dstID == 0) {
            apply(route_backward);
            /*
            // this is a response that destinated for collector
            modify_field(ig_intr_md_for_tm.ucast_egress_port, backward_route[0].nexthop);
            pop(backward_route, 1);
            add_to_field(myforward.hop_cnt, -1);
            */
        } else {

            // this is a request from collector
            if (myforward.ttl == 0) {
                apply(stop_mcast);
                /*
                modify_field(ig_intr_md_for_tm.drop_ctl, 1);
                */
            } else {
                apply(console_backward_route);
                if (myforward.hop_cnt == 1) {
                    apply(patch_cnt);
                }
                /*
                add_to_field(myforward.ttl, -1);
                // also record backward port for latter response
                add_to_field(myforward.hop_cnt, 1);
                push(backward_route, 1);
                add_header(backward_route[0]);
                if (myforward.hop_cnt == 1) {
                    modify_field(backward_route[0].bos, 1);
                }
                modify_field(backward_route[0].nexthop, ig_intr_md.ingress_port);
                clone_ingress_pkt_to_egress(1);
                */
            }
        }
    }
}

/*************************************************************************
 ****************  E G R E S S   P R O C E S S I N G   *******************
 *************************************************************************/
control egress {
}
