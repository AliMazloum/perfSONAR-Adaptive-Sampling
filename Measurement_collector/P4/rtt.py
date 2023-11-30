import json
import threading

def collect_rtt_measurements(self):
        from queue import Queue
        import datetime
        import numpy as np
        import copy
        flows = {}
        alpha = 0.5
        window_size = 5
        data = Queue(maxsize=window_size)
        expected_value = 0
        sampling_speed = 0.1
        min_sampling_speed = 5
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
                    if (report["flow_id"] not in flows.keys()):
                        flows[report["flow_id"]] = {"data" : Queue(maxsize=window_size),"expected_value" : 0,"sampling_speed":0.1,"min_sampling_speed":5\
                                                    ,"max_sampling_speed" :0.1,"last_sample_time":datetime.datetime.now(),"prev_report":report,\
                                                    "sample_count":0,"total_count":0,"sampled_data":[],"total_data":[],"expected_value_list":[],\
                                                        }

                    data = flows[report["flow_id"]]["data"]
                    data_list = list(flows[report["flow_id"]]["data"].queue)
                    expected_value = flows[report["flow_id"]]["expected_value"]
                    sampling_speed = flows[report["flow_id"]]["sampling_speed"]
                    min_sampling_speed = flows[report["flow_id"]]["min_sampling_speed"]
                    max_sampling_speed = flows[report["flow_id"]]["max_sampling_speed"]
                    last_sample_time = flows[report["flow_id"]]["last_sample_time"]
                    prev_report = flows[report["flow_id"]]["prev_report"]
                    sample_count = flows[report["flow_id"]]["sample_count"]
                    total_count = flows[report["flow_id"]]["total_count"]
                    sampled_data = flows[report["flow_id"]]["sampled_data"]                           
                    total_data = flows[report["flow_id"]]["total_data"]
                    expected_value_list = flows[report["flow_id"]]["expected_value_list"]

                    metric_value = float(report["rtt"])
                    if len(data_list) > 0 and metric_value > 0 and metric_value != data_list[len(data_list)-1]:
                        error = abs(expected_value/metric_value)
                    elif len(data_list) > 0 and metric_value == data_list[len(data_list)-1]:
                        error = 1

                    if data.qsize() == window_size:
                        data.get()
                    data.put(metric_value)
                    flows[report["flow_id"]]["data"] = data
                    total_data.append(metric_value)
                    flows[report["flow_id"]]["total_data"] = total_data

                    expected_value = ((1-alpha) * metric_value) + alpha*(sum(data_list)/data.qsize())
                    expected_value_list.append(expected_value)
                    flows[report["flow_id"]]["expected_value_list"] = expected_value_list
                    flows[report["flow_id"]]["expected_value"] = expected_value
                    flows[report["flow_id"]]["prev_report"] = copy.deepcopy(report)

                    if error > 0.95 and error < 1.05:
                        sampling_speed = min(min_sampling_speed,sampling_speed + 1)
                        flows[report["flow_id"]]["sampling_speed"] = sampling_speed
                        if last_sample_time.timestamp() + min(sampling_speed, min_sampling_speed) < datetime.datetime.now().timestamp():
                            flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                            sampled_data.append(metric_value)
                            flows[report["flow_id"]]["sampled_data"] = sampled_data
                            sample_count =1
                            report["rtt_RME"] = RME(metric_value,total_data,total_count)
                            flows[report["flow_id"]]["total_count"] = -1
                            flows[report["flow_id"]]["total_count"] = 0  
                            self.DB.write_measurement(report)
                    elif error < 0.95:
                        sampling_speed = max(max_sampling_speed,error * sampling_speed)
                        flows[report["flow_id"]]["sampling_speed"] = sampling_speed
                        flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                        sample_count =1
                        sampled_data.append(float(prev_report["rtt"]))
                        sampled_data.append(metric_value)
                        flows[report["flow_id"]]["sampled_data"] = sampled_data
                        if flows[report["flow_id"]]["total_count"] > 0:
                            report["rtt_RME"] = RME((sum(sampled_data[-2:])/2),total_data,total_count)
                            self.DB.write_measurement(prev_report)
                        else:
                            report["rtt_RME"] = 0
                        flows[report["flow_id"]]["total_count"] = -1
                        
                        self.DB.write_measurement(report)
                    elif error > 1.05:
                        sampling_speed = max(max_sampling_speed,1/error * sampling_speed)
                        flows[report["flow_id"]]["sampling_speed"] = sampling_speed
                        flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                        sampled_data.append(float(prev_report["rtt"]))
                        sampled_data.append(metric_value)
                        flows[report["flow_id"]]["sampled_data"] = sampled_data
                        sample_count = 1
                        if flows[report["flow_id"]]["total_count"] > 0:
                            report["rtt_RME"] = RME((sum(sampled_data[-2:])/2),total_data,total_count)
                            self.DB.write_measurement(prev_report)
                        else:
                            report["rtt_RME"] = 0
                        flows[report["flow_id"]]["total_count"] = -1           
                        # self.DB.write_measurement(prev_report)
                        self.DB.write_measurement(report)
                    
                    report["metric_name"] = "rtt_cont"
                    report["rtt_cont"] = report.pop("rtt")
                    report["rtt_sample_count"] = sample_count
                    report["rtt_total_count"] = 1
                    self.DB.write_measurement(report)
                    flows[report["flow_id"]]["total_count"] +=1
                    # print(flows[report["flow_id"]]["total_count"])

            except json.decoder.JSONDecodeError:
                counter +=1
                pass
                if measurements == ['']:
                    break
                print(counter)
            except Exception as e:
                exception_name = type(e).__name__
                print("\nAn error occurred while getting data from the control plane:", str(e),"\n")
                exit()  

def start_rtt_measurements_thread(self):
    collect_rtt_measurements_thread = threading.Thread(target=collect_rtt_measurements(self), name="collect_rtt_measurements")
    collect_rtt_measurements_thread.start()

