import threading
import Database
import Listening_socket
import json

from MuST.throughput import start_throughput_MuST_thread
from MuST.rtt import start_rtt_MuST_thread

from LP.throughput import start_throughput_LP_thread
from LP.rtt import start_rtt_LP_thread

from P4.throughput import start_throughput_measurements_thread
from P4.rtt import start_rtt_measurements_thread
from P4.other_measurements import start_measurements_thread

from P4.throughput import start_throughput_measurements_eval_thread, start_throughput_measurements_eval_no_mem_thread

class Measurements:
    def __init__(self,port=60002):
        self.N = 0

        # Initiate database instance
        self.DB = Database.database("10.173.85.231",11888)

        # Initiate the socket
        self.Socket = Listening_socket.Socket(port=port).get_Listener()
        
        # Start measurement collection
        # Measurements by the Proposed System
        if port == 60003:
            start_rtt_measurements_thread(self)
        elif port == 60004:
            start_throughput_measurements_thread(self)
        
        # Measurements by the LP
        elif port == 60007:
            start_throughput_LP_thread(self)
        elif port == 60008:
            start_rtt_LP_thread(self)
        
        # Measurements by the MuST
        elif port == 60009:
            start_throughput_MuST_thread(self)
        elif port == 60010:
            start_rtt_MuST_thread(self)
        elif port == 60011:
            start_throughput_measurements_eval_thread(self,0.025)
        elif port == 60012:
            start_throughput_measurements_eval_thread(self,0.075)
        elif port == 60013:
            start_throughput_measurements_eval_thread(self,0.1)
        elif port == 60014:
            start_throughput_measurements_eval_thread(self,0.15)
        elif port == 60015:
            start_throughput_measurements_eval_thread(self,0.2)
        elif port == 60016:
            start_throughput_measurements_eval_no_mem_thread(self,0.05)
        # else:
        #     start_measurements_thread(self)

