import mech_dpf
import Ans.DataProcessing as dpf 
import os
import wbjn
import struct
import subprocess

mech_dpf.setExtAPI(ExtAPI)

solution = DataModel.GetObjectsByName("Nominal Stress - 150 MPa - Cyclic")[0].Solution
projectDir = solution.WorkingDir

# --- CHANGE: List of node numbers to extract ---
nodeIds = [10, 11, 12]  # <--- your target nodes

# Get the data source (i.e. result file)
dataSource = dpf.DataSources(solution.Parent.ResultFileName)

# Create result operator for temperature
myRes = dpf.operators.result.structural_temperature()

# --- NEW: create one operator per stress component ---
Stress_X  = dpf.operators.result.stress_X()
Stress_Y  = dpf.operators.result.stress_Y()
Stress_Z  = dpf.operators.result.stress_Z()
Stress_XY = dpf.operators.result.stress_XY()
Stress_YZ = dpf.operators.result.stress_YZ()
Stress_XZ = dpf.operators.result.stress_XZ()

# Get the time data corresponding to result sets
time_provider = dpf.operators.metadata.time_freq_provider()
time_provider.inputs.data_sources.Connect(dataSource)
numSets = time_provider.outputs.time_freq_support.GetData().NumberSets
timeids = time_provider.outputs.time_freq_support.GetData().TimeFreqs.Data

result_set_ids = [i+1 for i in range(numSets)]

# Create time scoping operator
time_scoping = dpf.Scoping()
time_scoping.Location = dpf.locations.time_freq_sets
time_scoping.Ids = result_set_ids

# Provide inputs to all operators
myRes.inputs.data_sources.Connect(dataSource)
myRes.inputs.time_scoping.Connect(time_scoping)
for op in (Stress_X, Stress_Y, Stress_Z, Stress_XY, Stress_YZ, Stress_XZ):
    op.inputs.data_sources.Connect(dataSource)
    op.inputs.time_scoping.Connect(time_scoping)

myRes_fields   = myRes.outputs.fields_container.GetData()
sx_fields      = Stress_X.outputs.fields_container.GetData()
sy_fields      = Stress_Y.outputs.fields_container.GetData()
sz_fields      = Stress_Z.outputs.fields_container.GetData()
sxy_fields     = Stress_XY.outputs.fields_container.GetData()
syz_fields     = Stress_YZ.outputs.fields_container.GetData()
sxz_fields     = Stress_XZ.outputs.fields_container.GetData()

num_fields = 7
num_nodes = len(nodeIds)

# ---- Write binary in shape (time, node, field) ----
bin_path = os.path.join(projectDir, 'nodal_tensor.bin')
shape_path = os.path.join(projectDir, 'nodal_tensor_shape.txt')
node_path = os.path.join(projectDir, 'nodal_tensor_nodes.txt')

with open(bin_path, 'wb') as fout:
    for t in range(numSets):
        for n, nodeId in enumerate(nodeIds):
            vals = [
                myRes_fields[t].GetEntityDataById(nodeId)[0],
                sx_fields[t].GetEntityDataById(nodeId)[0],
                sy_fields[t].GetEntityDataById(nodeId)[0],
                sz_fields[t].GetEntityDataById(nodeId)[0],
                sxy_fields[t].GetEntityDataById(nodeId)[0],
                syz_fields[t].GetEntityDataById(nodeId)[0],
                sxz_fields[t].GetEntityDataById(nodeId)[0]
            ]
            fout.write(struct.pack('<7d', *vals))

# Write out shape info
with open(shape_path, 'w') as fshape:
    fshape.write('%d,%d,%d\n' % (numSets, num_nodes, num_fields))
with open(node_path, 'w') as fnodes:
    fshape = ",".join(str(nid) for nid in nodeIds)
    fnodes.write(fshape)

print("Wrote binary data to", bin_path)
print("Wrote shape to", shape_path)
print("Wrote node IDs to", node_path)

# ---- Call Python subprocess to wrap as numpy memmap ----
python_code = os.path.join(projectDir, 'wrap_numpy_memmap.py')
subprocess.call(['python', python_code, bin_path, shape_path])
