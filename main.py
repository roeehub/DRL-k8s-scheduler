from cluster_sim import *

if __name__ == '__main__':
    cluster1 = Cluster(NUM_OF_NODES, random_scheduler)
    cluster1.run(RUN_TIME_MINUTES)

