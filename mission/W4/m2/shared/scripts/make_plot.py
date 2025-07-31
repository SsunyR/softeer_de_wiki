# This script is used to generate plots and analyze taxi trip data.
# It reads data from Parquet files, processes it, and visualizes key metrics.

import pyarrow.parquet as pq
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
SPARK_HOME = "/opt/spark/"
metrics = pq.read_table(SPARK_HOME + "local/data/parquet/metrics/pd_metrics.parquet").to_pandas()
avg_trip_duration = metrics['avg_trip_duration'].iloc[0]
avg_trip_distance = metrics['avg_trip_distance'].iloc[0]
avg_fare = metrics['avg_fare'].iloc[0]
peak_hours_df = pq.read_table(SPARK_HOME + "local/data/parquet/peak_hours/pd_peak_hours.parquet").to_pandas()
weather_analysis = pq.read_table(SPARK_HOME + "local/data/parquet/weather_analysis/pd_weather_analysis.parquet").to_pandas()
distance_analysis = pq.read_table(SPARK_HOME + "local/data/parquet/distance_analysis/pd_distance_analysis.parquet").to_pandas()
location_analysis = pq.read_table(SPARK_HOME + "local/data/parquet/location_analysis/pd_location_analysis.parquet").to_pandas()

# Show metrics with along the plots
plt.figure(figsize=(12, 6))
plt.bar(['Average Trip Duration', 'Average Trip Distance', 'Average Fare'], [avg_trip_duration, avg_trip_distance, avg_fare], color='lightgreen')
plt.title('Average Metrics')
plt.ylabel('Value')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# Peak Hours Analysis
plt.figure(figsize=(12, 6))
plt.bar(peak_hours_df['hour'], peak_hours_df['count'], color='skyblue')
plt.xlabel('Hour of the Day')
plt.ylabel('Number of Trips')
plt.title('Peak Hours Distribution')
plt.xticks(range(0, 24))
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# Weather Analysis
plt.figure(figsize=(12, 6))
sns.barplot(x='temp_category', y='num_users', hue='weather_category', data=weather_analysis, palette='Set2')
plt.title('Weather Category Analysis')
plt.xlabel('Temperature Category')
plt.ylabel('Number of Users')
plt.legend(title='Weather Category')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# Distance Analysis
plt.figure(figsize=(12, 6))
sns.barplot(x='distance_category', y='num_users', data=distance_analysis, palette='Set1')
plt.title('Distance Category Analysis')
plt.xlabel('Distance Category')
plt.ylabel('Number of Users')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# Location Analysis
plt.figure(figsize=(12, 6))
sns.barplot(x='PULocation', y='num_users', data=location_analysis, palette='Set3')
plt.title('Pickup Location Analysis')
plt.xlabel('Pickup Location')
plt.ylabel('Number of Users')
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()