import random
import matplotlib.pyplot as plt
import numpy as np

def initialize_simulation(num_nodes):
    t = 0
    followers = list(range(num_nodes))
    candidates = 0
    return t, followers, candidates

def receive_heartbeat(follower, packet_loss_rate):
    if random.random() > packet_loss_rate:
        return True
    return False

def run_raft_test(num_nodes, packet_loss_rate, election_time_counter, tau):
    t, followers, candidates = initialize_simulation(num_nodes)
    time_recorded = None
    heartbeat_counts = []

    while candidates < num_nodes / 2:
        for follower in followers:
            if receive_heartbeat(follower, packet_loss_rate):
                election_time_counter[follower] = 0
            else:
                election_time_counter[follower] -= 1

                if election_time_counter[follower] == 0:
                    candidates += 1
                    followers.remove(follower)

        if candidates > num_nodes / 2:
            time_recorded = t
        else:
            t += tau

    return time_recorded, heartbeat_counts

def plot_cdf(heartbeat_counts):
    sorted_counts = np.sort(heartbeat_counts)
    cdf = np.arange(1, len(sorted_counts) + 1) / len(sorted_counts)

    plt.plot(sorted_counts, cdf, marker='o')
    plt.xlabel('Number of Heartbeats')
    plt.ylabel('Cumulative Probability')
    plt.title('CDF of Heartbeats Before Network Split')
    plt.show()

if __name__ == '__main__':
    num_nodes = 10
    packet_loss_rate = 0.2
    election_time_counter = {follower: 3 for follower in range(num_nodes)}
    tau = 1  # simulation time step

    time_recorded, heartbeat_counts = run_raft_test(num_nodes, packet_loss_rate, election_time_counter, tau)

    if time_recorded is not None:
        print(f"Network split recorded at time {time_recorded}")
    else:
        print("Network split not detected within the given conditions")

    plot_cdf(heartbeat_counts)
