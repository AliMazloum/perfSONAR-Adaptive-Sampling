import json
import threading


def collect_throughput_measurements(self,alpha = 0.05):
    from queue import Queue
    import datetime
    import numpy as np
    import copy
    flows = {}
    window_size = 10
    data = Queue(maxsize=window_size)
    timestamps = Queue(maxsize=window_size)
    expected_value = 0
    sampling_speed = 0.1
    min_sampling_speed = 10
    max_sampling_speed = 0.1
    error = 0
    last_sample_time = datetime.datetime.now()
    counter = 0
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
        data_list = list(data.queue)
        time_list = list(timestamps.queue)
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
                    timestamps = flows[report["flow_id"]]["timestamps"]
                    data_list = list(flows[report["flow_id"]]["data"].queue)
                    time_list = list(flows[report["flow_id"]]["timestamps"].queue)
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

                else:
                    flows[report["flow_id"]] = {"data" : Queue(maxsize=window_size),"expected_value" : 0,"sampling_speed":0.1,\
                                                "min_sampling_speed":5,"max_sampling_speed" :0.1,"last_sample_time":datetime.datetime.now()\
                                                    ,"timestamps": Queue(maxsize=window_size),"prev_report":report,\
                                                        "sample_count":0,"total_count":0,"sampled_data":[],"total_data":[],"expected_value_list":[]}
                    data = flows[report["flow_id"]]["data"]
                    timestamps = flows[report["flow_id"]]["timestamps"]
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

                report["throughput"] = float(report["throughput"])*10
                metric_value = float(report["throughput"])
                data.put(metric_value)
                total_data.append(metric_value)
                
                flows[report["flow_id"]]["total_data"] = total_data

                if len(total_data) > 1 and metric_value > 0 and metric_value != total_data[len(total_data)-2]:
                    error = abs(expected_value/metric_value)
                    # print("The error is: ", error, " the expected value is: ", expected_value, " the metric value is: ", metric_value)
                elif len(total_data) > 1 and metric_value == total_data[len(data_list)-2]:
                    error = 1

                if data.qsize() == window_size:
                    data.get()
                    timestamps.get()
                timestamps.put(datetime.datetime.strptime(report["report_time"],"%Y-%m-%dT%H:%M:%S.%f").timestamp())

                flows[report["flow_id"]]["data"] = data
                flows[report["flow_id"]]["timestamps"] = timestamps
                flows[report["flow_id"]]["prev_report"] = copy.deepcopy(report)
                
                if(len(total_data)>0):
                    expected_value = metric_value + average_rate_of_change(total_data,time_list)
                    
                else:
                    expected_value = metric_value
                expected_value_list.append(expected_value)
                flows[report["flow_id"]]["expected_value_list"] = expected_value_list
                if(len(total_data)>10):
                    report["throughput_cov"] = np.corrcoef(total_data[-10:], expected_value_list[-10:])[0, 1]
                flows[report["flow_id"]]["expected_value"] = expected_value
                    

                if error > (1-alpha) and error < (1+alpha):
                    sampling_speed = min(min_sampling_speed,sampling_speed + 1)
                    flows[report["flow_id"]]["sampling_speed"] = sampling_speed
                    if last_sample_time.timestamp() + min(sampling_speed, min_sampling_speed) < datetime.datetime.now().timestamp():
                        flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                        sampled_data.append(metric_value)
                        flows[report["flow_id"]]["sampled_data"] = sampled_data
                        
                        sample_count =1
                        report["throughput_RME"] = RME(metric_value,total_data,total_count)
                        # if report["throughput_RME"] > 0.1:
                        # flows[report["flow_id"]]["total_count"] = 0
                        # print(report)
                        self.DB.write_measurement(report)


                elif error < (1-alpha):
                    sampling_speed = max(max_sampling_speed,error * sampling_speed)
                    flows[report["flow_id"]]["sampling_speed"] = sampling_speed
                    flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                    sample_count =1
                    sampled_data.append(prev_report["throughput"])
                    sampled_data.append(metric_value)
                    flows[report["flow_id"]]["sampled_data"] = sampled_data

                    if flows[report["flow_id"]]["total_count"] == 0:
                        report["throughput_RME"] = 0

                    elif flows[report["flow_id"]]["total_count"] == 1:
                        report["throughput_RME"] = RME((sum(sampled_data[-1:])/1),total_data,total_count)
                        prev_report["throughput_sample_count"] =1
                        self.DB.write_measurement(prev_report)
                    else:
                        report["throughput_RME"] = RME((sum(sampled_data[-2:])/2),total_data,total_count)
                        prev_report["throughput_sample_count"] =1
                        self.DB.write_measurement(prev_report)

                    
                    self.DB.write_measurement(report)


                elif error > (1+alpha):
                    sampling_speed = max(max_sampling_speed,1/error * sampling_speed)
                    flows[report["flow_id"]]["sampling_speed"] = sampling_speed
                    flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                    sampled_data.append(prev_report["throughput"])
                    sampled_data.append(metric_value)
                    flows[report["flow_id"]]["sampled_data"] = sampled_data

                    sample_count =1
                    if flows[report["flow_id"]]["total_count"] == 0:
                        report["throughput_RME"] = 0

                    elif flows[report["flow_id"]]["total_count"] == 1:
                        report["throughput_RME"] = RME((sum(sampled_data[-1:])/1),total_data,total_count)
                        # print("RME: ", report["throughput_RME"]," error: ",error," ",sum(sampled_data[-1:])/1," ",total_data[-total_count:])
                        self.DB.write_measurement(prev_report)
                    else:
                        report["throughput_RME"] = RME((sum(sampled_data[-2:])/2),total_data,total_count)
                        self.DB.write_measurement(prev_report)
                    
                    self.DB.write_measurement(report)
                    
                
                # print(metric_value, " ",expected_value," error: ",error, ", sampling speed: ",sampling_speed)
                report["throughput_total_count"] = 1
                report["throughput_sample_count"] = sample_count
                report["metric_name"] = "throughput_cont"
                report["throughput_cont"] = report.pop("throughput")
                # print(report,"\n")
                self.DB.write_measurement(report)
                if sample_count == 0:
                    flows[report["flow_id"]]["total_count"]+=1
                else:
                    flows[report["flow_id"]]["total_count"] = 0
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
            print(report)
            print(prev_report)
            exit()


