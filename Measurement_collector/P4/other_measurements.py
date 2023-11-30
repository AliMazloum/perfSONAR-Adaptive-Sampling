import json
import threading

def collect_measurements(self):
        counter = 0
        while True:
            # Receive measurements from the P4 switch
            measurements = self.Socket.recv(1024)
            # measurements = measurements.decode()
            measurements = measurements.decode('utf-8')
            measurements = measurements.strip().split("\n")

            try:
                for report in measurements:
                    report = json.loads(report)
                    self.DB.write_measurement(report)
            except json.decoder.JSONDecodeError:
                counter +=1
                pass
                if measurements == ['']:
                    break
                print(counter)
            except Exception as e:
                exception_name = type(e).__name__
                print("\nAn error occurred while getting data from the control plane:", str(exception_name),"\n")
                # print(measurements)JSONDecodeError
                exit()

def start_measurements_thread(self):
    collect_measurements_thread = threading.Thread(target=collect_measurements(self), name="collect_measurements")
    collect_measurements_thread.start()
