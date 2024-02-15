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
        # Check if data is in cache and still valid
        if table_name in cache and (current_time - cache[table_name]['timestamp']) < timedelta(hours=12):
            if 'data' in cache[table_name]:  # Ensure data is present
                print(f"Returning cached data for {table_name}")
                return cache[table_name]['data']
            else:
                # If querying is in progress, wait
                pass
        else:
            # Mark as querying to block subsequent requests for the same table
            cache[table_name] = {'querying': True}

    # If data is not in cache or is stale, and no query is in progress
    if 'querying' in cache.get(table_name, {}):
        # Wait for the query to complete if another thread is working on it
        while 'querying' in cache.get(table_name, {}):
            time.sleep(0.1)  # Adjust sleep time as needed

        with lock:
            # Return the data after waiting
            if 'data' in cache[table_name]:
                print(f"Returning cached data for {table_name} after waiting")
                return cache[table_name]['data']

    # Only reach here if data needs to be queried and cached
    df = pd.read_sql_table(table_name=table_name, con=engine.connect())

    with lock:
        # Update the cache with the new data and timestamp
        cache[table_name] = {'data': df, 'timestamp': current_time}
        print(f"Querying database and caching data for {table_name}")

    return df
