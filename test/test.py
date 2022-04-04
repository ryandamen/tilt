from cassiopeia import ShardStatus
from collections import defaultdict
from pathlib2 import Path
import cassiopeia as cass


# import arrow
# import datetime
# import time
import json
# import numpy as np
# import pandas as pd

# Folder locations

# Project folders
project_folder = Path.cwd().parent

# Raw data storage
data_folder = project_folder / 'data'

# Out folder
out_folder = project_folder / 'out'
api_key_loc = data_folder / "dev_api_key.json"

with open(api_key_loc, 'r') as json_data:
    creds = json.load(json_data)
    api_key = creds['dev_api_key']
    cass.set_riot_api_key(api_key)


def get_shard():
    status = cass.get_status(region="NA")
    status = ShardStatus(region="NA")
    print(status.name)


get_shard()
