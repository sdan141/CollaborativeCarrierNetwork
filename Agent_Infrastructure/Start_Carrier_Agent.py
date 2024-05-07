from carrier import *
import threading
import json
import sys

if __name__ == "__main__":
    carrier = Carrier(sys.argv[1], socket.gethostname(), sys.argv[2])
    carrier.connect(socket.gethostname(), 40000)

    data = {
        "action": "REGISTER",
        "name": carrier.name
        }
    dataObj = json.dumps(data)
    carrier.send_message(dataObj)

    # start listening thread
    client_thread = threading.Thread(target=carrier.start)
    client_thread.start()

    client_thread.join() # the main thread will wait at this point 
                         # until the listen_thread finishes its execution.
                         # ensures that all incoming messages are processed 
                         # before moving on or terminating the program

    #carrier.disconnect()