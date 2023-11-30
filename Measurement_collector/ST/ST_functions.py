def collect_rtt_ST_measurements(self):   
        from queue import Queue
        import datetime
        import numpy as np
        import copy
        flows = {}
        alpha = 0.8
        error = 0
        last_sample_time = datetime.datetime.now()
        counter = 0

        def RME(sampled_data,total_data,sample_count):
            RME = abs(sampled_data - (sum(total_data[-sample_count:])/len(total_data[-sample_count:])))/(sum(total_data[-sample_count:])/len(total_data[-sample_count:]))
            return RME

        while True:
            measurements = self.Socket.recv(1024)
            measurements = measurements.decode('utf-8')
            measurements = measurements.strip().split("\n")
            try:
                for report in measurements:
                    report = json.loads(report)
                    if (report["flow_id"] in flows.keys()):
                        last_sample_time_500ms = flows[report["flow_id"]]["last_sample_time_500ms"]
                        last_sample_time_1s = flows[report["flow_id"]]["last_sample_time_1s"]
                        last_sample_time_2s = flows[report["flow_id"]]["last_sample_time_2s"]
                        sample_count = flows[report["flow_id"]]["sample_count"]
                        total_count = flows[report["flow_id"]]["total_count"]                         
                        total_data = flows[report["flow_id"]]["total_data"]
                        
                    else:
                        flows[report["flow_id"]] = {"last_sample_time_1s":datetime.datetime.now(),\
                            "last_sample_time_500ms":datetime.datetime.now(),"last_sample_time_2s":datetime.datetime.now(),\
                            "sample_count":0,"total_count":0,"total_data":[]}
                        last_sample_time_500ms = flows[report["flow_id"]]["last_sample_time_500ms"]
                        last_sample_time_1s = flows[report["flow_id"]]["last_sample_time_1s"]
                        last_sample_time_2s = flows[report["flow_id"]]["last_sample_time_2s"]
                        sample_count = flows[report["flow_id"]]["sample_count"]
                        total_count = flows[report["flow_id"]]["total_count"]                        
                        total_data = flows[report["flow_id"]]["total_data"]
                    
                    metric_value = float(report["rtt"])
                    total_data.append(metric_value)
                    
                    if datetime.datetime.now().timestamp() > last_sample_time_500ms.timestamp() + 0.5:
                        flows[report["flow_id"]]["last_sample_time_500ms"] = datetime.datetime.now()
                        report["metric_name"] = "rtt_500ms"
                        report["rtt_500ms"] = report.pop("rtt")
                        report["rtt_500ms_sample_count"] = 1
                        report["rtt_500ms_RME"] = RME(metric_value, total_data,5)
                        self.DB.write_measurement(report)
                    
                    if datetime.datetime.now().timestamp() > last_sample_time_1s.timestamp() + 1:
                        flows[report["flow_id"]]["last_sample_time_1s"] = datetime.datetime.now()
                        report["metric_name"] = "rtt_1s"
                        if "rtt" in report.keys():
                            report["rtt_1s"] = report.pop("rtt")
                        else:
                            report["rtt_1s"] = report.pop("rtt_500ms")
                            report["rtt_1s_sample_count"] = report.pop("rtt_500ms_sample_count")
                            report["rtt_1s_RME"] = report.pop("rtt_500ms_RME")
                        report["rtt_1s_sample_count"] = 1
                        report["rtt_1s_RME"] = RME(metric_value, total_data,10)
                        self.DB.write_measurement(report)
                        
                    # if datetime.datetime.now().timestamp() > last_sample_time_2s.timestamp() + 2:
                    #     flows[report["flow_id"]]["last_sample_time_2s"] = datetime.datetime.now()
                    #     report["metric_name"] = "rtt_2s"
                    #     if "rtt" in report.keys():
                    #         report["rtt_2s"] = report.pop("rtt")
                    #     if "rtt_1s" in report.keys():
                    #         report["rtt_2s"] = report.pop("rtt_1s")

                    #     report["rtt_2s_sample_count"] = 1
                    #     report["rtt_2s_RME"] = RME(metric_value, total_data,20)
                    #     self.DB.write_measurement(report)                        
                    
                    
                    flows[report["flow_id"]]["total_data"] = total_data
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

