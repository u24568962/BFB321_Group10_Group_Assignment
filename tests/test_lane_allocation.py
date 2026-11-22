# Unit tests for supply_chain lane allocations, expected values hand calculated
from supply_chain.lane_allocation import (allocate_lane, calculate_processing_time, default_lanes, make_lane, remove_truck)

def test_processing_time_two_categories():
    # 4.0 base + 1.5 electronics + 3.0 chemicals = 8.5
    assert calculate_processing_time(["electronics", "chemicals"]) == 8.5

def test_processing_time_counts_duplicates_once():
    # 4.0 + 2.0 food (only once) = 6.0
    assert calculate_processing_time(["food_beverages", "food_beverages"]) == 6.0

def test_processing_time_other_goods_adds_two_minutes():
    # 4.0 + 2.0 other = 6.0
    assert calculate_processing_time([], "office supplies") == 6.0

def test_processing_time_unknown_category_ignored():
    assert calculate_processing_time(["spaceships"]) == 4.0

def test_empty_lanes_tie_goes_to_lane_1():
    # all 5 lanes empty (workload 0) -> lowest lane number wins, no wait
    result = allocate_lane(default_lanes(), ["electronics"])
    assert result == {"lane": 1, "predicted_wait_min": 0.0, "processing_min": 5.5}

def test_picks_lane_with_least_workload():
    # lane 1 workload 10, lane 2 workload 4 -> lane 2, wait 4, processing 4 + 1.0 machinery = 5.0
    lanes = [make_lane(1, queue=[5.0, 5.0]), make_lane(2, queue=[4.0])]
    result = allocate_lane(lanes, ["machinery_parts"])
    assert result == {"lane": 2, "predicted_wait_min": 4.0, "processing_min": 5.0}
    assert lanes[1]["queue"] == [4.0, 5.0]  # truck added lane 2

def test_full_lanes_return_none():
    lanes = [make_lane(1, capacity=1, queue=[5.0])]
    assert allocate_lane(lanes, ["furniture"]) is None

def test_remove_truck():
    lanes = [make_lane(1, queue=[5.0, 6.0])]
    assert remove_truck(lanes, 1) is True
    assert lanes[0]["queue"] == [6.0]
    assert remove_truck(lanes, 9) is False  #lane doesnt exist
