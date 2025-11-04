"""
Simple validation script for circadian improvements
Tests the output format without needing imports
"""

def validate_timeline_slot(slot):
    """Validate a single timeline slot has all required fields"""
    required_fields = [
        "time",
        "energy_level",
        "slot_index",
        "zone",
        "zone_color",
        "zone_label",
        "motivation_message"
    ]

    for field in required_fields:
        if field not in slot:
            return False, f"Missing field: {field}"

    # Validate zone_color values
    if slot["zone_color"] not in ["green", "orange", "red"]:
        return False, f"Invalid zone_color: {slot['zone_color']}"

    # Validate energy level matches zone color
    energy = slot["energy_level"]
    color = slot["zone_color"]

    if color == "green" and energy < 75:
        return False, f"Green zone has energy < 75: {energy}"
    elif color == "orange" and not (50 <= energy < 75):
        return False, f"Orange zone energy not in range 50-74: {energy}"
    elif color == "red" and energy >= 50:
        return False, f"Red zone has energy >= 50: {energy}"

    return True, "OK"


def validate_timeline(timeline):
    """Validate complete timeline"""
    if len(timeline) != 96:
        return False, f"Timeline should have 96 slots, has {len(timeline)}"

    # Validate each slot
    for i, slot in enumerate(timeline):
        valid, msg = validate_timeline_slot(slot)
        if not valid:
            return False, f"Slot {i} ({slot.get('time', 'unknown')}): {msg}"

    # Check distribution
    total = len(timeline)
    green_count = sum(1 for s in timeline if s["zone_color"] == "green")
    red_count = sum(1 for s in timeline if s["zone_color"] == "red")

    green_pct = (green_count / total) * 100
    red_pct = (red_count / total) * 100

    if green_pct < 20.0:
        return False, f"Green zones only {green_pct:.1f}%, need >= 20%"

    if red_pct > 40.0:
        return False, f"Red zones {red_pct:.1f}%, need <= 40%"

    return True, f"✅ Valid timeline: {green_count} green ({green_pct:.1f}%), {red_count} red ({red_pct:.1f}%)"


# Example expected slot format
EXPECTED_SLOT_FORMAT = {
    "time": "08:00",
    "energy_level": 85,
    "slot_index": 32,
    "zone": "peak",
    "zone_color": "green",
    "zone_label": "High Energy",
    "motivation_message": "🎯 Perfect time for your most important tasks!"
}

if __name__ == "__main__":
    print("=" * 80)
    print("CIRCADIAN ENERGY ZONES - EXPECTED OUTPUT FORMAT")
    print("=" * 80)
    print()
    print("Example timeline slot (JSON format):")
    print()
    import json
    print(json.dumps(EXPECTED_SLOT_FORMAT, indent=2))
    print()
    print("=" * 80)
    print("VALIDATION RULES")
    print("=" * 80)
    print()
    print("✓ Timeline must have exactly 96 slots (15-minute intervals)")
    print("✓ Each slot must have: time, energy_level, slot_index, zone, zone_color, zone_label, motivation_message")
    print("✓ zone_color must be: 'green', 'orange', or 'red'")
    print("✓ Energy levels must match colors:")
    print("  - green: energy_level >= 75")
    print("  - orange: 50 <= energy_level < 75")
    print("  - red: energy_level < 50")
    print("✓ Distribution must be motivating:")
    print("  - At least 20% green zones (minimum ~19 slots)")
    print("  - Maximum 40% red zones (maximum ~38 slots)")
    print()
    print("=" * 80)
    print("To test actual output, call validate_timeline(your_timeline_data)")
    print("=" * 80)
