import datetime
import random
import threading
import uuid
import logging
from constants import *
import numpy as np
import coloredlogs
import utils

# TODO list:
"""
- Improve scheduler assessment - relative to greedy/overall success over time.
- keep better track of the cluster? - curr pending pods, curr node loads e.c.
- add a test of some sort?
"""

logging.basicConfig(
    level=logging.DEBUG,
    format='{asctime} {levelname:<6} {message}',
    style='{'
)

coloredlogs.install()


class PodState:
    pending = 0
    assigned = 1


class Pod:
    def __init__(self):
        self.state = PodState.pending
        self.memory = \
            max(round(np.random.normal(loc=POD_MEMORY_EXPECTATION, scale=POD_MEMORY_VARIANCE), 2), POD_MIN_MEMORY)
        self.run_time_seconds = random.uniform(MIN_TIME_POD, MAX_TIME_POD)
        self.uuid = str(uuid.uuid4())[:6]
        self.creation_time = datetime.datetime.now()
        # TODO maybe
        # self.start_time = datetime.datetime.now()
        # self.time_pending = 0


class Node:
    def __init__(self, index):
        self.index = index
        self.memory_left = NODE_MEMORY
        self.pods = {}
        # TODO maybe
        # self.events = []


class Cluster:
    def __init__(self, number_of_nodes):
        logging.info("Initializing cluster...")
        logging.info(f"Cluster config: {NUM_OF_NODES=}, {NODE_MEMORY=}, {SPAWN_TIME_INTERVAL_SECS=}, {MAX_NUM_OF_PODS=}, "
                     f"{ALPHA=}, {GAMMA=}")
        self.nodes = [Node(index) for index in range(number_of_nodes)]
        self.new_pods_to_add = {}
        self.pending_pods = {}
        self.assigned_pods = {}
        self.node_selection_func = None  # node_selection_func # Would be Q table!!!
        self.num_of_pod_lookahead = 1
        # self.i_for_logging = 0
        # TODO maybe a quicker cluster view with:
        # self.pending_pods_memory = []
        # self.nodes_memory_left = [(i, NODE_MEMORY) for i in range(number_of_nodes)]

    # def run(self, time_in_minutes):
    #     logging.info("Run started")
    #     finish_time = datetime.datetime.now() + datetime.timedelta(minutes=time_in_minutes)
    #     utils.set_interval(self.spawn_pod, SPAWN_TIME_INTERVAL_SECS)
    #     utils.set_interval(self.log_nodes_utility, UTILITY_LOG_INTERVAL_SECS)
    #     while datetime.datetime.now() < finish_time:
    #         # self.log_cluster_alive()
    #         pods_to_assign = []
    #         for pod in self.pending_pods.values():
    #             cluster_view = self.get_cluster_view(pod)
    #             node_index = self.node_selection_func(cluster_view)
    #             # logging.info(f"Pod {pod.uuid} Selected for Node {node_index}")
    #             if node_index > -1:  # decided to schedule
    #                 scheduled = self.schedule_pod(self.nodes[node_index], self.pending_pods[pod.uuid])
    #                 if scheduled:  # scheduling worked
    #                     pods_to_assign.append(pod)
    #         for pod in pods_to_assign:
    #             self.pending_pods.pop(pod.uuid)
    #             self.assigned_pods[pod.uuid] = pod
    #         self.pending_pods = {**self.pending_pods, **self.new_pods_to_add}
    #         self.new_pods_to_add.clear()
    #     utils.stop_interval()
    #     while len(self.assigned_pods) > 0:
    #         sleep(0.1)
    #     logging.info("Shutting down...")

    def train_run(self, time_in_seconds):
        logging.info(f"Run started, running for {time_in_seconds} seconds")
        utils.set_interval(self.spawn_pod_train, SPAWN_TIME_INTERVAL_SECS)
        utils.set_interval(self.log_nodes_utility, UTILITY_LOG_INTERVAL_SECS)
        logging.info("Done setting up intervals")
        # logging.info(f"train_run is now sleeping for {time_in_seconds} seconds")
        # sleep(time_in_seconds)
        # utils.stop_interval()
        # logging.info("Shutting down...")

    @staticmethod
    def end_train_run():
        logging.info("In End")
        utils.stop_interval()
        logging.info("Shutting down...")

    def schedule_pod(self, node_index):
        pod_uuid_to_sched = sorted(self.pending_pods, key=lambda x: self.pending_pods[x].creation_time)[0]
        # logging.info(f"Inside schedule pod, with pod {pod_uuid_to_sched}")
        # logging.info(f"node_index: {node_index}")
        overload = False
        if node_index > -1:  # decided to schedule
            node = self.nodes[node_index]
            pod = self.pending_pods[pod_uuid_to_sched]
            # logging.info(f"{pod.memory=}, {node.memory_left=}")
            if pod.memory < node.memory_left:
                # node
                node.memory_left -= pod.memory
                node.pods[pod_uuid_to_sched] = pod
                # pod
                pod.state = PodState.assigned
                scheduled = True
                self.pending_pods.pop(pod.uuid)
                self.assigned_pods[pod.uuid] = pod
                threading.Timer(pod.run_time_seconds, self.pod_finished, [node, pod]).start()
                logging.info(f"Pod {pod.uuid} with memory demand {pod.memory} is scheduled on:")
                logging.info(f"Node {node.index} with {node.memory_left} memory left")
            else:
                logging.info(f"Insufficient memory {pod.memory=}, {node.memory_left=}")
                overload = True
                scheduled = False
        else:  # Put in back of line
            logging.info(f"action was {node_index=}")
            scheduled = False
            self.pending_pods[pod_uuid_to_sched].creation_time = datetime.datetime.now()
        if overload:
            pass
            # logging.info(f"OVERLOAD!")
        return scheduled, overload

    def get_cluster_view(self, target_pod):  # TODO json format?
        target_pod_view = (target_pod.uuid, target_pod.memory)
        other_pending_pods_view = [(pod.uuid, pod.memory) for pod in self.pending_pods.values() if pod.uuid
                                   != target_pod.uuid]
        nodes_memory_view = [(node.index, node.memory_left) for node in self.nodes]
        return target_pod_view, other_pending_pods_view, nodes_memory_view

    def get_current_state(self):
        pod_lookahead_keys = \
            sorted(self.pending_pods, key=lambda x: self.pending_pods[x].creation_time)[:self.num_of_pod_lookahead]
        pod_lookahead_list = [(self.pending_pods[i].uuid, self.pending_pods[i].memory) for i in pod_lookahead_keys]
        nodes_memory_view = [(node.index, node.memory_left) for node in self.nodes]
        return pod_lookahead_list, nodes_memory_view

    # def spawn_pod(self):
    #     num_of_pods = len(self.pending_pods) + len(self.assigned_pods)
    #     if random.random() > num_of_pods / MAX_NUM_OF_PODS:
    #         new_pod = Pod()
    #         self.new_pods_to_add[new_pod.uuid] = new_pod
    #         # self.pending_pods[new_pod.uuid] = new_pod
    #         logging.info(f"New pod pending! UUID: {new_pod.uuid}, Memory: {new_pod.memory}, runtime: "
    #                      f"{new_pod.run_time_seconds}")
    #     else:
    #         logging.warning(f"Pod not created.")
    #     logging.warning(f"{num_of_pods} pods are currently running")

    def spawn_pod_train(self):
        num_of_pods = len(self.pending_pods) + len(self.assigned_pods)
        if random.random() > num_of_pods / MAX_NUM_OF_PODS:
            new_pod = Pod()
            self.pending_pods[new_pod.uuid] = new_pod
            # logging.info(f"New pod pending! UUID: {new_pod.uuid}, Memory: {new_pod.memory}")
        else:
            pass
            # logging.warning(f"Tried to spawn pod but no luck, {num_of_pods=}, {MAX_NUM_OF_PODS=}")

    def pod_finished(self, node, pod):
        node.memory_left += pod.memory
        node.pods.pop(pod.uuid, None)
        self.assigned_pods.pop(pod.uuid, None)
        logging.info(f"Pod {pod.uuid} finished")

    def log_nodes_utility(self):
        node_capacities = [round(((NODE_MEMORY - node.memory_left) / NODE_MEMORY), 2) for node in self.nodes]
        logging.warning("-"*100)
        nodes_utility_string = "Nodes memory utility: "
        for capacity in node_capacities:
            capacity_2f = "{:.2f}".format(capacity * 100)
            nodes_utility_string += f" {capacity_2f}%"
        logging.warning(nodes_utility_string)
        total_cluster_memory_2f = "{:.2f}".format(round(sum(node_capacities) / NUM_OF_NODES, 2) * 100)
        logging.warning(f"Total cluster memory utility: {total_cluster_memory_2f}%")
        logging.warning(f"Number of pending pods: {len(self.pending_pods)}")
        logging.warning(f"Number of assigned pods: {len(self.assigned_pods)}")
        logging.warning("-"*100)


def random_scheduler():
    if random.random() > 0.95:
        return -1
    return random.choice(list(range(NUM_OF_NODES)))


# cluster = Cluster(3)
# cluster.train_run(10)
# logging.critical(MAX_NUM_OF_PODS)
