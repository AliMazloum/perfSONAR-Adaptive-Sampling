import json
import time
from datetime import datetime,timezone
import threading
import socket
import atexit


p4 = bfrt.Per_Flow_Collector.pipe


long_flows = {}
queue_delay_alerted_flows=[]
rtt_alerted_flows=[]
throughput_alerted_flows=[]
retr_alerted_flows=[]
N = 0
sketches_reset_lock = 0

with open('/home/Per_Flow_Collector/bfrt_python/configuration.json', 'r') as file:
    global_variables = json.load(file)

P4_start_time = datetime.now(timezone.utc).timestamp()



sock_60003 = socket.socket()         # RTT thread
host = socket.gethostname()    
port = 60003                 
sock_60003.connect((host, port))

# sock_60006 = socket.socket()         # RTT thread ST   
# port = 60006                  
# sock_60006.connect((host, port))

sock_60008 = socket.socket()         # rtt thread LP   
port = 60008                  
sock_60008.connect((host, port))

# sock_60011 = socket.socket()         # throughput alpha 0.025  
# port = 60011                  
# sock_60011.connect((host, port))

# sock_60012 = socket.socket()         # throughput alpha 0.075 
# port = 60012                  
# sock_60012.connect((host, port))

# sock_60013 = socket.socket()         # throughput alpha 0.1  
# port = 60013                  
# sock_60013.connect((host, port))

# sock_60014 = socket.socket()         # throughput alpha 0.15  
# port = 60014                  
# sock_60014.connect((host, port))

# sock_60015 = socket.socket()         # throughput alpha 0.2  
# port = 60015                  
# sock_60015.connect((host, port))

sock_60016 = socket.socket()         # throughput no mem 
port = 60016                  
sock_60016.connect((host, port))

# sock_60008 = socket.socket()         # throughput alpha 0.25  
# port = 60011                  
# sock_60008.connect((host, port))

sock_60010 = socket.socket()         # rtt thread MuST   
port = 60010                 
sock_60010.connect((host, port))

sock_60004 = socket.socket()         # Throughput thread   
port = 60004                  
sock_60004.connect((host, port))

# sock_60005 = socket.socket()         # Throughput thread ST   
# port = 60005                  
# sock_60005.connect((host, port))

sock_60007 = socket.socket()         # Throughput thread LP   
port = 60007                  
sock_60007.connect((host, port))

sock_60009 = socket.socket()         # Throughput thread MuST   
port = 60009                  
sock_60009.connect((host, port))



def send_data(metric_name,metric_value, socket, metric_samples_per_second=250,to_sleep=True,time_deduction_offset=0,source_ip=None,flow_id=None,dst_ip=None,limited_by="Network"):
    import time,ipaddress
    from datetime import datetime,timezone
    global global_variables

    metric_value = "{:.4f}".format(metric_value)
    stats = {"metric_name": metric_name, metric_name:metric_value}
    stats["per_flow_measurement"] ={"type": metric_name}
    stats["report_time"] = datetime.utcfromtimestamp(datetime.now(timezone.utc).timestamp()).strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    if (source_ip != None):
        stats["source_ip"] = source_ip
    if (dst_ip != None):
        stats["dst_ip"] = dst_ip
    if (flow_id != None):
        stats["flow_id"] = flow_id
    stats = json.dumps(stats)
    stats +="\n"
    socket.send(stats.encode())
    if(to_sleep):
        if(global_variables[metric_name]["alert"]["enabled"] & (float(metric_value) > global_variables[metric_name]["alert"]["threshold"])):
            time.sleep(1/global_variables[metric_name]["alert"]["alert_samples_per_second"] - time_deduction_offset)
        else:
            time.sleep(1/global_variables[metric_name]["samples_per_second"] - time_deduction_offset)

