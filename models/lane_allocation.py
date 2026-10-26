# We need to allocate the truck to parking bays with the least number of workload minutes. Each bay can also only hold 5 trucks.

"""Supply chain model: truck lane allocation.

Each arriving truck is allocated to the truck lane with the least workload,
measured in minutes of processing still waiting in that lane. Each lane can
only hold 5 trucks at a time.

Assumptions:
    - Processing time = a fixed base time plus extra minutes for each cargo type.
    - The extra minutes per cargo type are estimates that will be updated as
      the dashboard is in use and actual times are recorded.
    - Each cargo type is only counted once per truck.
    - Trucks in a lane are processed first come, first served.
"""


# Model logic 
# Make a single parking bay record to start the process
def make_lane(number, capacity=5, queue=None):
    """Create a single truck lane record.

    Args:
        number: the lane number shown to the driver (e.g. 1 to 5).
        capacity: maximum number of trucks the lane can hold. Defaults to 5.
        queue: optional list of processing times (minutes) of trucks already in the lane.

    Returns:
        A dictionary with "number", "capacity" and "queue" (a new list of processing times).
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
    """Create the five empty truck lanes at the border post, each with a capacity of 5.

    Returns:
        A list of five lane dictionaries numbered 1 to 5.
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
    """Calculate the total processing time for a truck based on its cargo types.

    Formula:
        processing time = base_time
                          + sum of goods_time for each unique declared cargo type
                          + other_goods_time (only if other goods were declared)

    Args:
        goods_names: list of cargo type keys (e.g. ["electronics", "chemicals"]),
            or a single key as a string. Unknown keys add no extra time.
        other_goods: text the driver typed in "Other goods". Empty means none.
        base_time: minutes to stamp the passport and check the manifest. Defaults to 4.0.
        goods_time: dictionary of extra minutes per cargo type.
        other_goods_time: extra minutes if other goods were declared. Defaults to 2.0.

    Returns:
        The total processing time in minutes.

    Example:
        calculate_processing_time(["chemicals", "food_beverages"]) = 4.0 + 3.0 + 2.0 = 9.0
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
    """Calculate the total minutes of processing waiting in a lane.

    Formula:
        workload = sum of the processing times of all trucks in the lane's queue

    Args:
        lane: a lane dictionary (see make_lane).

    Returns:
        The workload in minutes (0.0 for an empty lane).
    """
    return sum(lane["queue"], 0.0)

# Define the lanes that are eligible for allocation based on their capacity
def eligible_lanes(lanes):
    """Find the lanes that still have space for another truck.

    Args:
        lanes: list of lane dictionaries.

    Returns:
        A list of the lanes whose number of trucks is below their capacity.
    """
    result = []
    for lane in lanes:
        if len(lane["queue"]) < lane["capacity"]:
            result.append(lane)
    return result

# Define a function to allocate a truck to the lane with the least workload
def allocate_lane(lanes, goods_names, other_goods=""):
    """Allocate a truck to the eligible lane with the least workload.

    Rule:
        best lane = the lane with space that has the lowest workload (minutes);
        ties go to the lowest lane number.
    The truck's processing time is then added to the end of that lane's queue.

    Args:
        lanes: list of lane dictionaries. The chosen lane's queue is updated in place.
        goods_names: list of cargo type keys the truck is carrying.
        other_goods: text the driver typed in "Other goods". Empty means none.

    Returns:
        A dictionary with:
            "lane": the allocated lane number
            "predicted_wait_min": minutes of work ahead of this truck in the lane
            "processing_min": this truck's own processing time in minutes
        or None if every lane is full.
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
    """Remove the first truck from a lane after it has been processed.

    Args:
        lanes: list of lane dictionaries. The lane's queue is updated in place.
        lane_number: the number of the lane to remove the truck from.

    Returns:
        True if a truck was removed, False if the lane is empty or does not exist.
    """
    for lane in lanes:
        if lane["number"] == lane_number:
            if lane["queue"]:
                lane["queue"].pop(0)  # Remove the first truck in the queue
                return True
            else:
                return False  # No trucks to remove
    return False  # Lane not found
