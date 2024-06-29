#!/bin/bash

commands=(
"python3 auctioneer_main.py"
"python3 carrier_main.py shachar"
"python3 carrier_main.py max"
"python3 carrier_main.py lorenz"
"python3 carrier_main.py lorenz"
)

for cmd in "${commands[@]}"; do
    gnome-terminal -- bash -c "$cmd; bash"
done
