# We need to allocate the truck to parking bays with the least number of workload minutes. Each bay can also only hold 5 trucks.


# Model logic 
# Make a single parking bay record to start the process
def make_lane(number, capacity=5, queue=None):
    if queue:
        queues = list(queue)
    else:
        queues = []

    single_lane = {"number": number,
                   "capacity": capacity,
                   "queue": queues
                   }
    return single_lane

# Five parking lanes
def default_lanes():
    lanes = []
    for i in range(1, 6):
        lanes.append(make_lane(i, capacity=5))
    return lanes


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
def calculate_processing_time(goods_names, other_goods="", base_time=base_time, goods_time=goods_time, other_goods_time=other_goods_time):
    # Single cargo is string and not list 
    if isinstance(goods_names, str):
        goods_names = [goods_names]
    total_time = base_time
    # count each cargo type only once
    unique_goods = set()
    for k in goods_names:
        unique_goods.add(k)

    for goods in unique_goods:
        if goods in goods_time:
            total_time += goods_time[goods]
    if other_goods and other_goods.strip():
        total_time += other_goods_time
    return total_time

# Define the total time in minutes it takes to process trucks in a queue
def lane_workload(lane):
    return sum(lane["queue"], 0.0)

# Define the lanes that are eligible for allocation based on their capacity
def eligible_lanes(lanes):
    result = []
    for lane in lanes:
        if len(lane["queue"]) < lane["capacity"]:
            result.append(lane)
    return result

# Define a function to allocate a truck to the lane with the least workload
def allocate_lane(lanes, goods_names, other_goods=""):
    goods_names = list(goods_names)  # Make sure that goods_names is a list
    processing_time = calculate_processing_time(goods_names, other_goods)
    options = eligible_lanes(lanes)
    if not options:
        return None  # No eligible lanes available
    # Pick the lane with the least workload; ties go to the lowest lane number
    def lane_score(lane):
        return lane_workload(lane), lane["number"]
    best_lane = min(options, key=lane_score)
    predicted_wait = lane_workload(best_lane)
    best_lane["queue"].append(processing_time)
    return {
        "lane": best_lane["number"],
        "predicted_wait_min": round(predicted_wait, 2),
        "processing_min": round(processing_time, 2),
    }

# Remove a truck from a lane after its been processed
def remove_truck(lanes, lane_number):
    for lane in lanes:
        if lane["number"] == lane_number:
            if lane["queue"]:
                lane["queue"].pop(0)  # Remove the first truck in the queue
                return True
            else:
                return False  # No trucks to remove
    return False  # Lane not found
