from carrier import *
import json
import pandas as pd

def TR_to_send(name):
    deliveries_df = pd.read_csv("example_TR.csv")
    print(f"all deliveries: {deliveries_df}")
    below_threshold = deliveries_df[(deliveries_df.profit).astype(float)<100]
    print(f"deliveries below threshhold: {below_threshold}")
    if len(below_threshold) > 0:
        data = {
            "action"        : "TR", 
            "name"          : name, 
            "pickup_long"   : below_threshold.pickup_long.values[0],
            "pickup_lat"    : below_threshold.pickup_lat.values[0],
            "delivery_long" : below_threshold.delivery_long.values[0],
            "delivery_lat"  : below_threshold.delivery_lat.values[0]
        }

    else:
        data =   {
            "action" : "NO_TR", 
            "name"   : name
        }
    print(f"transport request to send: {data}")
    return data 


if __name__ == "__main__":
    carrier = Carrier(socket.gethostname(), 3000)
    carrier.connect(socket.gethostname(), 40000)

    data = {
        "action": "REGISTER",
        "name": "carrier A"
        }
    dataObj = json.dumps(data)
    carrier.send_message(dataObj)

    response = carrier.receive_message()
    if response['action'] == 'ACK':
        print(f"Received message: {response['message']}")
              
    response = carrier.receive_message() 
    if response['action'] == 'REQUEST_TR':
        TR = TR_to_send(carrier.name)
        TRObj = json.dumps(TR)
        carrier.send_message(TRObj)

    carrier.disconnect()