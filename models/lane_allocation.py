# We need to allocate the truck to parking bays with the least number of workload minutes. Each bay can also only 5 trucks.

# Make a single parking bay record to start the process
def make_lane(number, capacity=5, queue=None   ):
    return {"number": number, 
            "capacity": capacity, 
            "queue": list(queue) if queue else []
            }

# Five parking lanes
def default_lanes():
     for i in range(1, 6):
        return make_lane(i,capacity=5)


# standard base processing time to stamp passport and check manifest estimate:
base_time = 4.0 #minutes

#Dictionary representing the estimated extra minutes it takes to process specific cargo types. These values are all assumptions that will be updated as the dashboard is in use and actual times are recorded.
goods_time = {
    "electronics": 1.5, 
    "furniture": 0.5,
    "clothing_textiles": 0.5,
    "chemicals": 3.0,
    "food_beverages": 2.0,
    "automotive_parts": 1.0,
    "machinery_parts": 1.0,
    "plastics": 0.5,
    "building_materials": 0.5,
    "paper_products": 0.5
} # in minutes
other_goods_time = 2.0 # in minutes

# define a function to calculate the total processing time for a truck based on its cargo types
def calculate_processing_time(goods_keys, other_goods="", base_time=base_time, goods_time=goods_time, other_goods_time=other_goods_time):
    total_time = base_time
    for key in goods_keys:
        if key in goods_time:
            total_time += goods_time[key]
    if other_goods and other_goods.strip():
            total_time += other_goods_time
    return total_time

# Define the total time in minutes it takes to process trucks in a queue
def lane_workload(lane):
    return sum(lane["queue"])  







