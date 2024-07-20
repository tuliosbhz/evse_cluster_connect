# Add raftos package to PYTHONPATH so we don't need to install it to run example
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../"

# Remove previous data
rm -f *.log
rm -f *.storage
rm -f *.state_machine

#Start
../venv/bin/python3 cp_node_v301.py ini_loc_cluster/node1_conf_local.ini &
../venv/bin/python3 cp_node_v301.py ini_loc_cluster/node2_conf_local.ini &
../venv/bin/python3 cp_node_v301.py ini_loc_cluster/node3_conf_local.ini &
