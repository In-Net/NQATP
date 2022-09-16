'''
After the monitor is chosen, we have to update the chosen node(s)' bias, most of the
time increase their cost (reduce preference)
'''

def update_weight(weights:list, pos: int):
    if isinstance(pos, list):
        for p in pos:
            weights[p] += 10
    elif isinstance(pos, int):
        weights[pos] += 10
    else:
        return
