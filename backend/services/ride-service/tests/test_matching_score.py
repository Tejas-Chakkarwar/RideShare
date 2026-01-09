import pytest
from app.utils.matching_utils import calculate_route_score, calculate_bearing, check_direction_alignment

def test_route_score():
    assert calculate_route_score(0) == 40
    assert calculate_route_score(0.5) == 40
    assert calculate_route_score(4.5) == 35
    assert calculate_route_score(9.0) == 30
    assert calculate_route_score(14.0) == 20
    assert calculate_route_score(16.0) == 0

def test_calculate_bearing():
    # North
    assert round(calculate_bearing(0, 0, 1, 0)) == 0
    # East
    assert round(calculate_bearing(0, 0, 0, 1)) == 90
    # South
    assert round(calculate_bearing(0, 0, -1, 0)) == 180
    # West
    assert round(calculate_bearing(0, 0, 0, -1)) == 270

def test_direction_alignment():
    # Case 1: Driver going North (0,0 -> 10,0). Pass dest at North (20,0). Aligned.
    assert check_direction_alignment(0, 0, 10, 0, 20, 0) == True
    
    # Case 2: Driver going North. Pass dest at South (-10,0). Diff = 180. Not Aligned.
    assert check_direction_alignment(0, 0, 10, 0, -10, 0) == False
    
    # Case 3: Driver going North. Pass dest North-East (10, 10). Bearing ~45. Diff 45. Borderline.
    # Note: calculate_bearing(0,0,10,10) is 45 deg.
    assert check_direction_alignment(0, 0, 10, 0, 10, 10) == True
