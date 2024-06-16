import sys 
from carrier import Carrier

if __name__ == "__main__":
    carrier = Carrier(sys.argv[1], path_config=None, path_deliveries=None)
    carrier.start()