def start_throughput_measurements_thread(self,alpha=0.05):
    collect_throughput_measurements_thread = threading.Thread(target=collect_throughput_measurements(self,alpha), name="collect_throughput_measurements")
    collect_throughput_measurements_thread.start()


def collect_throughput_measurements_eval(self,alpha = 0.05):
    from queue import Queue
    import datetime
    import numpy as np
    import copy
    flows = {}
    window_size = 10
    data = Queue(maxsize=window_size)
    timestamps = Queue(maxsize=window_size)
    expected_value = 0
    sampling_speed = 0.1
    min_sampling_speed = 10
    max_sampling_speed = 0.1
    error = 0
    last_sample_time = datetime.datetime.now()
    counter = 0
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
        data_list = list(data.queue)
        time_list = list(timestamps.queue)
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
                    timestamps = flows[report["flow_id"]]["timestamps"]
                    data_list = list(flows[report["flow_id"]]["data"].queue)
                    time_list = list(flows[report["flow_id"]]["timestamps"].queue)
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

                else:
                    flows[report["flow_id"]] = {"data" : Queue(maxsize=window_size),"expected_value" : 0,"sampling_speed":0.1,\
                                                "min_sampling_speed":5,"max_sampling_speed" :0.1,"last_sample_time":datetime.datetime.now()\
                                                    ,"timestamps": Queue(maxsize=window_size),"prev_report":report,\
                                                        "sample_count":0,"total_count":0,"sampled_data":[],"total_data":[],"expected_value_list":[]}
                    data = flows[report["flow_id"]]["data"]
                    timestamps = flows[report["flow_id"]]["timestamps"]
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

                report["metric_name"] = f"throughput_{alpha}"
                report[f"throughput_{alpha}"] = report.pop("throughput")
                report[f"throughput_{alpha}"] = float(report[f"throughput_{alpha}"])*10
                metric_value = float(report[f"throughput_{alpha}"])
                data.put(metric_value)
                total_data.append(metric_value)

                
                flows[report["flow_id"]]["total_data"] = total_data

                if len(total_data) > 1 and metric_value > 0 and metric_value != total_data[len(total_data)-2]:
                    error = abs(expected_value/metric_value)
                    # print("The error is: ", error, " the expected value is: ", expected_value, " the metric value is: ", metric_value)
                elif len(total_data) > 1 and metric_value == total_data[len(data_list)-2]:
                    error = 1

                if data.qsize() == window_size:
                    data.get()
                    timestamps.get()
                timestamps.put(datetime.datetime.strptime(report["report_time"],"%Y-%m-%dT%H:%M:%S.%f").timestamp())

                flows[report["flow_id"]]["data"] = data
                flows[report["flow_id"]]["timestamps"] = timestamps
                flows[report["flow_id"]]["prev_report"] = copy.deepcopy(report)
                
                if(len(total_data)>0):
                    expected_value = metric_value + average_rate_of_change(total_data,time_list)
                    
                else:
                    expected_value = metric_value
                expected_value_list.append(expected_value)
                flows[report["flow_id"]]["expected_value_list"] = expected_value_list
                if(len(total_data)>10):
                    report["throughput_cov"] = np.corrcoef(total_data[-10:], expected_value_list[-10:])[0, 1]
                flows[report["flow_id"]]["expected_value"] = expected_value
                    

                if error > (1-alpha) and error < (1+alpha):
                    sampling_speed = min(min_sampling_speed,sampling_speed + 1)
                    flows[report["flow_id"]]["sampling_speed"] = sampling_speed
                    if last_sample_time.timestamp() + min(sampling_speed, min_sampling_speed) < datetime.datetime.now().timestamp():
                        flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                        sampled_data.append(metric_value)
                        flows[report["flow_id"]]["sampled_data"] = sampled_data
                        
                        sample_count =1
                        report[f"throughput_{alpha}_RME"] = RME(metric_value,total_data,total_count)
                        # if report["throughput_RME"] > 0.1:
                        # flows[report["flow_id"]]["total_count"] = 0
                        # print(report)
                        self.DB.write_measurement(report)


                elif error < (1-alpha):
                    sampling_speed = max(max_sampling_speed,error * sampling_speed)
                    flows[report["flow_id"]]["sampling_speed"] = sampling_speed
                    flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                    sample_count =1
                    sampled_data.append(prev_report[f"throughput_{alpha}"])
                    sampled_data.append(metric_value)
                    flows[report["flow_id"]]["sampled_data"] = sampled_data

                    if flows[report["flow_id"]]["total_count"] == 0:
                        report[f"throughput_{alpha}_RME"] = 0

                    elif flows[report["flow_id"]]["total_count"] == 1:
                        report[f"throughput_{alpha}_RME"] = RME((sum(sampled_data[-1:])/1),total_data,total_count)
                        prev_report[f"throughput_{alpha}_sample_count"] =1
                        self.DB.write_measurement(prev_report)
                    else:
                        report[f"throughput_{alpha}_RME"] = RME((sum(sampled_data[-2:])/2),total_data,total_count)
                        prev_report[f"throughput_{alpha}_sample_count"] =1
                        self.DB.write_measurement(prev_report)

                    
                    self.DB.write_measurement(report)


                elif error > (1+alpha):
                    sampling_speed = max(max_sampling_speed,1/error * sampling_speed)
                    flows[report["flow_id"]]["sampling_speed"] = sampling_speed
                    flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                    sampled_data.append(prev_report[f"throughput_{alpha}"])
                    sampled_data.append(metric_value)
                    flows[report["flow_id"]]["sampled_data"] = sampled_data

                    sample_count =1
                    if flows[report["flow_id"]]["total_count"] == 0:
                        report[f"throughput_{alpha}_RME"] = 0

                    elif flows[report["flow_id"]]["total_count"] == 1:
                        report[f"throughput_{alpha}_RME"] = RME((sum(sampled_data[-1:])/1),total_data,total_count)
                        # print("RME: ", report["throughput_RME"]," error: ",error," ",sum(sampled_data[-1:])/1," ",total_data[-total_count:])
                        self.DB.write_measurement(prev_report)
                    else:
                        report[f"throughput_{alpha}_RME"] = RME((sum(sampled_data[-2:])/2),total_data,total_count)
                        self.DB.write_measurement(prev_report)
                    
                    self.DB.write_measurement(report)
                    
                
                # print(metric_value, " ",expected_value," error: ",error, ", sampling speed: ",sampling_speed)
                report[f"throughput_{alpha}_total_count"] = 1
                report[f"throughput_{alpha}_sample_count"] = sample_count
                # print(report,"\n")
                self.DB.write_measurement(report)
                if sample_count == 0:
                    flows[report["flow_id"]]["total_count"]+=1
                else:
                    flows[report["flow_id"]]["total_count"] = 0
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
            print(report)
            print(prev_report)
            exit()

