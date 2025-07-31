from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, mean, round, unix_timestamp, expr, regexp_replace, when
from pyspark.sql.functions import year, month, dayofmonth, hour
import os
import glob

# Initialize Spark session
spark = SparkSession.builder \
    .appName("NYC TLC Analysis") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

SPARK_HOME = "/opt/spark/"

FILE_NAME_HEADER = SPARK_HOME + "local/data/fhv_tripdata_2024_1278/fhvhv_tripdata_2024-"
months = ['01', '01', '07', '08']
df = None

for m in months:
    file_path = f"{FILE_NAME_HEADER}{m}.parquet"
    new_df = spark.read.parquet(file_path)

    if df is None:
        df = new_df
    else:
        df = df.union(new_df)

del new_df

# 불필요한 열 제거

columns_to_drop = [
    'dispatching_base_num', 'originating_base_num', 'shared_request_flag',
    'shared_match_flag', 'access_a_ride_flag', 'wav_request_flag', 'wav_match_flag'
]
df_clean = df.drop(*columns_to_drop)

# Average trip duration, distance, and fare
avg_trip_duration = df_clean.agg(mean("trip_time").alias("avg_trip_time")).collect()[0]["avg_trip_time"]
avg_trip_distance = df_clean.agg(mean("trip_miles").alias("avg_trip_distance")).collect()[0]["avg_trip_distance"]
avg_fare = df_clean.agg(mean("base_passenger_fare").alias("avg_base_passenger_fare")).collect()[0]["avg_base_passenger_fare"]

# save metrics as Parquet
metrics_df = spark.createDataFrame([
    (avg_trip_duration, avg_trip_distance, avg_fare)
], ["avg_trip_duration", "avg_trip_distance", "avg_fare"])
metrics_df.coalesce(1) \
    .write \
    .format("parquet") \
    .mode("overwrite") \
    .save(SPARK_HOME + "local/data/parquet/metrics")

# File rename
file_path = glob.glob(SPARK_HOME + "local/data/parquet/metrics/part-00000-*.parquet")[0]
os.rename(file_path, SPARK_HOME + "local/data/parquet/metrics/pd_metrics.parquet")


# 시간 조건 필터링
df_clean = df_clean \
    .withColumn("pickup_ts", unix_timestamp("pickup_datetime")) \
    .withColumn("dropoff_ts", unix_timestamp("dropoff_datetime")) \
    .withColumn("scene_ts", unix_timestamp("on_scene_datetime")) \
    .withColumn("request_ts", unix_timestamp("request_datetime"))

df_clean = df_clean.filter((col("dropoff_ts") > col("pickup_ts")) &
                           (col("scene_ts") > col("request_ts")) &
                           (col("base_passenger_fare") > 0) &
                           (col("driver_pay") >= 0))

# scene_time 계산
df_clean = df_clean.withColumn("scene_time", expr("scene_ts - request_ts"))

# ts 열 제거
df_clean = df_clean.drop("pickup_ts", "dropoff_ts", "scene_ts", "request_ts")

# 분단위 시간 변환
# 반올림
df_clean = df_clean.withColumn("scene_time", round(expr("scene_time / 60")))
df_clean = df_clean.withColumn("trip_time", round(expr("trip_time / 60")))

# 날짜 정보 추출
df_with_date = df_clean \
    .withColumn("request_datetime", col("request_datetime").cast("timestamp")) \
    .withColumn("year", year("request_datetime")) \
    .withColumn("month", month("request_datetime")) \
    .withColumn("day", dayofmonth("request_datetime")) \
    .withColumn("hour", hour("request_datetime"))

# 계절 정보 추가
df_with_date = df_with_date.withColumn(
    "season",
    expr("""
        CASE
            WHEN month = 1 OR month = 2 THEN 'Winter'
            WHEN month = 7 OR month = 8 THEN 'Summer'
        END
    """)
)

# 계절이 NULL인 행 제거
df_with_date = df_with_date.filter(col("season").isNotNull())

# 택시 라이센스 타입 추가
df_with_date = df_with_date.withColumn(
    "service_type",
    expr("""
        CASE
            WHEN hvfhs_license_num='HV0003' THEN 'Uber'
            WHEN hvfhs_license_num='HV0004' THEN 'Lyft'
        END
    """)
)

