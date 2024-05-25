import pandas as pd

def handle_file(uploaded_file):
    if 'file' not in uploaded_file:
        print("No file part") 
    
    file = uploaded_file['file']
    
    if file.filename == '':
        print("No selected file") 
    
    if file and allowed_file(file.filename):
        try:
            df = pd.read_excel(file)
            data = process_excel(df)
            return data
        except Exception as e:
            print(f"Error: {str(e)}") 
    
    print("File not allowed")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xls', 'xlsx'}

def process_excel(file):
    locations = []
    deliveries = []

    # Add depot
    depot = []
    depot.append(file.columns[1])
    depot.append(file.columns[2])
    depot = tuple(depot)
    locations.append(depot)
    
    # Add transport requests
    for row in range(1, len(file)):
        pickup_x = file.iloc[row, 1]
        pickup_y = file.iloc[row, 2]
        dropoff_x = file.iloc[row, 3]
        dropoff_y = file.iloc[row, 4]
        locations.append((pickup_x, pickup_y))
        locations.append((dropoff_x, dropoff_y))

    # Map deliveries
    multiplier = 0
    delivery_amount = int((len(locations) - 1 ) / 2)
    for i in range(0, delivery_amount):
        deliveries.append([i + (1 + multiplier), i + (2 + multiplier)])
        multiplier = multiplier + 1

    data = {
        'locations': locations,
        'deliveries': deliveries,
    }

    return data