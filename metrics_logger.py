import time
import csv
import threading
from datetime import datetime

class MetricsLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, file_name="metrics"):
        if self._initialized:
            return
        # Initialize file for benchmarks
        current_time = datetime.now().strftime("%m-%d-%Y_%H_%M_%S")

        self.raft_file_name = f"{file_name}_raft_{current_time}.csv"
        self.ocpp_file_name = f"{file_name}_ocpp_{current_time}.csv"

        self.start_time = time.time()
        self.downtime = 0
        self.last_down = None
        self.requests = 0
        self.failures = 0
        self.repairs = 0
        self.election_times = []
        self.last_election_start = None
        self.election_count = 0
        self.raft_message_failures = 0
        self.raft_message_latencies = []
        self.raft_message_throughput = 0
        self.ocpp_latency = []
        self.ocpp_throughput = 0
        self.ocpp_message_name = ""
        self.raft_headers_written = False
        self.ocpp_headers_written = False
        self._initialized = True

    def start_downtime(self):
        if self.last_down is None:
            self.last_down = time.time()

    def end_downtime(self):
        if self.last_down is not None:
            self.downtime += time.time() - self.last_down
            self.last_down = None

    def record_ocpp_latency(self, start_time, end_time):
        latency = end_time - start_time
        self.ocpp_latency.append(latency)
        self.requests += 1

    def record_ocpp_throughput(self, msg_size):
        total_latency = sum(self.ocpp_latency) if self.ocpp_latency else 1
        self.ocpp_throughput = (msg_size * self.requests * 8) / (total_latency * 1_000_000)

    def record_failure(self):
        self.failures += 1
        self.start_downtime()

    def record_repair(self):
        self.repairs += 1
        self.end_downtime()

    def start_election(self):
        self.last_election_start = time.time()

    def end_election(self):
        if self.last_election_start is not None:
            self.election_times.append(time.time() - self.last_election_start)
            self.last_election_start = None
            self.election_count += 1

    def record_raft_message_failure(self):
        self.raft_message_failures += 1

    def record_raft_message_latency(self, latency):
        self.raft_message_latencies.append(latency)

    def record_raft_message_throughput(self, count):
        self.raft_message_throughput += count

    def log_raft_metrics(self, heartbeat, step_down, election_spread):
        with open(self.raft_file_name, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not self.raft_headers_written:
                writer.writerow([
                    "Timestamp",
                    "heartbeat_interval",
                    "step_down_missed_heartbeats",
                    "election_interval_spread",
                    "Uptime",
                    "MTBF",
                    "MTTR",
                    "Average Election Time",
                    "Election Count",
                    "Raft Message Failures",
                    "Average Raft Message Latency",
                    "Raft Message Throughput",
                ])
                self.raft_headers_written = True
            writer.writerow([
                datetime.now().strftime("%m-%d-%Y_%H:%M:%S"), #Timestamp
                heartbeat, #heartbeat_interval
                step_down, #step_down_missed_heartbeats
                election_spread, #election_interval_spread
                time.time() - self.start_time - self.downtime, #uptime
                (time.time() - self.start_time) / self.failures if self.failures else 0, #MTBF 
                self.downtime / self.repairs if self.repairs else 0, #MTTR
                sum(self.election_times) / len(self.election_times) if self.election_times else 0, #Average election time
                self.election_count, #election count
                self.raft_message_failures,
                sum(self.raft_message_latencies) / len(self.raft_message_latencies) if self.raft_message_latencies else 0,
                self.raft_message_throughput,
            ])
        self.reset_raft_metrics()

    def log_ocpp_metrics(self, ocpp_active_clients, ocpp_denied_boots, heartbeat_interval):
        with open(self.ocpp_file_name, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not self.ocpp_headers_written:
                writer.writerow([
                    "Timestamp",
                    "OCPP active clientes",
                    "OCPP denied cps",
                    "HeartbeatInterval",
                ])
                self.ocpp_headers_written = True
            writer.writerow([
                datetime.now().strftime("%m-%d-%Y_%H:%M:%S"),
                ocpp_active_clients,
                ocpp_denied_boots,
                heartbeat_interval
            ])
        self.reset_ocpp_metrics()

    def reset_raft_metrics(self):
        self.downtime = 0
        self.failures = 0
        self.repairs = 0
        self.election_times = []
        self.election_count = 0
        self.raft_message_failures = 0
        self.raft_message_latencies = []
        self.raft_message_throughput = 0

    def reset_ocpp_metrics(self):
        self.ocpp_latency = []
        self.requests = 0
        self.ocpp_throughput = 0
        self.ocpp_message_name = ""
