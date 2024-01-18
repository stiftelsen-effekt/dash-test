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

def get_df(table_name):
    return pd.read_sql_table(table_name=table_name,con=engine.connect())


