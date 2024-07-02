import sys 
from random import randint
from carrier import Carrier

if __name__ == "__main__":
    carrier_id = sys.argv[1] if len(sys.argv)>1 else "carrier_"+str(randint(0,10))
    carrier = Carrier(carrier_id, path_config=None)
    carrier.start()

