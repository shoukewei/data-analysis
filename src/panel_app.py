import panel as pn
import pandas as pd
import hvplot.pandas

pn.extension()

df = pd.read_parquet("yellow_tripdata_2023-01.parquet",
                     columns=["tpep_pickup_datetime","fare_amount"])
df["hour"] = df["tpep_pickup_datetime"].dt.hour
hourly = df.groupby("hour")["fare_amount"].mean().reset_index()

chart = hourly.hvplot.bar(x="hour", y="fare_amount",
                           title="Mean Fare by Hour",
                           width=700, height=350)

pn.Column("# NYC Taxi Panel Dashboard", chart).servable()