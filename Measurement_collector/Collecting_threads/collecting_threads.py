import threading
import os
import sys

sys.path.append('../../Measurement_collector')
from measurements import Measurements

def collect_measurements():
    measurements = Measurements()

def collect_rtt():
    measurements_rtt = Measurements(60003)

def collect_throughput():
    measurements_throughput = Measurements(60004)

def collect_throughput_LP():
    measurements_throughput_LP = Measurements(60007)

def collect_rtt_LP():
    measurements_rtt_LP = Measurements(60008)

def collect_throughput_MuST():
    measurements_throughput_MuST = Measurements(60009)

def collect_rtt_MuST():
    measurements_rtt_MuST = Measurements(60010)

def collect_throughput_alpha1():
    measurements_throughput = Measurements(60011)

def collect_throughput_alpha2():
    measurements_throughput = Measurements(60012)

def collect_throughput_alpha3():
    measurements_throughput = Measurements(60013)

def collect_throughput_alpha4():
    measurements_throughput = Measurements(60014)

def collect_throughput_alpha5():
    measurements_throughput = Measurements(60015)

def start_throughput_measurements_eval_no_mem():
    measurements_throughput = Measurements(60016)

collect_rtt_thread = threading.Thread(target=collect_rtt, name="collect_rtt")

collect_throughput_thread = threading.Thread(target=collect_throughput, name="collect_throughput")

collect_throughput_LP_thread = threading.Thread(target=collect_throughput_LP, name="collect_throughput_LP")

collect_rtt_LP_thread = threading.Thread(target=collect_rtt_LP, name="collect_rtt_LP")

collect_throughput_MuST_thread = threading.Thread(target=collect_throughput_MuST, name="collect_throughput_MuST")

collect_rtt_MuST_thread = threading.Thread(target=collect_rtt_MuST, name="collect_rtt_MuST")

collect_throughput_alpha1_thread = threading.Thread(target=collect_throughput_alpha1, name="collect_throughput_alpha1")

collect_throughput_alpha2_thread = threading.Thread(target=collect_throughput_alpha2, name="collect_throughput_alpha2")

collect_throughput_alpha3_thread = threading.Thread(target=collect_throughput_alpha3, name="collect_throughput_alpha3")

collect_throughput_alpha4_thread = threading.Thread(target=collect_throughput_alpha4, name="collect_throughput_alpha4")

collect_throughput_alpha5_thread = threading.Thread(target=collect_throughput_alpha5, name="collect_throughput_alpha5")

collect_throughput_no_mem_thread = threading.Thread(target=start_throughput_measurements_eval_no_mem, name="start_throughput_measurements_eval_no_mem")