def new_long_flow(dev_id, pipe_id, direction, parser_id, session, msg):
    import ipaddress
    from datetime import datetime,timezone
    import time
    global p4
    global long_flows
    global P4_start_time
    global N
    for digest in msg:
        flow_id = digest['flow_id']
        rev_flow_id = digest['rev_flow_id']
        src_IP = str(ipaddress.ip_address(digest['flow_source_IP']))
        dst_IP = str(ipaddress.ip_address(digest['flow_destination_IP']))
        flow_start_time = float(p4.Ingress.flow_start_end_time.get\
                     (REGISTER_INDEX=flow_id, from_hw=True, print_ents=False).data[b'Ingress.flow_start_end_time.flow_start_time'][1])/10**6 + P4_start_time
        long_flows[digest["flow_id"]] = {'rev_flow_id':rev_flow_id,'src_IP':src_IP,'dst_IP':dst_IP,"flow_start_time":flow_start_time \
                                ,"per_flow_measurement": {'type':"long_flow"},'flow_id':digest["flow_id"],"number_of_bytes":0, \
                                    "old_retr":0,"bloating_number":0,"total_packets":0,"counter":0,"prev_throughput":0}       
        N+=1
        print("New flow: ", flow_id)
        p4.Ingress.counted_flow.add_with_meter(flow_id=digest['flow_id'], ENTRY_TTL = 500)
    return 0

def long_flow_timeout(dev_id, pipe_id, direction, parser_id, entry):
    import json
    from datetime import datetime,timezone
    global p4
    global long_flows
    global P4_start_time
    global N
    try:

        flow_id = entry.key[b'meta.flow_id']
        
        number_of_bytes = float(p4.Ingress.Sample_length.get\
                             (REGISTER_INDEX=flow_id, from_hw=True, print_ents=False).data[b'Ingress.Sample_length.f1'][1])
        end_time = float(p4.Ingress.flow_start_end_time.get\
                        (REGISTER_INDEX=flow_id, from_hw=True, print_ents=False).data[b'Ingress.flow_start_end_time.flow_end_time'][1])/10**6 + P4_start_time
        duration = end_time - long_flows[flow_id]['flow_start_time']
        p4.Ingress.flow_start_end_time.mod(REGISTER_INDEX=flow_id, flow_start_time=0)
        p4.Ingress.flow_start_end_time.mod(REGISTER_INDEX=flow_id, flow_end_time=0)
        p4.Egress.total_packets.mod(REGISTER_INDEX=flow_id, f1=0)
        
        long_flows[flow_id]['flow_end_time'] = end_time
        long_flows[flow_id]['duration'] = duration
        long_flows[flow_id]['number_of_bytes'] = number_of_bytes
        long_flows[flow_id]['bitrate'] = (long_flows[flow_id]['number_of_bytes'])*8/long_flows[flow_id]['duration']
        report =long_flows[flow_id]
        report["report_time"] = datetime.utcfromtimestamp(datetime.now(timezone.utc).timestamp()).strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        report = json.dumps(report)
        report += "\n"
        del long_flows[flow_id]
        N-=1
    except Exception as e:
            print(e)

def reset_sketches():
    global p4
    import time
    global long_flows
    global sketches_reset_lock
    
    while (True):
        time.sleep(4)
        if(sketches_reset_lock):
            p4.Ingress.sketch0.clear()
            p4.Ingress.sketch1.clear()
            p4.Ingress.sketch2.clear()

            p4.Ingress.reg_table_1.clear() 
        else:
            time.sleep(1)
            sketches_reset_lock = 1

def queue_delay_thread():

    import time

    global send_data
    global p4
    global long_flows
    global queue_delay_alerted_flows
 
    metric_name = "queue_occupancy"

    while (1):
        try:
            for flow_id in long_flows.copy():
                if flow_id not in queue_delay_alerted_flows:     
                    queue_delay = p4.Egress.queue_delays.get(REGISTER_INDEX=flow_id, from_hw=True, print_ents=False).data[b'Egress.queue_delays.f1'][1]
                    queue_delay = (queue_delay) / (50000000)
                    metric_value = queue_delay
                    send_data(metric_name,metric_value,to_sleep=False,flow_id=flow_id,dst_ip=long_flows[flow_id]["dst_IP"])
                    if(global_variables[metric_name]["alert"]["enabled"] & (float(metric_value) > global_variables[metric_name]["alert"]["threshold"])):
                            queue_delay_alerted_flows.append(flow_id)
            # time.sleep(1/global_variables[metric_name]["samples_per_second"])
            time.sleep(0.1)
        except KeyError:
            pass
        except Exception as e:
            print("An error occurred in queue_delay_thread :", str(e))
            break

    return 0

