import sys
from pyspark import SparkContext, SparkConf 

# ----- Spark setup -----
conf = SparkConf().setAppName("pagerank_part1")
spark = SparkContext(conf=conf)

input_path = sys.argv[1]
output_path = sys.argv[2]

# ----- Read data -----
lines = spark.textFile(input_path)

# Load edges: (from, [to1, to2, ...]) and cache
edges_rdd = (
    lines.filter(lambda line: not line.startswith("#"))
         .map(lambda line: line.split('\t'))
         .map(lambda tokens: (tokens[0], tokens[1]))
         .groupByKey()
         .mapValues(list)
         .cache()
)

# Initial rank for each page
ranks_rdd = edges_rdd.map(lambda x: (x[0], 1.0))

# ----- PageRank iterations -----
for i in range(10):
    contributions_rdd = edges_rdd.join(ranks_rdd).flatMap(
        lambda x: [
            (to, x[1][1] / len(x[1][0]))
            for to in x[1][0]
        ]
    )
    ranks_rdd = (
        contributions_rdd
        .reduceByKey(lambda x, y: x + y)
        .map(lambda x: (x[0], 0.15 + 0.85 * x[1]))
    )

# ----- Save output & stop Spark -----
ranks_rdd.saveAsTextFile(output_path)
spark.stop()