del df_clean

taxi_zone = spark.read.option("header", True).csv(
    SPARK_HOME + "local/data/taxi_zone_lookup.csv"
)

# 1. PULocationID에 대한 join
# df_with_date와 taxi_zone에 각각 별칭(alias)을 부여합니다.
pu_zones = taxi_zone.alias("pu_zones")

df_with_pu = df_with_date.join(
    pu_zones,
    df_with_date.PULocationID == col("pu_zones.LocationID"),
    how="left"
).select(
    df_with_date["*"],
    col("pu_zones.Borough").alias("PULocation") # 별칭을 사용해 명확히 지정
)

# 2. DOLocationID에 대한 join
# taxi_zone에 다시 새로운 별칭을 부여합니다.
do_zones = taxi_zone.alias("do_zones")

df_with_do = df_with_pu.join(
    do_zones,
    df_with_pu.DOLocationID == col("do_zones.LocationID"),
    how="left"
).select(
    df_with_pu["*"],
    col("do_zones.Borough").alias("DOLocation") # 별칭을 사용해 명확히 지정
)

# Pickup과 Dropoff 지역 "N/A"인 행 제거
df_with_do = df_with_do.filter(
    (col("PULocation") != "N/A") & (col("DOLocation") != "N/A")
)

# drop locationid
df_zone = df_with_do.drop("PULocationID", "DOLocationID", "LocationID")

del df_with_date, df_with_pu, df_with_do

# 날씨 데이터 로드
weather_path_header = SPARK_HOME + "local/data/2024_weather/"
weather_df = spark.read.option("header", True).csv(weather_path_header + "*.csv")


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

df_final = df_zone.join(
    weather_df,
    on=["year", "month", "day"],
    how="left"
)

del df_zone, weather_df

# Peak Hours Analysis
peak_hours = df_final.groupBy("hour").count().orderBy(col("count").desc())

# Save as Parquet
peak_hours.coalesce(1) \
  .write \
  .format("parquet") \
  .mode("overwrite") \
  .save(SPARK_HOME + "local/data/parquet/peak_hours")

import os
import glob
file_path = glob.glob(SPARK_HOME + "local/data/parquet/peak_hours/part-00000-*.parquet")[0]
os.rename(file_path, SPARK_HOME + "local/data/parquet/peak_hours/pd_peak_hours.parquet")

# 
# 온도 카테고리
df_final = df_final.withColumn(
    "temp_category",
    when(col("max").isNull(), "Unknown")
    .when(col("max") <= 0, "Below Freezing")
    .when((col("max") > 0) & (col("max") <= 10), "0-10°C")
    .when((col("max") > 10) & (col("max") <= 20), "10-20°C")
    .when((col("max") > 20) & (col("max") <= 30), "20-30°C")
    .when(col("max") > 30, "Above 30°C")
    .otherwise("Unknown")
)

# 강수량 카테고리
df_final = df_final.withColumn(
    "weather_category",
    when(col("precipitation").isNull(), "Unknown")
    .when(col("precipitation") <= 0.1, "No Precipitation")
    .when((col("precipitation") > 0.1) & (col("precipitation") <= 0.5), "Light Precipitation")
    .when((col("precipitation") > 0.5) & (col("precipitation") <= 1.0), "Moderate Precipitation")
    .when(col("precipitation") > 1.0, "Heavy Precipitation")
    .otherwise("Unknown")
)

df_final = df_final.filter(col("weather_category") != "Unknown")

# Save as Parquet
df_final.coalesce(1) \
  .write \
  .format("parquet") \
  .mode("overwrite") \
  .save(SPARK_HOME + "local/data/parquet/pd_final_data")

# File rename
file_path = glob.glob(SPARK_HOME + "local/data/parquet/pd_final_data/part-00000-*.parquet")[0]
os.rename(file_path, SPARK_HOME + "local/data/parquet/pd_final_data/pd_final_data.parquet")

