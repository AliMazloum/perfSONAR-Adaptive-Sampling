from measurements import Measurements
from Collecting_threads.collecting_threads import collect_rtt_thread, collect_throughput_thread
from Collecting_threads.collecting_threads import collect_throughput_alpha1_thread,collect_throughput_alpha2_thread
from Collecting_threads.collecting_threads import collect_throughput_alpha3_thread, collect_throughput_alpha4_thread
from Collecting_threads.collecting_threads import collect_throughput_alpha5_thread, collect_throughput_no_mem_thread
from Collecting_threads.collecting_threads import collect_throughput_LP_thread, collect_rtt_LP_thread
from Collecting_threads.collecting_threads import collect_throughput_MuST_thread, collect_rtt_MuST_thread
import threading



collect_rtt_thread.start()

collect_throughput_thread.start()

collect_throughput_LP_thread.start()

collect_rtt_LP_thread.start()

collect_throughput_MuST_thread.start()

collect_rtt_MuST_thread.start()

# collect_throughput_alpha1_thread.start()

# collect_throughput_alpha2_thread.start()

# collect_throughput_alpha3_thread.start()

# collect_throughput_alpha4_thread.start()

# collect_throughput_alpha5_thread.start()

collect_throughput_no_mem_thread.start()

