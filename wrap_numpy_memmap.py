import sys
import numpy as np

bin_file = sys.argv[1]
shape_file = sys.argv[2]

with open(shape_file) as f:
    shape = tuple(map(int, f.read().strip().split(',')))

# Wrap as memmap
mm = np.memmap(bin_file, dtype='float64', mode='r', shape=shape)

# Save as .npy (optional, for fast future loads)
np.save(bin_file.replace('.bin', '.npy'), mm)
print("Wrote .npy file")

# Test: access one node's time history for temperature
# (e.g. all times, node 0, field 0)
# print(mm[:,0,0])
