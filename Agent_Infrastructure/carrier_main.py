import sys 
from carrier import Carrier

if __name__ == "__main__":
    carrier = Carrier(sys.argv[1], config_file=None, deliveries_file=None)
    carrier.start()