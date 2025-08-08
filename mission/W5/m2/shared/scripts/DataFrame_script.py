from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, to_date, dayofweek, when, count, make_date, regexp_replace, round, floor
from pyspark.sql.functions import year, month
import os

# Initialize Spark session
spark = SparkSession.builder \
    .appName("DataFrame_Analysis") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_DATA_PATH = os.path.join(BASE_DIR, 'data')

FILE_NAME_HEADER = os.path.join(INPUT_DATA_PATH, "fhv_tripdata_2024_1278/fhvhv_tripdata_2024-")
month = '01'

path = f"{FILE_NAME_HEADER}{month}.parquet"
df = spark.read.parquet(path)

columns = [
    'request_datetime',
    'trip_miles',
    'trip_time',
    'base_passenger_fare'
]

reduced_df = df.select(*columns)
reduced_df.show(5)

filtered_df = reduced_df.filter((col('base_passenger_fare') > 0))

filtered_df = filtered_df.withColumn('date', to_date(col('request_datetime'), 'yyyy-MM-dd'))
filtered_df = filtered_df.drop('request_datetime')

# Select 2024 datas
filtered_df = filtered_df.filter(year(col('request_datetime')) == 2024)

# 날씨 데이터 로드
weather_path_header = os.path.join(INPUT_DATA_PATH, "2024_weather/")
weather_df = spark.read.option("header", True).csv(weather_path_header + "01.csv")

weather_df = weather_df.withColumn("date", make_date("year", "month", "day"))
weather_df = weather_df.drop("year", "month", "day")

for col_name in ['precipitation1', 'precipitation2', 'precipitation3']:
    weather_df = weather_df.withColumn(
        col_name,
        regexp_replace(col(col_name), 'T', '0')
    )

# 타입 변경
for col_name in ['precipitation1', 'precipitation2', 'precipitation3']:
    weather_df = weather_df.withColumn(
        col_name,
        col(col_name).cast('float')
    )

# precipitation 합산
weather_df = weather_df.withColumn(
    "precipitation",
    round(col("precipitation1") + col("precipitation2") + col("precipitation3"), 2)
)

weather_df = weather_df.drop("precipitation1", "precipitation2", "precipitation3")

weather_df = weather_df \
    .withColumn("max", round((col("max") - 32) * 5 / 9, 1).alias("max")) \
    .withColumn("min", round((col("min") - 32) * 5 / 9, 1).alias("min")) \

df_with_weather = filtered_df.join(weather_df, on="date", how="left")

df_with_day = df_with_weather.withColumn("date", to_date(col("date"))) \
    .withColumn("day_of_week", dayofweek(col("date"))) \
    .withColumn("day_type", when(col("day_of_week").isin(1, 7), "weekend").otherwise("weekday"))

# cache the DataFrame to optimize performance for subsequent operations
df_with_day.cache()

# 평일/주말 기준 집계
result1 = df_with_day.groupBy("day_type").agg(
    count("*").alias("count"),
    avg("trip_miles").alias("avg_trip_miles"),
    avg("base_passenger_fare").alias("avg_base_passenger_fare")
)

result1.show()

df_with_day = df_with_day.withColumn("temp_group", floor(col("max") / 5) * 5)

result2 = df_with_day.groupBy("temp_group").agg(
    count("*").alias("count"),
    round(avg("trip_miles"), 2).alias("avg_trip_miles"),
    round(avg("base_passenger_fare"), 2).alias("avg_base_passenger_fare")
).orderBy("temp_group")

result2.show()

# Stop the Spark session
spark.stop()