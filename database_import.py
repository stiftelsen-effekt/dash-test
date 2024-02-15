import sqlalchemy as db
import pandas as pd
import os

engine = None

print("K_SERVICE: ", os.getenv('K_SERVICE'))

# Check if running in google cloud, by checking the environment variable K_SERVICE
if os.getenv('K_SERVICE') is not None:
    engine = db.create_engine(os.environ['DB_CONNECTION_STRING'])
else:
    host = 'host.docker.internal' # Requires that the host machine is running google cloud proxy
    database = 'EffektAnalysisDB'
    engine = db.create_engine(f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{host}/{database}")

# Initialize a cache dictionary
cache = {}

def get_df(table_name):
    current_time = datetime.now()
    
    # Check if the table_name is in the cache and if the cache is still valid
    if table_name in cache and (current_time - cache[table_name]['timestamp']) < timedelta(hours=12):
        return cache[table_name]['data']
    else:
        # If the data is not in cache or cache is old, read from the database
        df = pd.read_sql_table(table_name=table_name, con=engine.connect())
        
        # Update the cache
        cache[table_name] = {'data': df, 'timestamp': current_time}
        return df



