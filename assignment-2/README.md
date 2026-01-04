[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DPLnryEt)

# CSC4160 Assignment 2 (8 points)

### Deadline: October 10, 2025, 23:59

### Name: Chua Qin Di

### Student ID: 125400010

---

## DockerCoins

- DockerCoins is made of 5 services
  - `rng` = web service generating random bytes
  - `hasher` = web service computing hash of POSTed data
  - `worker` = background process calling `rng` and `hasher`
  - `webui` = web interface to watch progress
  - `redis` = data store (holds a counter updated by `worker`)

![](https://raw.githubusercontent.com/cuhksz-csc4303-24s/assets/main/dockercoins.png)

In this assignment, you will deploy an application called `DockerCoins` which generates a few random bytes, hashes these bytes, increments a counter (to keep track of speed) and repeats forever! You will try to find its bottlenecks when scaling and use HPA (Horizontal Pod Autoscaler) to scale the application. Please follow these instructions carefully!

## Environment Setup

The assignment needs to be setup in `AWS`. You should choose `Ubuntu Server 24.04 LTS (HVM), SSD Volume Type` as AMI (Amazon Machine Image) and `m4.large` as the instance type. And you need to configure security group as followed, to make sure that you can access the service of minikube on the web browser later.

| Type        | Protocol | Port Range | Source    | Description |
| ----------- | -------- | ---------- | --------- | ----------- |
| All traffic | All      | All        | 0.0.0.0/0 |             |

Run the following commands to satisfy the requirements.

```bash
# Install Minikube
$ curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
$ sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Install kubectl
$ curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
$ sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Docker
$ sudo apt-get update && sudo apt-get install docker.io -y

# Install conntrack
$ sudo apt-get install -y conntrack

# Install httping
$ sudo apt-get install httping

# Install Helm
$ curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3
$ chmod 700 get_helm.sh
$ ./get_helm.sh
```

## Running Minikube on EC2 Ubuntu

Add user to “docker” group and switch primary group

```bash
$ sudo usermod -aG docker $USER && newgrp docker
```

### Start Minikube

```bash
$ minikube start
```

## Start the application

You can transfer the assignment zip file from your local machine to the EC2 instance and `cd` into the assignment directory.

- Start the application from the `dockercoins` yaml

```bash
$ kubectl apply -f dockercoins.yaml
```

- Wait until all the components are running

```bash
$ kubectl get po
# NAME                     READY   STATUS    RESTARTS   AGE
# hasher-89f59d444-r7v7j   1/1     Running   0          27s
# redis-85d47694f4-m8vnt   1/1     Running   0          27s
# rng-778c878fb8-ch7c2     1/1     Running   0          27s
# webui-7dfbbf5985-24z79   1/1     Running   0          27s
# worker-949969887-rkn48   1/1     Running   0          27s
```

- Check the results from UI

```bash
$ minikube service webui
# |-----------|-------|-------------|----------------------------|
# | NAMESPACE | NAME  | TARGET PORT |            URL             |
# |-----------|-------|-------------|----------------------------|
# | default   | webui |          80 | http://172.31.67.128:30163 |
# |-----------|-------|-------------|----------------------------|
# 🎉  Opening service default/webui in default browser...
# 👉  http://172.31.67.128:30163
```

- Port forwarding for WebUI

You need to forward connections to a local port to a port on the pod.

```bash
$ kubectl port-forward --address 0.0.0.0 <webui pod name> <local port>:<pod port>
```

Local port is any number. Pod Port is target port (e.g., 80).

You can access the DockerCoin Miner WebUI on a web browser. The address is &lt;Public IPv4 address&gt;:&lt;local port&gt; (e.g., `3.238.254.199`:`30163`, where `3.238.254.199` is Public IPv4 address of the instance).

_Note_: kubectl port-forward does not return. To continue with the exercises, you will need to open another terminal.

![](https://raw.githubusercontent.com/cuhksz-csc4303-24s/assets/main/webui.png)

## Bottleneck detection

### Workers

Scale the # of workers from 2 to 10 (change the number of `replicas`).

```bash
$ kubectl scale deployment worker --replicas=3
```

| # of workers  | 1   | 2   | 3   | 4   | 5    | 10   |
| ------------- | --- | --- | --- | --- | ---- | ---- |
| hashes/second | 4.0 | 6.0 | 8.0 | 9.0 | 10.0 | 10.0 |

> **Question**: What is the speedup bump when you have 10x workers?
>
> Answer: The speedup bump is 10.0 / 4.0 = 2.5.

### Rng / Hasher

After we scaled to 10 workers, the speed bump is not 10x! Something is slowing us down... But what?

Let's keep the number of workers as `10` and use the good old `httping` command for latency detection. Possible bottlenecks for now are `rng` and `hasher`.

```bash
# Expose the service, since we are detecting the latency outside the k8s cluster
$ kubectl expose service rng --type=NodePort --target-port=80 --name=rng-np
$ kubectl expose service hasher --type=NodePort --target-port=80 --name=hasher-np

# Get the url of the service
$ kubectl get svc rng-np hasher-np

# Find the minikube address
$ kubectl cluster-info
# Kubernetes control plane is running at https://172.31.67.128:8443
# KubeDNS is running at https://172.31.67.128:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
# Here, minikube address is 172.31.67.128

# Detect the latency of hasher
$ httping <minikube-address>:<hasher-np-port>

# Detect the latency of rng
$ httping <minikube-address>:<rng-np-port>
```

| Service      | Hasher | Rng   |
| ------------ | ------ | ----- |
| Latency (ms) | 1.4    | 734.7 |

> **Question**: Which service is the bottleneck?
>
> Answer: The bottleneck here seems to be Rng although in theory, Hasher is designed to be the bottleneck.

## Application monitoring

### Collecting metrics with Prometheus

Prometheus is an open-source tool to monitor and collect metrics from applications, allowing users to see and understand important metrics that let them know how well an application is doing.

We are going to deploy Prometheus on our Kubernetes cluster and see how to query it.

```bash
# Install prometheus
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
$ helm install prometheus prometheus-community/prometheus

# Expose service port
$ kubectl expose service prometheus-server --type=NodePort --target-port=9090 --name=prometheus-server-np
```

Befor proceeding, our metric-server add on is disabled by default. Check it using:

```bash
$ minikube addons list
```

If its disabled, you will see something like metrics-server: disabled Enable it using:

```bash
$ minikube addons enable metrics-server
```

We want to collect latency metric via `httplat`, a minimalist Prometheus exporter that exposes the latency of a single HTTP target. (Please replace `<FILL IN>` in the `httplat` yaml as which you need).

```bash
$ kubectl apply -f httplat.yaml
$ kubectl expose deployment httplat --port=9080

# Check if the deployment is ready
$ kubectl get deploy httplat
# NAME      READY   UP-TO-DATE   AVAILABLE   AGE
# httplat   1/1     1            1           43s
```

Configure Prometheus to gather the detected latency.

```bash
$ kubectl annotate service httplat \
          prometheus.io/scrape=true \
          prometheus.io/port=9080 \
          prometheus.io/path=/metrics
```

#### Connect to Prometheus

```bash
$ kubectl get svc prometheus-server-np
# NAME                   TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
# prometheus-server-np   NodePort   10.96.122.34   <none>        80:24057/TCP   87s
```

_Port forwarding for Prometheus UI_

You need to forward connections to a local port to a port on the pod.

```bash
$ kubectl port-forward --address 0.0.0.0 <prometheus server pod name> <local port>:9090
or
$ kubectl port-forward --address 0.0.0.0 service/prometheus-server-np <local port>:80
```

_Note:_ Why the difference?

To retrieve the Prometheus server pod name, type the following command into your terminal:

```bash
$ kubectl get po
```

The pod name you're looking for begins with `prometheus-server-`, such as `prometheus-server-8444b5b7f7-hk6g7`.

_Access Prometheus_

You can access the Prometheus on a web browser. The address is &lt;Public IPv4 address&gt;:&lt;local port&gt;. Check if `httplab` metrics are available. You can try to graph the following PromQL expression that detects the latency of rng/hasher (as you specified in `httplat.yaml`).

```sql
rate(httplat_latency_seconds_sum[2m])/rate(httplat_latency_seconds_count[2m])
```

## HPA

To solve the bottleneck of the application, you can specify a horizontal pod autoscaler which can scale the number of Pods based on some metrics.

### Generating a load test

This is how you generate a load test. You do not need to generate one until further instruction in the next section.

Create a Load Test Job as,

```bash
file: loadtest-job.yaml
```

```bash
apiVersion: batch/v1
kind: Job
metadata:
  generateName: loadtest
spec:
  template:
    spec:
      containers:
      - name: siege
        image: schoolofdevops/loadtest:v1
        command: ["siege",  "--concurrent=15", "--benchmark", "--time=4m", "http://<FILL IN>"] # FILL IN: rng or hasher
      restartPolicy: Never
  backoffLimit: 4
```

and launch it as

```bash
kubectl create -f loadtest-job.yaml
```

This will launch a one off Job which would run for 4 minutes.

To get information about the job

```bash
kubectl get jobs
kubectl describe  job loadtest-xxx
```

replace loadtest-xxx with actual job name.

To check the load test output

```bash
kubectl logs  -f loadtest-xxxx
```

[replace loadtest-xxxx with the actual pod id.]

[Sample Output]

```bash
** SIEGE 3.0.8
** Preparing 15 concurrent users for battle.
The server is now under siege...
Lifting the server siege...      done.

Transactions:                  47246 hits
Availability:                 100.00 %
Elapsed time:                 239.82 secs
Data transferred:               1.62 MB
Response time:                  0.08 secs
Transaction rate:             197.01 trans/sec
Throughput:                     0.01 MB/sec
Concurrency:                   14.94
Successful transactions:       47246
Failed transactions:               0
Longest transaction:            0.61
Shortest transaction:           0.00

FILE: /var/log/siege.log
You can disable this annoying message by editing
the .siegerc file in your home directory; change
the directive 'show-logfile' to false.
```

### Create the autoscaling policy.

Please replace `<FILL IN>` in the `hpa` yaml as which you need. Now we are ready to see our HPA in action.

1. Keep monitoring the latency of the rng/hasher (bottleneck component) in Prometheus UI.
2. Generate load test before we apply our HPA.
3. Apply HPA (before our load test job completes):

Type the following command into your terminal:

```bash
$ kubectl apply -f hpa.yaml
```

The horizontal pod autoscaler in `hpa.yaml` is designed to automatically adjust the number of replicas for a particular deployment (that you need to `<FILL IN>`, either rng or hasher) based on a sample autoscaling policy.

Let's see the details of our hpa. If you still see `<unknown> / 5%`, try to wait for a while.

```bash
$ kubectl describe hpa <FILL IN> # FILL IN: rng or hasher
```

4. Continuously watch our HPA (for rng or hasher) to see real-time updates of our HPA in action.

```bash
$ kubectl get hpa <FILL IN> -w # FILL IN: rng or hasher
```

[Sample Output]

```bash
NAME   REFERENCE        TARGETS      MINPODS   MAXPODS   REPLICAS   AGE
rng    Deployment/rng   cpu: 7%/5%   1         10        6          12m
...
```

> **Screenshot**:
>
> - The Prometheus UI that queries the latency of rng/hasher.
> - The the terminal when we watched HPA in action as it scales out/in the rng/hasher with the increasing/decreasing load.

![Hasher Prometheus UI](https://github.com/cloud-computing-cuhksz/assignment-2-chuaqindi/blob/master/images/hasher%20prometheus%20ui.png?raw=true)

![Describe Hasher HPA](https://github.com/cloud-computing-cuhksz/assignment-2-chuaqindi/blob/master/images/describe%20hasher%20hpa.png?raw=true)

## Pod Resource Usage Analysis

In the previous steps, we found the application's performance bottleneck by measuring latency. However, high latency does not always equate to high CPU or memory consumption. What does the resource usage look like for a well-designed system that makes full use of its resources?

In this bonus task, you will use the `kubectl top pods` command to monitor the actual CPU and memory usage of the various components in the `dockercoins` application under load.

**Background**:

The `kubectl top pods` command can display the resource consumption of running pods in real time. The CPU is reported in "millicores" (`m`), where `1000m` is equivalent to one full CPU core. Memory is reported in "mebibytes" (`Mi`). **Note**: This command depends on `metrics-server`, which you have already enabled in the previous steps, so you can use it directly.

**Steps**:

1.  **Observe Baseline Resource Usage**

    First, check the resource usage of each pod without any additional load to establish a baseline.

    ```bash
    $ kubectl top pods
    # NAME                      CPU(cores)   MEMORY(bytes)
    # hasher-xxxxxxxxxx-xxxxx   1m           8Mi
    # redis-xxxxxxxxxx-xxxxx    1m           3Mi
    # rng-xxxxxxxxxx-xxxxx      51m          14Mi
    # webui-xxxxxxxxxx-xxxxx    1m           15Mi
    # worker-xxxxxxxxxx-xxxxx   2m           11Mi
    ```

    _(Note: The values you see may differ.)_

2.  **Apply Load and Observe**

    As in the "Bottleneck detection" section, we will increase the number of `worker`s to 10 to put pressure on the system.

    ```bash
    $ kubectl scale deployment worker --replicas=10
    ```

    After the new `worker` pods have started and are running (you can confirm with `kubectl get po`), use the `watch` utility to continuously monitor resource usage. This will refresh the output every 5 seconds, making it easy to see changes under load.

    Run the following command and observe the values for a few minutes, paying close attention to the `rng` and `hasher` pods:

    ```bash
    $ watch -n 5 kubectl top pods
    ```

    ![Watch kubectl top pods](https://github.com/cloud-computing-cuhksz/assignment-2-chuaqindi/blob/master/images/watch%20-n%205%20kubectl%20top%20pods.png?raw=true)

**Question to answer**:

> **Question**:
>
> 1.  Under the load of 10 `worker`s, which service (`rng` or `hasher`) consistently consumes the most **CPU**?
> 2.  Is this service with the highest CPU consumption the same as the service you previously identified with the highest **latency** using `httping`?
> 3.  Based on your observations, does the high latency seem to be caused by the service being CPU-bound (i.e., busy with computation)? Briefly explain your reasoning.
> 4.  Do you think scaling the rng/hasher based on CPU utilization makes sense? If not, what alternative metric could we use instead? Please explain your reasoning.

**Answer**: <Your answer goes here>
<br>

1. Hasher consistently consumes the most CPU. The total CPU consumption of all Hasher replica is greater than the total CPU consumption of Rng.

2. No. Rng had a much higher latency than Hasher.

3. The high latency is not caused by the service being CPU-bound. Rng has high latency due to Python/Flask request-handling and network overhead.

4. For Hasher, CPU utilization makes sense as its workload is compute-heavy. But for Rng, more suitable metrics would be latency and request rate since the bottleneck is in handling HTTP requests.

## Grading

In this assignment, you are required to finish the following things:

- Report the performance of DockerCoins with different number of workers (2 marks).
- Detect latency and find the bottleneck component (rng or hasher) (2 marks).
- Upload the screenshot of the HPA in action (2 marks):
  - Prometheus UI
  - Terminal
- Analyze pod resource usages (2 marks).
