#!/usr/bin/env python2
from argparse import ArgumentParser
import json

"""
input: monitor indices
output: aggregation bitmasks for each monitor
"""
def find_aggregation_bitmap(monitors):
	size = len(monitors)
	aggr_bitmaps = [[0] * 5 for i in range(size)]
	for index, aggr_bitmap in enumerate(aggr_bitmaps):
		aggr_bitmap[0] = 2 ** (size - index - 1)
	return []

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument("-r", "--read", help="Read location of query-entry mapping json", dest="read_loc", default="~/git/catchment-basin-seeker/gurobi/placement.json")
	args = parser.parse_args()
		
	with open(args.read_loc) as f:
		data = json.load(f)
		for query in data["queries"]:
			monitors = sorted(query["monitors"])
			print monitors