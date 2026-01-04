from pyspark.sql import SparkSession
import sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: part2_temperature_avg.py <input_path> <output_path>")
        sys.exit(-1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    # Start Spark session
    spark = SparkSession.builder.appName("TemperatureAverage").getOrCreate()

    # Read CSV from HDFS (each line: city,temperature)
    df = spark.read.option("header", "false").option("inferSchema", "true").csv(input_path)

    # Rename the default columns for clarity
    df = df.withColumnRenamed("_c0", "city").withColumnRenamed("_c1", "temperature")

    # Compute average temperature for each city
    result = df.groupBy("city").avg("temperature").orderBy("city")

    # Save the result to HDFS as plain text (CSV)
    result.write.mode("overwrite").csv(output_path)

    spark.stop()

