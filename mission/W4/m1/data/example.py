from pyspark.sql import SparkSession

# 1. Initialize a SparkSession
# The SparkSession is the entry point to Spark functionality.
spark = SparkSession.builder \
    .appName("PySparkBasicExample") \
    .master("local[*]") \
    .getOrCreate()

# 2. Create a PySpark DataFrame from a list of data
data = [("Alice", 1, "New York"),
        ("Bob", 2, "London"),
        ("Charlie", 3, "Paris"),
        ("David", 1, "New York")]
columns = ["Name", "ID", "City"]

df = spark.createDataFrame(data, schema=columns)

# 3. Show the DataFrame schema and content
print("DataFrame Schema:")
df.printSchema()

print("\nOriginal DataFrame:")
df.show()

# 4. Perform a simple transformation: filter rows where City is "New York"
filtered_df = df.filter(df["City"] == "New York")

# 5. Show the transformed DataFrame
print("\nFiltered DataFrame (City = 'New York'):")
filtered_df.show()

df.write.format("csv")

# 6. Stop the SparkSession
spark.stop()