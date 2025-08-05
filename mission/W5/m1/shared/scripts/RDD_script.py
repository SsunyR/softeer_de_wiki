from pyspark.sql import SparkSession
from pyspark import SparkConf, SparkContext

import os
import glob
import sys
import shutil

# Initialize Spark session
spark = SparkSession.builder \
    .appName("RDD_Analysis") \
    .getOrCreate()

sc = spark.sparkContext

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(BASE_DIR, 'data')

FILE_NAME = os.path.join(DATA_PATH, "fhv_tripdata_2024_1278/fhvhv_tripdata_2024-01.parquet")

rdds = []
df = spark.read.parquet(FILE_NAME)
rdd = df.rdd.sample(withReplacement=False, fraction=0.001, seed=42)

reduced_rdd = rdd.map(
    lambda row: dict(
        request_datetime=row.request_datetime,
        trip_miles=row.trip_miles,
        trip_time=row.trip_time,
        base_passenger_fare=row.base_passenger_fare
    )
)
filtered_rdd = reduced_rdd.filter(lambda row: row['request_datetime'].year == 2024 and row['base_passenger_fare'] > 0)

filtered_rdd = filtered_rdd.cache()

total_revenue_count = filtered_rdd.map(
    lambda row: (row['base_passenger_fare'], 1)
).reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]))

total_revenue, total_count = total_revenue_count

average_revenue = total_revenue / total_count
average_revenue = round(average_revenue, 2)

total_distance = filtered_rdd.map(lambda row: row['trip_miles']).reduce(lambda x, y: x + y)

average_distance = total_distance / total_count
average_distance = round(average_distance, 2)

daily_metrics_rdd = filtered_rdd.map(
    lambda row: (
        row['request_datetime'].date(),  # key: 날짜
        (1, row['base_passenger_fare'])  # value: (건수, 수익)
    )
).reduceByKey(
    lambda a, b: (a[0] + b[0], a[1] + b[1])
)

daily_metrics_sorted = daily_metrics_rdd.sortByKey()

summary_rdd = sc.parallelize([
    "total_revenue,total_count,average_distance",
    f"{round(total_revenue_count[0], 2)},{total_revenue_count[1]},{round(average_distance, 2)}"
])

# 저장
summary_rdd.coalesce(1).saveAsTextFile(DATA_PATH + "/output/summary")

daily_csv_rdd = daily_metrics_sorted.map(
    lambda x: f"{x[0]},{x[1][0]},{round(x[1][1], 2)}"
)

# 하나의 파일로 저장하여 순서 보장
daily_csv_rdd.coalesce(1).saveAsTextFile(DATA_PATH + "/output/daily_metrics")

# File rename
file_path = os.path.join(DATA_PATH + "/output/daily_metrics/part-00000")
os.rename(file_path, os.path.join(DATA_PATH + "/output/daily_metrics/daily_metrics.csv"))
file_path = os.path.join(DATA_PATH + "/output/summary/part-00000")
os.rename(file_path, os.path.join(DATA_PATH + "/output/summary/summary.csv"))

# File move
shutil.move(os.path.join(DATA_PATH + "/output/daily_metrics/daily_metrics.csv"), os.path.join(DATA_PATH + "/daily_metrics_final.csv"))
shutil.move(os.path.join(DATA_PATH + "/output/summary/summary.csv"), os.path.join(DATA_PATH + "/summary_final.csv"))

# Remove output directory
shutil.rmtree(os.path.join(DATA_PATH + "/output"), ignore_errors=True)

spark.stop()