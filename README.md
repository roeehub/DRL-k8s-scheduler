# A Reinforcement Learning-based Scheduler for Kubernetes
## Quick Background 

Kubernetes is a leading open source framework for container orchestration - the process of automating deployment and managing applications in a containerized and clustered environment. At its basic level, Kubernetes runs and coordinates container-based applications across a cluster of machines. It is designed to completely manage the life cycle of containerized applications and services using methods that provide predictability, scalability, and high availability. \
A Kubernetes user provides the applications to be deployed in the form of pods - basic units of execution containing one or more tightly-coupled containers. These pods are then assigned to nodes, that represent actual computing resources such as physical or virtual servers. A collection of nodes forms a Kubernetes cluster, managed by the control plane. \
All nodes are heterogeneous by definition, that is, they may encapsulate resources of different capacities. Each node can contain and concurrently execute multiple pods. \
The following figure provides a simplified view of the architecture of Kubernetes.

![alt text for screen readers](docs/images/k8s.jpeg)

Scheduling pods to nodes - that is, assigning each pod to a node on which it will be deployed - is a highly crucial, yet extremely difficult task. A suboptimal pod placement strategy could result in severe underutilization of cluster resources and unsatisfactory application performance. However, finding an optimal placement is a well-known NP-hard combinatorial problem (similar to bin packing) that cannot be solved under practical time and resource constraints. Therefore, the currently available implementation of Kubernetes scheduler, a component responsible for this task, resorts to simple heuristics that often provide results of poor quality.

## Final Project Goal

The goal of this project is to design and implement an alternative scheduler for Kubernetes, utilizing recent advances in deep reinforcement learning to combine low running time with high quality of the produced placements. This RL-based scheduler will repeatedly attempt different pod placements in the cluster and learn the most potent scheduling decisions based on the resulting application performance and resource utilization. The scheduler will be fully compatible with any application currently relying on the default Kubernetes scheduler in terms of API and the supported parameters and constraints.

## Current progress
For developing purposes, we built a k8s simulator in the file cluster_sim.py. There we define three objects: Cluster, Node, and Pod. running a cluster in the simulation creates pods at a controlled pace, and assigns them to Nodes via some given scheduling function. This simulation allows us to train our model in a controlled and transparent environment. 
Note that a very similar file called test_sim.py exists. Its purpose is to run the simulation for testing, without integration with the learning regiment.
For a start, we decided to work with a simple instance of the problem, having only 3 nodes in the cluster. 
Furthermore, as a convention, any scheduling decision is based on the current cluster information (Nodes free memory and pending pods memory demand) and the action is for the first pod in the list. This means that for N nodes and 3 pods, 3 separate scheduling decisions need to be made. Since a lot of pods can be pending at a given moment, the information the simulation provides is only for a fixed pod lookahead, and for simplicity, we only used one pod lookahead in our work.
Regarding the learning process, the notebook kubernetes.ipynb contains the parts needed for a basic RL learning loop. The important parts are as follows:
#### Environment:
The environment is connected to the cluster simulation, it provides the reward system and all the functions needed to interact with the simulation.
#### The Q-Table:
The agent learns using a condensed version of a q-table. This is a simple value-based learning approach for a start and can be improved in the future. 
Since the cluster reports memory usage as a real number (like 37.6% free memory left on node 2), The number of different states is huge and theoretically infinite. This can be solved with neural nets (Checkout next steps) but we went with the approach of cutting the spectrum into fixed-size bins. This transforms the continuous problem into a discrete problem and allows us to assign an entry for similar states. A regular Q-table becomes very large as the number of nodes/pods lookahead grows. We save space by removing duplicate states and keeping track only of states we have seen (this can cause problems in unseen scenarios).
The table is implemented as a python dictionary.
#### Agent:
The agent holds, uses, and updates the Q-table.
The user can choose which heuristic he wants the agent to use when scheduling the pods in nodes.
There are two options built into the code that the user can choose from:
Arrange the pods in a way that maintains balance in all nodes, i.e; the utility of all the nodes strives to be equal.
Compresses the pods in such a way that it utilizes as much of the memory as possible, i.e; The system strives to have cells that utilize all of their memory and ones whose entire memory is free.
(The user can easily add more heuristics by adding the appropriate function.)

 
## Next steps
Our implementation takes a continuous problem and transforms it into a discrete problem (can add references to other sources that have done so). It will be interesting to find a continuous solution for this problem. Such a solution can be implemented with deep learning techniques such as neural nets.
A good next step would be to integrate the model (or even a simple random scheduler) into a real k8s cluster. We did not research the ways cluster data is available to the scheduler and they are important for real-life usage.