def rtt_thread():
    import time

    global send_data
    global p4
    global long_flows
    global rtt_alerted_flows
    global sock_60003 
    # global sock_60006
    global sock_60008
    global sock_60010
    metric_name = "rtt"

    while (1):
        try:
            for flow_id in long_flows.copy():
                # print("rtt_thread: ",flow_id)
                if flow_id not in rtt_alerted_flows:     
                    rtt = float(p4.Ingress.rtt.get\
                                            (REGISTER_INDEX=long_flows[flow_id]["rev_flow_id"],from_hw=True, print_ents=False).data[b'Ingress.rtt.f1'][1])
                    metric_value = rtt/1e9
                    send_data(metric_name,metric_value,flow_id=flow_id,socket=sock_60003,to_sleep=False)
                    # send_data(metric_name,metric_value,flow_id=flow_id,dst_ip=long_flows[flow_id]["dst_IP"],socket=sock_60006,to_sleep=False)
                    send_data(metric_name,metric_value,flow_id=flow_id,socket=sock_60008,to_sleep=False)
                    send_data(metric_name,metric_value,flow_id=flow_id,socket=sock_60010,to_sleep=False)
            time.sleep(0.1)
        except KeyError:
            pass
        except Exception as e:
            print("Error occured in the rtt_thread: ",e)
            break

    return 0

def throughput_thread():

    import time
    from datetime import datetime
    global send_data
    global p4
    global long_flows
    global global_variables
    global throughput_alerted_flows
    global sock_60004
    # global sock_60005
    global sock_60007
    global sock_60009
    # global sock_60011
    # global sock_60012
    # global sock_60013
    # global sock_60014
    # global sock_60015
    global sock_60016
    # sock_60011
 
    metric_name = "throughput"

    while (1):
        try:
            for flow_id in long_flows.copy():
                if flow_id not in throughput_alerted_flows:     
                    total_bytes = float(p4.Ingress.Sample_length.get\
                                            (REGISTER_INDEX=flow_id,from_hw=True, print_ents=False).data[b'Ingress.Sample_length.f1'][1])
                    new_bytes = total_bytes - long_flows[flow_id]["number_of_bytes"]+ long_flows[flow_id]["bloating_number"]*4294967296
                    if (new_bytes < 0):
                        new_bytes = total_bytes + 4294967296 - long_flows[flow_id]["number_of_bytes"] + long_flows[flow_id]["bloating_number"]*4294967296 
                        long_flows[flow_id]["bloating_number"] += 1
                    metric_value = (new_bytes)*8/10
                    long_flows[flow_id]["number_of_bytes"] += new_bytes
                    send_data(metric_name,metric_value,to_sleep=False,flow_id=flow_id,socket=sock_60004)
                    # send_data(metric_name,metric_value,to_sleep=False,flow_id=flow_id,dst_ip=long_flows[flow_id]["dst_IP"],socket=sock_60005)
                    send_data(metric_name,metric_value,to_sleep=False,flow_id=flow_id,socket=sock_60007)
                    send_data(metric_name,metric_value,to_sleep=False,flow_id=flow_id,socket=sock_60009)
                    # send_data(metric_name,metric_value,to_sleep=False,flow_id=flow_id,socket=sock_60011)
                    # send_data(metric_name,metric_value,to_sleep=False,flow_id=flow_id,socket=sock_60012)
                    # send_data(metric_name,metric_value,to_sleep=False,flow_id=flow_id,socket=sock_60013)
                    # send_data(metric_name,metric_value,to_sleep=False,flow_id=flow_id,socket=sock_60014)
                    # send_data(metric_name,metric_value,to_sleep=False,flow_id=flow_id,socket=sock_60015)
                    send_data(metric_name,metric_value,to_sleep=False,flow_id=flow_id,socket=sock_60016)

                    # last_sample_time = datetime.now()
            # time.sleep(1/global_variables[metric_name]["samples_per_second"])
            time.sleep(1)
        except KeyError:
            pass
        except Exception as e:
            print("Error occured in the throughput_thread: ",e)
            break

    return 0

