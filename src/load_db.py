import sqlite3
import pandas as pd

# The CSV uses ";" as separator. Codes are read as text to keep leading zeros (e.g. "01").
df = pd.read_csv(
    "data/communes.csv",
    sep=";",
    dtype={"code_insee": str, "code_departement": str},
)

con = sqlite3.connect("data/coverage.db")
df.to_sql("communes", con, if_exists="replace", index=False)

count = con.execute("SELECT COUNT(*) FROM communes").fetchone()[0]
print(f"{count} communes loaded into data/coverage.db")
con.close()
