import sqlalchemy as db
import pandas as pd
import os
from datetime import datetime, timedelta
from threading import Lock
import time

engine = None

print("K_SERVICE: ", os.getenv('K_SERVICE'))

# Check if running in google cloud, by checking the environment variable K_SERVICE
if os.getenv('K_SERVICE') is not None:
    engine = db.create_engine(os.environ['DB_CONNECTION_STRING'])
else:
    host = 'host.docker.internal' # Requires that the host machine is running google cloud proxy
    database = 'EffektAnalysisDB'
    engine = db.create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{host}/{database}")

cache = {}
lock = Lock()

def get_df(table_name):
    with lock:
        current_time = datetime.now()
        cache_entry = cache.get(table_name, {})
        # Check if data is already being queried or is in cache and still valid
        if 'querying' in cache_entry:
            should_wait = True
        elif 'data' in cache_entry and (current_time - cache_entry['timestamp']) < timedelta(hours=12):
            print(f"Returning cached data for {table_name}")
            return cache_entry['data']
        else:
            # Mark as querying and proceed to fetch
            cache[table_name] = {'querying': True}
            should_wait = False

    if should_wait:
        # Wait for data to be available
        print(f"Waiting for {table_name} data to be cached")
        start = datetime.now()
        while 'querying' in cache.get(table_name, {}):
            time.sleep(0.1)  # Adjust sleep time as needed
            if datetime.now() - start > timedelta(seconds=30):  # Timeout after 30 seconds
                print(f"Timeout while waiting for {table_name}. Attempting to fetch directly.")
                break  # Break the loop and attempt to fetch the data directly

    # Fetch and cache data
    with lock:
        # Check again if data is now available or still needs fetching
        if 'data' not in cache.get(table_name, {}) or datetime.now() - cache[table_name]['timestamp'] > timedelta(hours=12):
            print(f"Fetching data for {table_name}")
            df = pd.read_sql_table(table_name=table_name, con=engine.connect())
            cache[table_name] = {'data': df, 'timestamp': datetime.now()}
        else:
            df = cache[table_name]['data']

    return df
