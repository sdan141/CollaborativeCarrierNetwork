#!/bin/bash

commands=("python3 auctioneer_main.py")

for (( i=0; i<$1; i++ )); do
    commands+=("python3 carrier_main.py carrier_$i")
done

for cmd in "${commands[@]}"; do
    gnome-terminal -- bash -c "$cmd; bash"
done