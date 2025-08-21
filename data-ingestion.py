import pandas as pd
import mysql.connector
from sqlalchemy import create_engine

# ---- Database connection ----
username = "root"
password = "1a0qaeta"
host = "localhost"
database = "super_market"

# Create SQLAlchemy engine
engine = create_engine(f"mysql+mysqlconnector://{username}:{password}@{host}/{database}")

# ---- Read Excel ----
excel_file = "Synthetic_Store.xlsx"
xls = pd.ExcelFile(excel_file)

# Loop through each sheet and save as a MySQL table
for sheet_name in xls.sheet_names:
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    df.to_sql(sheet_name, con=engine, if_exists="replace", index=False)  # replace = overwrite if exists
    print(f"Imported sheet '{sheet_name}' into table '{sheet_name}'")

print("✅ All sheets imported successfully into MySQL!")
