# We need to allocate the truck to parking bays with the least number of workload minutes. Each bay can also only hold 5 trucks.

# Model logic 
# Make a single parking bay record to start the process
def make_lane(number, capacity=5, queue=None):
    """
This function creates a parking lane with all its relevant information.
Rule:
    Each lane has a number,capacity and a specific queue.
Inputs:
    number: This is the number of the lane.
    capacity: this shows how many trucks can fit into the lane (this is a default of 5).
    queue: this is the processing times of trucks already in that lane.
Output:
    The output is a dictionary with the lane's relevant information.
Assumptions:
    Each lane can hold a max of 5 trucks unless changed.
    If no specific queue is given, the lane automatically starts with an empty queue.
"""
    
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
    """
    this function creates the five parking lanes inside the lebombo border post.
    Rule:
       it creates lanes numbered 1 to 5.
    Inputs:
       there are no inputs for this function.
    Output:
       this will be a list of the five parking lanes.
    Assumptions:
       There are 5 parking lanes, each with a max capacity of 5 trucks.
       The lanes all start with empty queues.
    """
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
    """
    this function calculates the processing time for a truck based on the types of goods that it is carrying.
    Rule:
       it starts with a base processing time of 4 minutes then adds extra time based on the types of goods that it is carrying.
       the standard is to count each goods category only once and then add 2 minutes if any other goods are specified outside of the common goods. 
    Inputs:
       goods_names – this is the types of goods the truck is carrying.
       other_goods – this is any other goods specified outside of the common goods
       base_time – this is the standard processing time.
       goods_time – this is the extra minutes for each category of goods
       other_goods_time – this is extra minutes for other goods outside of the standard
    Output:
       this is the total estimated processing time in minutes
    Assumptions:
       the processing times are only estimates.
       duplicate categories will only be counted once
       Unknown category in goods_names: this will be ignored
       each goods category adds time without being influenced by others
    """

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
    """
    Rule: this adds together all the processing times of the trucks currently in this lane;s queue
    Input: the input is the lane's number which is the lane containing the queue of trucks and their processing times.
    Output: the total workload of this lane in minutes
    """
    return sum(lane["queue"], 0.0)

# Define the lanes that are eligible for allocation based on their capacity
def eligible_lanes(lanes):
    """
    Rule: this function checks how many trucks are currently in each lane and then compares it to the max capacity of each lane. It only includes lanes that are not full.
    Input: this is lanes which is a list of all the parking lanes and their relevant information 
    Output: a list of lanes that all have space for another truck
    Assumption: that each entry into a lane's queue represents a truck and that the max capacity of each lane if 5 trucks. 
    """
    result = []
    for lane in lanes:
        if len(lane["queue"]) < lane["capacity"]:
            result.append(lane)
    return result

# Define a function to allocate a truck to the lane with the least workload
def allocate_lane(lanes, goods_names, other_goods=""):
    """
    Rule: calculates the pro essing time of the truck based on the goods that it is carrying and checks which lanes stil have space. 
    It then selects the lane with the lowest workload in minutes and if 2 lanes have the same workload it selects the one with the lowest number. 
    Finally, it will add the calculated processing time to the lane which was selected. 
    Inputs: the inputs are the list of parking lanes with their current queues, the types of goods that are being carried and any additional goods that are not in the common goods. 
    Output: the allocated lane, predicted waiting times and estimated processing times both in minutes. it returns none in the queue is full.
    """
    # Single cargo is string and not list, so wrap it before converting
    if isinstance(goods_names, str):
        goods_names = [goods_names]
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
    """
    Rule: located the lane, checks whether there are trucks in the queue, and then removes the first truck in the queue. 
    Inputs: the list of lanes and their information and the number of the lane from which the truck must be removed.
    Output: returns true is the removal was successful and false if the lane is empty. 
    """
    for lane in lanes:
        if lane["number"] == lane_number:
            if lane["queue"]:
                lane["queue"].pop(0)  # Remove the first truck in the queue
                return True
            else:
                return False  # No trucks to remove
    return False  # Lane not found
