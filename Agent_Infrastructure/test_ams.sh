#!/bin/bash

commands=(
"cd tuhh/SW-D/agent_comm; python3 auctioneer_init.py"
"cd tuhh/SW-D/agent_comm; python3 carrier_init.py shachar"
"cd tuhh/SW-D/agent_comm; python3 carrier_init.py max"
"cd tuhh/SW-D/agent_comm; python3 carrier_init.py lorenz"
"cd tuhh/SW-D/agent_comm; python3 carrier_init.py shachar"
)

for cmd in "${commands[@]}"; do
    gnome-terminal -- bash -c "$cmd; bash"
done
