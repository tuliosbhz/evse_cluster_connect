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
        current_time = datetime.now().strftime("%m-%d-%Y")

        self.raft_file_name = f"{file_name}_raft_{current_time}.csv"

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
        self.raft_headers_written = False
        self._initialized = True
        self.last_log_time = time.time()

    def start_downtime(self):
        if self.last_down is None:
            self.last_down = time.time()

    def end_downtime(self):
        if self.last_down is not None:
            self.downtime += time.time() - self.last_down
            self.last_down = None
    
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
                    "Uptime",
                    "Average Election Time",
                    "Election Count",
                    "Average Raft Message Latency",
                    "Raft Message Throughput",
                ])
                self.raft_headers_written = True
            writer.writerow([
                datetime.now().strftime("%m-%d-%YT%H:%M:%S"), #Timestamp
                time.time() - self.start_time - sum(self.election_times), #uptime
                sum(self.election_times) / len(self.election_times) if self.election_times else 0, #Average election time
                self.election_count, #election count
                sum(self.raft_message_latencies) / len(self.raft_message_latencies) if self.raft_message_latencies else 0,
                self.raft_message_throughput / (time.time() - self.last_log_time), #That will provide the TPS for the RAFT messages
            ])
        self.reset_raft_metrics()
        self.last_log_time = time.time()

    def reset_raft_metrics(self):
        self.downtime = 0
        self.failures = 0
        self.repairs = 0
        self.election_times = []
        self.raft_message_failures = 0
        self.raft_message_latencies = []
        self.raft_message_throughput = 0
