from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("PySparkBasicExample") \
    .getOrCreate()

data = [("Alice", 1, "New York"),
        ("Bob", 2, "London"),
        ("Charlie", 3, "Paris"),
        ("David", 1, "New York")]
columns = ["Name", "ID", "City"]

df = spark.createDataFrame(data, schema=columns)

print("DataFrame Schema:")
df.printSchema()

print("\nOriginal DataFrame:")
df.show()

filtered_df = df.filter(df["City"] == "New York")

print("\nFiltered DataFrame (City = 'New York'):")
filtered_df.show()

filtered_df.repartition(1) \
  .write \
  .format("csv") \
  .option("header", "true") \
  .mode("overwrite") \
  .save("/opt/spark/local/csv")

spark.stop()