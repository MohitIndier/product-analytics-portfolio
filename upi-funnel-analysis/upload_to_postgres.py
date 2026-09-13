import pandas as pd
from sqlalchemy import create_engine

csv_file = r"C:\likeit\creators\upi_transactions_v4.csv"
df = pd.read_csv(csv_file)

engine = create_engine('postgresql://postgres:{password}5@localhost:5432/postgres')

table_name = "upi_transactions"
schema_name = "upi_funnel"

df.to_sql(table_name, engine, index=False, if_exists='replace', schema=schema_name)

print(f"Table '{schema_name}.{table_name}' created and data uploaded successfully!")
