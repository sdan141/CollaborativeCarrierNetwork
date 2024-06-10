#!/bin/bash

commands=(
"cd tuhh/SW-D/backupsGroup09/AMS; python3 auctioneer_main.py"
"cd tuhh/SW-D/backupsGroup09/AMS; python3 carrier_main.py shachar"
"cd tuhh/SW-D/backupsGroup09/AMS; python3 carrier_main.py max"
"cd tuhh/SW-D/backupsGroup09/AMS; python3 carrier_main.py lorenz"
"cd tuhh/SW-D/backupsGroup09/AMS; python3 carrier_main.py lorenz"
)

for cmd in "${commands[@]}"; do
    gnome-terminal -- bash -c "$cmd; bash"
done
