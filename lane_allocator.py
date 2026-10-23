def allocate_truck_lane(lane_counts):
    """
    Allocate a truck to the lane with the fewest trucks.

    lane_counts: dictionary containing lane numbers and
                 the number of trucks in each lane.

    Returns the lane number selected.
    """

    # Find the smallest number of trucks
    fewest_trucks = min(lane_counts.values())

    # Find all lanes with the smallest number
    available_lanes = [
        lane for lane, count in lane_counts.items()
        if count == fewest_trucks
    ]

    # If tied, select the lane with the lowest number
    selected_lane = min(available_lanes)

    return selected_lane


# Example: current number of trucks in each lane
lane_counts = {
    1: 8,
    2: 5,
    3: 3,
    4: 6,
    5: 4
}

allocated_lane = allocate_truck_lane(lane_counts)

print(f"Truck allocated to Lane {allocated_lane}")