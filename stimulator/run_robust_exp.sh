#!/bin/bash

dot_per_box=10
starting_point=25
hop_size=5
total_hop_steps=16
query_size=2000

exec_time_output_dstfile="/home/lthpc/git/catchment-basin-seeker/plot/exec_robust.csv"

# clear output dst first
> $exec_time_output_dstfile

for ((hops=0; hops<total_hop_steps; hops++ ))
do
	let item_name=hops*hop_size+starting_point
	if [ $hops -eq 0 ];
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
	for (( hops=0; hops<total_hop_steps; hops++ ))
	do
		let ratio=hops*hop_size+starting_point
		python3 data/gen_query.py -n $query_size -e 4 -m 1 -p $ratio
		if [ $hops -eq 0 ];
		then
			python gurobi/bipartite.py | grep "variance =" | awk '{printf $7}' >> $exec_time_output_dstfile
		else
			python gurobi/bipartite.py | grep "variance =" | awk '{printf ", %s", $7}' >> $exec_time_output_dstfile
			# python gurobi/bipartite.py | grep "iterations) in" | awk '{printf ", %s", $8}' >> $exec_time_output_dstfile
		fi
		# python gurobi/bipartite.py | grep "iterations) in" | awk '{print $8}' >> $exec_time_output_dstfile
		# echo -n "$counter "
		# a little sleep to try to cool down machine
		sleep 10
	done
	printf "\n" >> $exec_time_output_dstfile
done