# 날씨 카테고리별 택시 이용자 수, 요금, 이동 시간 분석
weather_analysis = df_final.groupBy("temp_category", "weather_category").agg(
    count("service_type").alias("num_users"),
    round(mean("base_passenger_fare"), 2).alias("avg_fare"),
    round(mean("trip_time"), 2).alias("avg_trip_time")
).orderBy(col("num_users").desc())

# Save as Parquet
weather_analysis.coalesce(1) \
  .write \
  .format("parquet") \
  .mode("overwrite") \
  .save(SPARK_HOME + "local/data/parquet/weather_analysis")
# File rename
file_path = glob.glob(SPARK_HOME + "local/data/parquet/weather_analysis/part-00000-*.parquet")[0]
os.rename(file_path, SPARK_HOME + "local/data/parquet/weather_analysis/pd_weather_analysis.parquet")

# 이동 거리 구간별 분석
distance_bins = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, float("inf")]
distance_labels = [
    "0-1 miles", "1-2 miles", "2-3 miles",
    "3-4 miles", "4-5 miles", "5-10 miles",
    "10-15 miles", "15-20 miles", "20-25 miles",
    "25-30 miles", "30+ miles"
]
distance_category = when(
    col("trip_miles").isNull(), "Unknown"
).when(
    col("trip_miles") < 1, "0-1 miles"
).when(
    (col("trip_miles") >= 1) & (col("trip_miles") < 2), "1-2 miles"
).when(
    (col("trip_miles") >= 2) & (col("trip_miles") < 3), "2-3 miles"
).when(
    (col("trip_miles") >= 3) & (col("trip_miles") < 4), "3-4 miles"
).when(
    (col("trip_miles") >= 4) & (col("trip_miles") < 5), "4-5 miles"
).when(
    (col("trip_miles") >= 5) & (col("trip_miles") < 10), "5-10 miles"
).when(
    (col("trip_miles") >= 10) & (col("trip_miles") < 15), "10-15 miles"
).when(
    (col("trip_miles") >= 15) & (col("trip_miles") < 20), "15-20 miles"
).when(
    (col("trip_miles") >= 20) & (col("trip_miles") < 25), "20-25 miles"
).when(
    (col("trip_miles") >= 25) & (col("trip_miles") < 30), "25-30 miles"
).otherwise("30+ miles")

df_final = df_final.withColumn(
    "distance_category",
    distance_category
)

# 거리 카테고리별 택시 이용자 수, 평균 trip_time, scene_time, base_passenger_fare, tips
distance_analysis = df_final.groupBy("distance_category").agg(
    count("service_type").alias("num_users"),
    round(mean("trip_time")).alias("avg_trip_time(minutes)"),
    round(mean("scene_time")).alias("avg_scene_time(minutes)"),
    round(mean("base_passenger_fare")).alias("avg_base_passenger_fare"),
    round(mean("tips")).alias("avg_tips")
)

# Save as Parquet
distance_analysis.coalesce(1) \
  .write \
  .format("parquet") \
  .mode("overwrite") \
  .save(SPARK_HOME + "local/data/parquet/distance_analysis")
# File rename
file_path = glob.glob(SPARK_HOME + "local/data/parquet/distance_analysis/part-00000-*.parquet")[0]
os.rename(file_path, SPARK_HOME + "local/data/parquet/distance_analysis/pd_distance_analysis.parquet")

# 탑승 지역과 하차 지역별 택시 이용자 수, 요금, 이동 시간 분석
location_analysis = df_final.groupBy("PULocation", "DOLocation").agg(
    count("service_type").alias("num_users"),
    round(mean("base_passenger_fare"), 2).alias("avg_fare"),
    round(mean("trip_time"), 2).alias("avg_trip_time"),
    round(mean("scene_time"), 2).alias("avg_scene_time")
).orderBy("num_users", ascending=False)

# Save as Parquet
location_analysis.coalesce(1) \
  .write \
  .format("parquet") \
  .mode("overwrite") \
  .save(SPARK_HOME + "local/data/parquet/location_analysis")
# File rename
file_path = glob.glob(SPARK_HOME + "local/data/parquet/location_analysis/part-00000-*.parquet")[0]
os.rename(file_path, SPARK_HOME + "local/data/parquet/location_analysis/pd_location_analysis.parquet")


# Stop the Spark session
spark.stop()