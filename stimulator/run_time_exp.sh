#!/bin/bash

dot_per_box=10
hop_size=250
total_hop_steps=12
exec_time_output_dstfile="/home/lthpc/git/catchment-basin-seeker/plot/exec_time.csv"

# clear output dst first
> $exec_time_output_dstfile

for ((hops=1; hops<=total_hop_steps; hops++ ))
do
	let item_name=hops*hop_size
	if [ $hops -eq 1 ];
	then
		echo -n "$item_name" >> $exec_time_output_dstfile
	else
		echo -n ", $item_name" >> $exec_time_output_dstfile
	fi
done
printf "\n" >> $exec_time_output_dstfile

for (( counter=dot_per_box; counter>0; counter-- ))
do
	# let query_counts=hops*hop_size
	# echo "$query_counts" >> $exec_time_output_dstfile
	# printf "\n"
	for (( hops=1; hops<=total_hop_steps; hops++ ))
	do
		let query_counts=hops*hop_size
		python3 data/gen_query.py -n $query_counts -e 4
		if [ $hops -eq 1 ];
		then
			python gurobi/bipartite.py | grep "iterations) in" | awk '{printf $8}' >> $exec_time_output_dstfile
		else
			python gurobi/bipartite.py | grep "iterations) in" | awk '{printf ", %s", $8}' >> $exec_time_output_dstfile
		fi
		# python gurobi/bipartite.py | grep "iterations) in" | awk '{print $8}' >> $exec_time_output_dstfile
		# echo -n "$counter "
		# a little sleep to try to cool down machine
		sleep 10
	done
	printf "\n" >> $exec_time_output_dstfile
done
