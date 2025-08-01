import pyarrow.parquet as pq
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
# import seaborn as sns

# Check for test mode
is_test_mode = '--test' in sys.argv

# 스크립트의 위치를 기준으로 데이터 디렉토리 경로를 동적으로 설정
# /.../local/scripts/ -> /.../local/
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(BASE_DIR, 'test_data') if is_test_mode else os.path.join(BASE_DIR, 'data')

# Load the data
metrics = pq.read_table(os.path.join(DATA_PATH, "parquet/metrics/pd_metrics.parquet")).to_pandas()
avg_trip_duration = metrics['avg_trip_duration'].iloc[0]
avg_trip_distance = metrics['avg_trip_distance'].iloc[0]
avg_fare = metrics['avg_fare'].iloc[0]
peak_hours_df = pq.read_table(os.path.join(DATA_PATH, "parquet/peak_hours/pd_peak_hours.parquet")).to_pandas()
weather_analysis = pq.read_table(os.path.join(DATA_PATH, "parquet/weather_analysis/pd_weather_analysis.parquet")).to_pandas()
distance_analysis = pq.read_table(os.path.join(DATA_PATH, "parquet/distance_analysis/pd_distance_analysis.parquet")).to_pandas()
location_analysis = pq.read_table(os.path.join(DATA_PATH, "parquet/location_analysis/pd_location_analysis.parquet")).to_pandas()

# To csv
csv_output_path = os.path.join(DATA_PATH, "csv")
os.makedirs(csv_output_path, exist_ok=True)

metrics.to_csv(os.path.join(csv_output_path, "metrics.csv"), index=False)
peak_hours_df.to_csv(os.path.join(csv_output_path, "peak_hours.csv"), index=False)
weather_analysis.to_csv(os.path.join(csv_output_path, "weather_analysis.csv"), index=False)
distance_analysis.to_csv(os.path.join(csv_output_path, "distance_analysis.csv"), index=False)
location_analysis.to_csv(os.path.join(csv_output_path, "location_analysis.csv"), index=False)