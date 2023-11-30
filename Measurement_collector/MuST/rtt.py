import json
import threading
def collect_rtt_MuST_measurements(self):
    from queue import Queue
    import datetime
    import numpy as np
    import copy
    flows = {}
    window_size = 10
    expected_value = 0
    min_sampling_speed = 3
    max_sampling_speed = 0.1
    error = 0
    last_sample_time = datetime.datetime.now()
    counter = 0

    # def average_rate_of_change(data_list, time_list):
    #     if len(data_list) < 2:
    #         return sum(data_list)
    #     data_diff = data_list[len(data_list)-1] - data_list[0]
    #     time_diff = time_list[len(data_list)-1] - time_list[0]
    #     avg_rate = data_diff/time_diff
    #     avg_rate = (time_list[len(data_list)-1] - time_list[len(data_list)-2])*(avg_rate / (len(data_list)-1))
    #     return avg_rate
    def average_rate_of_change(data_list, time_list):
        if len(time_list) < 2 or len(data_list) < 2:
            return sum(data_list)
        data_diff = data_list[-1] - data_list[-len(time_list)+1]
        time_diff = time_list[-1] - time_list[0]
        avg_rate = data_diff/time_diff
        avg_rate = (time_list[-1] - time_list[-2])*(avg_rate / (len(time_list)-1))
        return avg_rate

    def RME(sampled_data,total_data,sample_count):
        RME = abs(sampled_data - (sum(total_data[-sample_count:])/len(total_data[-sample_count:])))/(sum(total_data[-sample_count:])/len(total_data[-sample_count:]))
        return RME

    while True:
        # Receive measurements from the P4 switch
        measurements = self.Socket.recv(1024)
        # measurements = measurements.decode()
        measurements = measurements.decode('utf-8')
        measurements = measurements.strip().split("\n")
        try:
            for report in measurements:
                report = json.loads(report)
                if (report["flow_id"] in flows.keys()):
                    timestamps = flows[report["flow_id"]]["timestamps"]
                    time_list = list(flows[report["flow_id"]]["timestamps"].queue)
                    expected_value = flows[report["flow_id"]]["expected_value"]
                    sample_count = flows[report["flow_id"]]["sample_count"]
                    total_count = flows[report["flow_id"]]["total_count"]
                    sampled_data = flows[report["flow_id"]]["sampled_data"]                           
                    total_data = flows[report["flow_id"]]["total_data"]
                    last_sample_time = flows[report["flow_id"]]["last_sample_time"]
                    sampling_speed = flows[report["flow_id"]]["sampling_speed"]
                    expected_value_list = flows[report["flow_id"]]["expected_value_list"]


                else:
                    flows[report["flow_id"]] = {"expected_value" : 0,"last_sample_time": datetime.datetime.now(),\
                                                "sample_count":0,"total_count":0,"sampled_data":[],"total_data":[],"expected_value_list":[],\
                                                    "sampling_speed": 1,"timestamps" : Queue(maxsize=window_size)}
                    timestamps = flows[report["flow_id"]]["timestamps"]
                    time_list = list(flows[report["flow_id"]]["timestamps"].queue)
                    expected_value = flows[report["flow_id"]]["expected_value"]
                    sample_count = flows[report["flow_id"]]["sample_count"]
                    total_count = flows[report["flow_id"]]["total_count"]
                    sampled_data = flows[report["flow_id"]]["sampled_data"]                           
                    total_data = flows[report["flow_id"]]["total_data"]
                    last_sample_time = flows[report["flow_id"]]["last_sample_time"]
                    sampling_speed = flows[report["flow_id"]]["sampling_speed"]
                    expected_value_list = flows[report["flow_id"]]["expected_value_list"]

                report["rtt"] = float(report["rtt"])
                metric_value = float(report["rtt"])
                total_data.append(metric_value)
                flows[report["flow_id"]]["total_data"] = total_data
                if metric_value > 0:
                    error = abs(expected_value/metric_value)
                else:
                    error = 1
                if timestamps.qsize() == window_size:
                    timestamps.get()
                timestamps.put(datetime.datetime.strptime(report["report_time"],"%Y-%m-%dT%H:%M:%S.%f").timestamp())
                flows[report["flow_id"]]["timestamps"] = timestamps
                if last_sample_time.timestamp() + sampling_speed < datetime.datetime.now().timestamp():
                    flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                    sampled_data.append(metric_value)
                    flows[report["flow_id"]]["sampled_data"] = sampled_data
                    if flows[report["flow_id"]]["total_count"] == 0:
                        report["rtt_MuST_RME"] = 0
                    else:
                        report["rtt_MuST_RME"] = RME(metric_value,total_data,total_count)
                    report["rtt_MuST_sample_count"] = 1
                    flows[report["flow_id"]]["total_count"] = -1
                    report["metric_name"] = "rtt_MuST"
                    report["rtt_MuST"] = report.pop("rtt")
                    self.DB.write_measurement(report)
                    
                    if(len(total_data)>0):
                        expected_value = metric_value + average_rate_of_change(total_data,time_list)
                        
                    else:
                        expected_value = metric_value

                    expected_value_list.append(expected_value)
                    flows[report["flow_id"]]["expected_value_list"] = expected_value_list

                    # if(len(total_data)>10):
                    #     report["throughput_LP_cov"] = np.corrcoef(total_data[-10:], expected_value_list[-10:])[0, 1]

                    flows[report["flow_id"]]["expected_value"] = expected_value
                        

                    if error > 0.95 and error < 1.05:
                        sampling_speed = min(min_sampling_speed,sampling_speed + 1)
                        flows[report["flow_id"]]["sampling_speed"] = sampling_speed

                    elif error < 0.95:
                        sampling_speed = max(max_sampling_speed,error * sampling_speed)
                        flows[report["flow_id"]]["sampling_speed"] = sampling_speed

                    elif error > 1.05:
                        sampling_speed = min(min_sampling_speed,2 * sampling_speed)
                        flows[report["flow_id"]]["sampling_speed"] = sampling_speed
    
                # print(metric_value, " ",expected_value," error: ",error, ", sampling speed: ",sampling_speed)
                flows[report["flow_id"]]["total_count"]+=1
        
        except json.decoder.JSONDecodeError:
            counter +=1
            pass
            if measurements == ['']:
                break
            print(counter)
        except Exception as e:
            exception_name = type(e).__name__
            print("\nAn error occurred while getting data from the control plane:", str(e),"\n")
            print(report)
            exit()

def start_rtt_MuST_thread(self):
        collect_rtt_MuST_thread = threading.Thread(target=collect_rtt_MuST_measurements(self), name="collect_rtt_MuST_measurements")
        collect_rtt_MuST_thread.start()

