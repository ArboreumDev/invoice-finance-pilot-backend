from typing import Dict

def remove_none_entries(d: Dict):
    return {k:v for k,v in d.items() if v != None}

