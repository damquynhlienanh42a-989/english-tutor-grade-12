import json
import os

def load_unit(unit_number):
    """
    Load a specific unit JSON file.
    
    Args:
        unit_number (int): The unit number (1-10)
    
    Returns:
        dict: The unit data or None if not found
    """
    file_path = f"units/unit{unit_number}.json"
    
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading unit {unit_number}: {e}")
        return None

def list_available_units():
    """
    List all available units by scanning the units/ directory.
    
    Returns:
        list: List of available unit numbers sorted ascending
    """
    available = []
    units_dir = "units"
    if os.path.exists(units_dir):
        for filename in os.listdir(units_dir):
            if filename.startswith("unit") and filename.endswith(".json"):
                try:
                    num = int(filename[4:-5])
                    available.append(num)
                except ValueError:
                    pass
    return sorted(available)