def start_throughput_measurements_eval_thread(self,alpha=0.05):
    collect_throughput_measurements_eval_thread = threading.Thread(target=collect_throughput_measurements_eval(self,alpha), name="collect_throughput_measurements_eval")
    collect_throughput_measurements_eval_thread.start()

def collect_throughput_measurements_eval_no_mem(self,alpha = 0.05):
    from queue import Queue
    import datetime
    import numpy as np
    import copy
    flows = {}
    window_size = 10
    data = Queue(maxsize=window_size)
    timestamps = Queue(maxsize=window_size)
    expected_value = 0
    sampling_speed = 0.1
    min_sampling_speed = 10
    max_sampling_speed = 0.1
    error = 0
    last_sample_time = datetime.datetime.now()
    counter = 0
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
        data_list = list(data.queue)
        time_list = list(timestamps.queue)
        # Receive measurements from the P4 switch
        measurements = self.Socket.recv(1024)
        # measurements = measurements.decode()
        measurements = measurements.decode('utf-8')
        measurements = measurements.strip().split("\n")
        # try:
        for report in measurements:
            report = json.loads(report)
            if (report["flow_id"] in flows.keys()):
                data = flows[report["flow_id"]]["data"]
                timestamps = flows[report["flow_id"]]["timestamps"]
                data_list = list(flows[report["flow_id"]]["data"].queue)
                time_list = list(flows[report["flow_id"]]["timestamps"].queue)
                expected_value = flows[report["flow_id"]]["expected_value"]
                sampling_speed = flows[report["flow_id"]]["sampling_speed"]
                min_sampling_speed = flows[report["flow_id"]]["min_sampling_speed"]
                max_sampling_speed = flows[report["flow_id"]]["max_sampling_speed"]
                last_sample_time = flows[report["flow_id"]]["last_sample_time"]
                sample_count = flows[report["flow_id"]]["sample_count"]
                total_count = flows[report["flow_id"]]["total_count"]
                sampled_data = flows[report["flow_id"]]["sampled_data"]                           
                total_data = flows[report["flow_id"]]["total_data"]
                expected_value_list = flows[report["flow_id"]]["expected_value_list"]

            else:
                flows[report["flow_id"]] = {"data" : Queue(maxsize=window_size),"expected_value" : 0,"sampling_speed":0.1,\
                                            "min_sampling_speed":5,"max_sampling_speed" :0.1,"last_sample_time":datetime.datetime.now()\
                                                ,"timestamps": Queue(maxsize=window_size),\
                                                    "sample_count":0,"total_count":0,"sampled_data":[],"total_data":[],"expected_value_list":[]}
                data = flows[report["flow_id"]]["data"]
                timestamps = flows[report["flow_id"]]["timestamps"]
                data_list = list(flows[report["flow_id"]]["data"].queue)
                expected_value = flows[report["flow_id"]]["expected_value"]
                sampling_speed = flows[report["flow_id"]]["sampling_speed"]
                min_sampling_speed = flows[report["flow_id"]]["min_sampling_speed"]
                max_sampling_speed = flows[report["flow_id"]]["max_sampling_speed"]
                last_sample_time = flows[report["flow_id"]]["last_sample_time"]
                sample_count = flows[report["flow_id"]]["sample_count"]
                total_count = flows[report["flow_id"]]["total_count"]
                sampled_data = flows[report["flow_id"]]["sampled_data"]                           
                total_data = flows[report["flow_id"]]["total_data"]
                expected_value_list = flows[report["flow_id"]]["expected_value_list"]

            report["metric_name"] = f"throughput_no_mem"
            report[f"throughput_no_mem"] = report.pop("throughput")
            report[f"throughput_no_mem"] = float(report[f"throughput_no_mem"])*10
            metric_value = float(report[f"throughput_no_mem"])
            data.put(metric_value)
            total_data.append(metric_value)

            
            flows[report["flow_id"]]["total_data"] = total_data

            if len(total_data) > 1 and metric_value > 0 and metric_value != total_data[len(total_data)-2]:
                error = abs(expected_value/metric_value)
                # print("The error is: ", error, " the expected value is: ", expected_value, " the metric value is: ", metric_value)
            elif len(total_data) > 1 and metric_value == total_data[len(data_list)-2]:
                error = 1

            if data.qsize() == window_size:
                data.get()
                timestamps.get()
            timestamps.put(datetime.datetime.strptime(report["report_time"],"%Y-%m-%dT%H:%M:%S.%f").timestamp())

            flows[report["flow_id"]]["data"] = data
            flows[report["flow_id"]]["timestamps"] = timestamps
            
            if(len(total_data)>0):
                expected_value = metric_value + average_rate_of_change(total_data,time_list)
                
            else:
                expected_value = metric_value
            expected_value_list.append(expected_value)
            flows[report["flow_id"]]["expected_value_list"] = expected_value_list
            if(len(total_data)>10):
                report["throughput_cov"] = np.corrcoef(total_data[-10:], expected_value_list[-10:])[0, 1]
            flows[report["flow_id"]]["expected_value"] = expected_value
                

            if error > (1-alpha) and error < (1+alpha):
                sampling_speed = min(min_sampling_speed,sampling_speed + 1)
                flows[report["flow_id"]]["sampling_speed"] = sampling_speed
                if last_sample_time.timestamp() + min(sampling_speed, min_sampling_speed) < datetime.datetime.now().timestamp():
                    flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                    sampled_data.append(metric_value)
                    flows[report["flow_id"]]["sampled_data"] = sampled_data
                    
                    sample_count =1
                    report[f"throughput_no_mem_RME"] = RME(metric_value,total_data,total_count)
                    # if report["throughput_RME"] > 0.1:
                    # flows[report["flow_id"]]["total_count"] = 0
                    # print(report)
                    report[f"throughput_no_mem_sample_count"] = sample_count
                    self.DB.write_measurement(report)


            elif error < (1-alpha):
                sampling_speed = max(max_sampling_speed,error * sampling_speed)
                flows[report["flow_id"]]["sampling_speed"] = sampling_speed
                flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                sample_count =1
                sampled_data.append(metric_value)
                flows[report["flow_id"]]["sampled_data"] = sampled_data

                if flows[report["flow_id"]]["total_count"] == 0:
                    report[f"throughput_no_mem_RME"] = 0

                else:
                    report[f"throughput_no_mem_RME"] = RME(sampled_data[-1],total_data,total_count)
                report[f"throughput_no_mem_sample_count"] = sample_count
                self.DB.write_measurement(report)


            elif error > (1+alpha):
                sampling_speed = max(max_sampling_speed,1/error * sampling_speed)
                flows[report["flow_id"]]["sampling_speed"] = sampling_speed
                flows[report["flow_id"]]["last_sample_time"] = datetime.datetime.now()
                sampled_data.append(metric_value)
                flows[report["flow_id"]]["sampled_data"] = sampled_data

                sample_count =1
                if flows[report["flow_id"]]["total_count"] == 0:
                    report[f"throughput_no_mem_RME"] = 0

                else:
                    report[f"throughput_no_mem_RME"] = RME(sampled_data[-1],total_data,total_count)   
                report[f"throughput_no_mem_sample_count"] = sample_count                 
                self.DB.write_measurement(report)
                    
            # report[f"throughput_no_mem_total_count"] = 1
            # report[f"throughput_no_mem_sample_count"] = sample_count
            # # print(report,"\n")
            # self.DB.write_measurement(report)
            if sample_count == 0:
                flows[report["flow_id"]]["total_count"]+=1
            else:
                flows[report["flow_id"]]["total_count"] = 0
            # print(flows[report["flow_id"]]["total_count"])
        
        # except json.decoder.JSONDecodeError:
        #     counter +=1
        #     pass
        #     if measurements == ['']:
        #         break
        #     print(counter)
        # except Exception as e:
        #     exception_name = type(e).__name__
        #     print("\nAn error occurred while getting data from the control plane:", str(e),"\n")
        #     print(report)
        #     exit()

def start_throughput_measurements_eval_no_mem_thread(self,alpha=0.05):
    collect_throughput_measurements_eval_no_mem_thread = threading.Thread(target=collect_throughput_measurements_eval_no_mem(self,alpha), name="collect_throughput_measurements_eval_no_mem")
    collect_throughput_measurements_eval_no_mem_thread.start()