# tofino-flow-aggregation
Flow aggregation throughput benchmark on tofino switch(es)

### Quick starting
1. Build then run switch
    1. Build p4 on tofino switch
        ```
            cd $SDE
            . ~/tools/set_sde.bash
            ~/tools/p4_build.sh ~/chenishi/tofino-flow-aggregation/aggregatorv2.p4
        ```

    2. Run compiled model in an terminal
        ```
            ./run_tofino_model.sh -p aggregatorv2
        ```

    3. Run switch in another terminal
        ```
            cd $SDE
            . ~/tools/set_sde.bash
            ./run_switchd.sh -p aggregatorv2
        ```

    4. Config control plane in terminal at step 3
        ```
            ucli
            port-add -/- 100G RS
            port-enb -/-
            (pm show)
            exit
            pd-aggregatorv2
            pd check_flow_direction add_entry nop ipv4_dstAddr 192.168.0.1
        ```

2. Run controller in **w1**
    1. Compile recver
        ```
            cd recver/
            gcc -Wall -o sniffex sniffex.c -lpcap -O2
        ```
    2. Disable ICMP destination unreachable message

    Reference: [Disable ICMP Unreachable replies](https://serverfault.com/questions/522709/disable-icmp-unreachable-replies)
        ```
            iptables -I OUTPUT -p icmp --icmp-type destination-unreachable -j DROP
        ```

        > Since we are using an informal ip proto (159), it is natural for us to get such warning
        However, such warning message will mess around the testbench, so we have to disable
        it.

    3. Run recver
        ```
            sudo ./sniffex enp178s0f0
        ```

      > You have to specify the NIC connected to tofino switch, in our case, it will be
      *enp178s0f0*


3. Run multiple monitors (in **w3**, **w4**)
    By default, the monitor number is **2**. You could use more monitors (up to 65536
    theoretically), however, you should modify P4 on the **MONITOR_NUMBER**
    (it could be dynamic, but I don't want to configure it per query)
    1. Compile the c sender
        ```
            cd sender/
            gcc icmp4_ll.c -o icmp4_ll -O2
        ```
        > sender is done by raw socket, so there is no need for pcap library

    2. Run sender
        ```
            sudo ./icmp4_ll
        ```
        > TODO: make all monitors execute concurrently
