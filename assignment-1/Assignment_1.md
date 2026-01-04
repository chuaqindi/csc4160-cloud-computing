# CSC4160 Assignment-1: EC2 Measurement (2 questions)

### Deadline: 23:59, Sep 22, Sunday

---

### Name:

### Student Id:

---

## Question 1: Measure the EC2 CPU and Memory performance

1. (1 mark) Report the name of measurement tool used in your measurements (you are free to choose any open source measurement software as long as it can measure CPU and memory performance). Please describe your configuration of the measurement tool, and explain why you set such a value for each parameter. Explain what the values obtained from measurement results represent (e.g., the value of your measurement result can be the execution time for a scientific computing task, a score given by the measurement tools or something else).

   > **Name**: Sysbench is the measurement tool used.
   >
   > **Configuration** :  
   > For **CPU benchmarking**,
   > `sysbench --test=cpu --num-threads=4 --cpu-max-prime=10000 run` is used.
   >
   > For **memory benchmarking**, `sysbench --test=memory --num-threads=4 --memory-total-size=10G --memory-oper=write --memory-scope=global run` is used.
   >
   > `--test` parameter is to set the test mode. Eg. cpu, memory, fileio, oltp
   >
   > `--num-threads` parameter creates the specified number of threads and mutexes for the test. 4 threads is chosen as it is a common configuration used to fully utilize the CPU cores and used for standardized comparison with other EC2 instances.
   >
   > In the **CPU** test,  
   > `cpu-max-prime=10000` is chosen as smaller ranges like 1000 finish too fast to provide meaningful comparisons and large ranges like 100,000 are too time-consuming for a simple CPU benchmark. Thus, 10,000 is a reasonable number that can provide meaningful comparisons between various EC2 instances.
   >
   > In the **memory** test,
   > `--memory-total-size=10G` sets the total size of data to transfer as 10 GB. This number is chosen for standardized and meaningful comparison with other EC2 instances as the test will not finish too quickly or take too long to complete.
   >
   > `--memory-oper=write` sets the memory operation as write because write-operations, as compared to read-operations, allow us to measure the worst case performance of the memory, providing meaningful comparisons with other EC2 instances.
   >
   > `--memory-scope=global run` specifies that each thread will use a globally allocated memory block which reflects real-world scenarios like databases, so the results produced will be more meaningful and realistic for comparison.

   <br>

   > Results:
   > In **CPU** test,  
   > CPU speed: events per second: 1696.22 represents the number of calculations of prime numbers completed per second across all threads. A higher number represents better performance and this number can be used as the <u>main benchmarking score</u>.
   >
   > In **memory** test,  
   > Total operations: 10,485,760 (4,718,501.68 per second) is the number of write operations completed total and per second.
   >
   > **Transferred**: 10,240 MiB (4607.91 MiB/sec) indicates memory throughput.  
   > A higher number (MiB/sec) represents better performance and this number can be used as the <u>main benchmarking score</u>.
   >
   > In both tests,
   > **Latency**:
   > **Min latency** is the time taken for the fastest calculation of a prime number or write operation respectively.  
   > **Avg latency** is the average time taken for one calculation/operation.  
   > **Max latency** is the time taken for the slowest calculation/operation.  
   > **Sum**is the time taken for all calculations/operations to be completed.  
   > **Thread fairness:**  
   > **Avg events** is the average number of calculations processed by each thread with a standard deviation.  
   > A small standard deviation represents that workload is distributed evenly.  
   > **Avg execution** time shows the average total time that the threads ran for. Standard deviation = 0 shows that all threads are utilized evenly.

2. (1 mark) Run your measurement tool on general purpose `t3.medium`, `m5.large`, and `c5d.large` Linux instances, respectively, and find the performance differences among them. Launch all instances in the **US East (N. Virginia)** region. What about the differences among these instances in terms of CPU and memory performance? Please try explaining the differences.

   In order to answer this question, you need to complete the following table by filling out blanks with the measurement results corresponding to each instance type.

   | Size        | CPU performance (events per second) | Memory performance (MiB/sec) |
   | ----------- | ----------------------------------- | ---------------------------- |
   | `t3.medium` | 1654.74                             | 5682.70                      |
   | `m5.large`  | 1641.21                             | 6890.52                      |
   | `c5d.large` | 1801.50                             | 7544.41                      |

   > Region: US East (N. Virginia).
   >
   > In terms of **CPU** performance, `t3.medium` and `m5.large` are relatively similar in performance while `c5d.large` has better CPU performance. This is because `c5d.large` is designed for high performance per core, with higher base clock speed while `m5.large` and `t3.medium` is designed for general purposes.
   >
   > In terms of **memory** performance, `c5d.large` is better than `m5.large` and `t3.medium` is significantly worse than `c5d.large` and `m5.large`. `m5.large` has 8 GiB memory compared to `t3.medium`’s 4 GiB memory. `c5d.large` also has 4 GiB memory but it has higher base memory clock speed.

## Question 2: Measure the EC2 Network performance

1. (1 mark) The metrics of network performance include **TCP bandwidth** and **round-trip time (RTT)**. Within the same region, what network performance is experienced between instances of the same type and different types? In order to answer this question, you need to complete the following table.

   | Type                    | TCP b/w (Mbps) | RTT (ms) |
   | ----------------------- | -------------- | -------- |
   | `t3.medium`-`t3.medium` | 4220           | 0.270    |
   | `m5.large`-`m5.large`   | 9230           | 0.101    |
   | `c5n.large`-`c5n.large` | 9040           | 0.105    |
   | `t3.medium`-`c5n.large` | 2210           | 0.541    |
   | `m5.large`-`c5n.large`  | 2660           | 0.624    |
   | `m5.large`-`t3.medium`  | 1810           | 0.953    |

   > Region: US East (N. Virginia)
   >
   > Between two instances of the same type, the network performance depends on the specifications of the instance family.
   >
   > Between two instances of different instance families, the network performance is bottlenecked by the instance with lower specifications.  
   > There may also be other overhead that decreases performance.

2. (1 mark) What about the network performance for instances deployed in different regions? In order to answer this question, you need to complete the following table.

   | Connection              | TCP b/w (Mbps) | RTT (ms) |
   | ----------------------- | -------------- | -------- |
   | N. Virginia-Oregon      | 32.4           | 64.6     |
   | N. Virginia-N. Virginia | 4960           | 0.156    |
   | Oregon-Oregon           | 4970           | 0.152    |

   > All instances are `c5.large`.  
   > For two instances in the same region, the network performance is good.
   >
   > However, for two instances in different regions, the network performance drops significantly. Cross-region communication depends on the public internet, which has high latency and bandwidth limits.
