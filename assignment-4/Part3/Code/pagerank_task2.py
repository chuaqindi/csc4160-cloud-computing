import sys
from pyspark import SparkContext, SparkConf 

conf = SparkConf().setAppName("pagerank_part2")
spark = SparkContext(conf=conf)

input_path = sys.argv[1]
output_path = sys.argv[2]

num_partitions = 10

# read data
lines = spark.textFile(input_path)

# loading edge: (src, [dst1, dst2, ...]) with fixed number of partitions
edges_rdd = (
    lines.filter(lambda line: not line.startswith("#"))
         .map(lambda line: line.split('\t'))
         .map(lambda tokens: (tokens[0], tokens[1]))
         .groupByKey(num_partitions)   # partition here
         .cache()
)

# initial ranks, aligned with the same partitioning
ranks_rdd = edges_rdd.map(lambda x: (x[0], 1.0))

for i in range(10):
    # edges_rdd: (src, neighbors)
    # ranks_rdd: (src, rank)
    contributions_rdd = edges_rdd.join(ranks_rdd).flatMap(
        lambda x: [
            (to, x[1][1] / len(x[1][0]))
            for to in x[1][0]
        ]
    )

    ranks_rdd = (
        contributions_rdd
        .reduceByKey(lambda x, y: x + y, num_partitions)  # keep same partitioning
        .map(lambda x: (x[0], 0.15 + 0.85 * x[1]))
    )

ranks_rdd.saveAsTextFile(output_path)
spark.stop()
