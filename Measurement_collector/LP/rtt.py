import json
import threading

def collect_rtt_LP_measurements(self):
    from queue import Queue
    import datetime
    import numpy as np
    import copy
    flows = {}
    alpha = 0.1
    window_size = 4
    data = Queue(maxsize=window_size)
    expected_value = 0
    min_sampling_speed = 3
    max_sampling_speed = 0.1
    error = 0
    last_sample_time = datetime.datetime.now()
    counter = 0
    def RME(sampled_data,total_data,sample_count):
        RME = abs(sampled_data - (sum(total_data[-sample_count:])/len(total_data[-sample_count:])))/(sum(total_data[-sample_count:])/len(total_data[-sample_count:]))
        return RME

    while True:
        data_list = list(data.queue)
        # Receive measurements from the P4 switch
        measurements = self.Socket.recv(1024)
        # measurements = measurements.decode()
        measurements = measurements.decode('utf-8')
        measurements = measurements.strip().split("\n")
        try:
            for report in measurements:
                report = json.loads(report)
                if (report["flow_id"] in flows.keys()):
                    data = flows[report["flow_id"]]["data"]
                    data_list = list(flows[report["flow_id"]]["data"].queue)
                    expected_value = flows[report["flow_id"]]["expected_value"]
                    sample_count = flows[report["flow_id"]]["sample_count"]
                    total_count = flows[report["flow_id"]]["total_count"]
                    sampled_data = flows[report["flow_id"]]["sampled_data"]                           
                    total_data = flows[report["flow_id"]]["total_data"]
                    last_sample_time = flows[report["flow_id"]]["last_sample_time"]
                    sampling_speed = flows[report["flow_id"]]["sampling_speed"]
                    expected_value_list = flows[report["flow_id"]]["expected_value_list"]


                else:
                    flows[report["flow_id"]] = {"data" : Queue(maxsize=window_size),"expected_value" : 0,"last_sample_time": datetime.datetime.now(),\
                                                "sample_count":0,"total_count":0,"sampled_data":[],"total_data":[],"expected_value_list":[],\
                                                    "sampling_speed": 1}
                    data = flows[report["flow_id"]]["data"]
                    data_list = list(flows[report["flow_id"]]["data"].queue)
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
                data.put(metric_value)
                total_data.append(metric_value)
                # if len(data_list) > 0:
                #     metric_value = (1-alpha)*metric_value + alpha*(sum(data_list)/(len(data_list)+1))
                
                flows[report["flow_id"]]["total_data"] = total_data

                if len(data_list) > 0 and metric_value > 0 and metric_value != data_list[len(data_list)-1]:
                    error = abs(expected_value/metric_value)
                elif len(data_list) > 0 and metric_value == data_list[len(data_list)-1]:
                    error = 1

                if data.qsize() == window_size:
                    data.get()

                flows[report["flow_id"]]["data"] = data
                
                if last_sample_time.timestamp() + sampling_speed < datetime.datetime.now().timestamp():
                    flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                    sampled_data.append(metric_value)
                    flows[report["flow_id"]]["sampled_data"] = sampled_data
                    if flows[report["flow_id"]]["total_count"] == 0:
                        report["rtt_LP_RME"] = 0
                    else:
                        report["rtt_LP_RME"] = RME(metric_value,total_data,total_count)
                    report["rtt_LP_sample_count"] = 1
                    flows[report["flow_id"]]["total_count"] = -1
                    report["metric_name"] = "rtt_LP"
                    report["rtt_LP"] = report.pop("rtt")
                    self.DB.write_measurement(report)
                    
                    if(len(data_list)>0):
                        expected_value = (1-alpha)*metric_value + alpha*(sum(data_list)/(len(data_list)))
                        
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
                        sampling_speed = max(max_sampling_speed,1/error * sampling_speed)
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

def start_rtt_LP_thread(self):
    collect_rtt_LP_thread = threading.Thread(target=collect_rtt_LP_measurements(self), name="collect_rtt_LP_measurements")
    collect_rtt_LP_thread.start()