def retr_thread():

    import time

    global send_data
    global p4
    global long_flows
 
    metric_name = "retr"
 
    while (1):
        try:
            for flow_id in long_flows.copy():     
                retr = float(p4.Ingress.retr.get\
                                        (REGISTER_INDEX=flow_id,from_hw=True, print_ents=False).data[b'Ingress.retr.f1'][1])
                total_packets = float(p4.Egress.total_packets.get\
                                        (REGISTER_INDEX=flow_id,from_hw=True, print_ents=False).data[b'Egress.total_packets.f1'][1])
                if(total_packets == long_flows[flow_id]["total_packets"]):
                    metric_value = 0
                else:
                    metric_value = retr - long_flows[flow_id]["old_retr"]
                    retr_percentage = ((retr - long_flows[flow_id]["old_retr"]) / (total_packets - long_flows[flow_id]["total_packets"]))*100 
                    long_flows[flow_id]["total_packets"] = total_packets
                long_flows[flow_id]["old_retr"] = retr
                send_data(metric_name,metric_value,to_sleep=False,flow_id=flow_id,dst_ip=long_flows[flow_id]["dst_IP"])
                send_data("retr_percentage",retr_percentage,to_sleep=False,flow_id=flow_id,dst_ip=long_flows[flow_id]["dst_IP"])
            time.sleep(1)
        except KeyError:
            pass
        except Exception as e:
            print("Error occured in the retr_thread: ",e)
            break

    return 0

def number_of_flows():

    import time

    global send_data
    global p4
    global N
 
    metric_name = "number_of_flows"

    while (1):
        metric_value = N
        send_data(metric_name,metric_value,to_sleep=False)
        time.sleep(1)

    return 0

def recieve_remote_configuration():
    import socket
    import json
    global global_variables
    import ipaddress
    try:
        listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listening_socket.bind(("10.173.85.43", 11881))
        listening_socket.listen(1)
        while True:
            
            client_socket, address = listening_socket.accept()
            data = client_socket.recv(1024).decode('utf-8')
            data = json.loads(data)
            global_variables = data
            json.dump(data,open('/home/Per_Flow_Collector/bfrt_python/configuration.json',"w"))
            client_socket.close()

    except Exception as e:
        print("An error occurred while binding to local port:", str(e))
    
    def cleanup(mysocket):
    # Perform cleanup actions here
        mysocket.close()

    # Register the cleanup function to be called on program exit
    atexit.register(cleanup(listening_socket)) 
 
try:
    p4.Ingress.counted_flow.idle_table_set_notify(enable=True, callback=long_flow_timeout, interval=200, min_ttl=400, max_ttl=1000)
    p4.IngressDeparser.new_long_flow_digest.callback_register(new_long_flow)
except:
    print('Error registering callback')

periodic_reset = threading.Thread(target=reset_sketches, name="reset_sketches")
recieve_remote_configuration = threading.Thread(target=recieve_remote_configuration, name="recieve_remote_configuration")

# th_queue_delay_thread = threading.Thread(target=queue_delay_thread, name="th_queue_delay_thread")

th_rtt_thread = threading.Thread(target=rtt_thread, name="th_rtt_thread")

th_throughput_thread = threading.Thread(target=throughput_thread , name="th_throughput_thread")

th_retr_thread = threading.Thread(target=retr_thread, name="th_retr_thread")
# th_number_of_flows = threading.Thread(target=number_of_flows, name="number_of_flows")


periodic_reset.start()
recieve_remote_configuration.start()

# th_queue_delay_thread.start()

th_rtt_thread.start()

th_throughput_thread.start()


# th_retr_thread.start()
# th_number_of_flows.start()

i=0
while(1):
   
    if(N==0):
        i+=1
    else:
        i=0

    if(i==3): #10):
        sketches_reset_lock = 0
        try:
            i=0
            long_flows.clear()
        
            p4.Ingress.calc_flow_id.clear() 
            p4.Ingress.calc_rev_flow_id.clear()    
            p4.Ingress.copy32_1.clear()    
            p4.Ingress.copy32_2.clear()    
            p4.Ingress.crc16_1.clear()    
            p4.Ingress.crc16_2.clear()    
            p4.Ingress.crc32_1.clear()    
            p4.Ingress.crc32_2.clear()     
            
            long_flows.clear()
            p4.Ingress.sketch0.clear()
            p4.Ingress.sketch1.clear()
            p4.Ingress.sketch2.clear()

        except Exception as e:
            print(e)
    
    time.sleep(1)