def collect_throughput_ST_measurements(self):   
        from queue import Queue
        import datetime
        import numpy as np
        import copy
        flows = {}
        alpha = 0.8
        error = 0
        last_sample_time = datetime.datetime.now()
        counter = 0

        def RME(sampled_data,total_data,sample_count):
            if (sum(total_data[-sample_count:])/len(total_data[-sample_count:]))>0:
                RME = abs(sampled_data - (sum(total_data[-sample_count:])/len(total_data[-sample_count:])))/(sum(total_data[-sample_count:])/len(total_data[-sample_count:]))
            return RME

        while True:
            measurements = self.Socket.recv(1024)
            measurements = measurements.decode('utf-8')
            measurements = measurements.strip().split("\n")
            try:
                for report in measurements:
                    report = json.loads(report)
                    if (report["flow_id"] in flows.keys()):
                        last_sample_time_500ms = flows[report["flow_id"]]["last_sample_time_500ms"]
                        last_sample_time_1s = flows[report["flow_id"]]["last_sample_time_1s"]
                        last_sample_time_2s = flows[report["flow_id"]]["last_sample_time_2s"]
                        sample_count = flows[report["flow_id"]]["sample_count"]
                        total_count = flows[report["flow_id"]]["total_count"]                         
                        total_data = flows[report["flow_id"]]["total_data"]
                        
                    else:
                        flows[report["flow_id"]] = {"last_sample_time_1s":datetime.datetime.now(),\
                            "last_sample_time_500ms":datetime.datetime.now(),"last_sample_time_2s":datetime.datetime.now(),\
                            "sample_count":0,"total_count":0,"total_data":[]}
                        last_sample_time_500ms = flows[report["flow_id"]]["last_sample_time_500ms"]
                        last_sample_time_1s = flows[report["flow_id"]]["last_sample_time_1s"]
                        last_sample_time_2s = flows[report["flow_id"]]["last_sample_time_2s"]
                        sample_count = flows[report["flow_id"]]["sample_count"]
                        total_count = flows[report["flow_id"]]["total_count"]                        
                        total_data = flows[report["flow_id"]]["total_data"]
                    
                        
                    report["throughput"] = float(report["throughput"])*10
                    metric_value = float(report["throughput"])
                    total_data.append(metric_value)
                    
                    if datetime.datetime.now().timestamp() > last_sample_time_500ms.timestamp() + 0.5:
                        flows[report["flow_id"]]["last_sample_time_500ms"] = datetime.datetime.now()
                        report["metric_name"] = "throughput_500ms"
                        report["throughput_500ms"] = report.pop("throughput")
                        report["throughput_500ms_sample_count"] = 1
                        report["throughput_500ms_RME"] = RME(metric_value, total_data,5)
                        self.DB.write_measurement(report)
                    
                    if datetime.datetime.now().timestamp() > last_sample_time_1s.timestamp() + 1:
                        flows[report["flow_id"]]["last_sample_time_1s"] = datetime.datetime.now()
                        report["metric_name"] = "throughput_1s"
                        if "throughput" in report.keys():
                            report["throughput_1s"] = report.pop("throughput")
                        else:
                            report["throughput_1s"] = report.pop("throughput_500ms")
                        report["throughput_1s_sample_count"] = 1
                        report["throughput_1s_RME"] = RME(metric_value, total_data,10)
                        self.DB.write_measurement(report)
                        
                    # if datetime.datetime.now().timestamp() > last_sample_time_2s.timestamp() + 2:
                    #     flows[report["flow_id"]]["last_sample_time_2s"] = datetime.datetime.now()
                    #     report["metric_name"] = "throughput_2s"
                    #     if "throughput" in report.keys():
                    #         report["throughput_2s"] = report.pop("throughput")
                    #     elif "throughput_1s" in report.keys():
                    #         report["throughput_2s"] = report.pop("throughput_1s")

                    #     report["throughput_2s_sample_count"] = 1
                    #     report["throughput_2s_RME"] = RME(metric_value, total_data,20)
                    #     self.DB.write_measurement(report)                        
                    
                    
                    flows[report["flow_id"]]["total_data"] = total_data
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

