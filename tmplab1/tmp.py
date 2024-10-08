import time
import pywinusb.hid as hid
import matplotlib.pyplot as plt
import threading
import csv
from datetime import datetime
import os
from matplotlib.ticker import MaxNLocator
from datetime import datetime, timedelta
import random


class _TemperWindows:
    def __init__(self):
        self.read_data = None
        self.read_data_received = False

    def raw_data_handler(self, data):
        self.read_data = data
        self.read_data_received = True

    @staticmethod
    def convert_data_to_temperature(data, device_name):
        device_name_lowerCase = device_name.lower()
        #print(device_name)
        #print(device_name_lowerCase)

        if device_name_lowerCase == "temper1f":
            #print(data)
            return float(data[3] * 256 + data[4]) / 100
        
        elif device_name_lowerCase == "temper1f_v1.3":
            #print(data)
            return float(data[3] * 256 + data[6]) / 256  
        
        elif device_name_lowerCase == "temper2":
            #print(data)
            return float(data[3] * 256 + data[4]) / 100
        
        else:
            return 1


    def get_temperature(self, device_name, _vendor_id, _product_id):
        self.read_data = None
        self.read_data_received = False

        devices = hid.HidDeviceFilter(vendor_id=_vendor_id,product_id=_product_id).get_devices()

        if not device_name.startswith("TEMP"):
            return None
        
        device = devices[0]

        try:
            device.open()
            device.set_raw_data_handler(self.raw_data_handler)
            write_data = [0x00, 0x01, 0x80, 0x33, 0x01, 0x00, 0x00, 0x00, 0x00]
            self.read_data_received = False
            device.send_output_report(write_data)

            sleep_amount = 0.1 
            while not self.read_data_received:
                time.sleep(sleep_amount)
                sleep_amount = 0.5  # 0.05 to avoid causing high cpu
                device.set_raw_data_handler(self.raw_data_handler) #need to call here because we catch the last 8bytes - for Temper2 the external tmp comes on the 2ns 8byte transmission

            return self.convert_data_to_temperature(self.read_data, device_name)
        finally:
            device.close()

_temper_windows = None

# Global variables for logging and acquisition
temperature_data = []
list_time_end_aq = []
list_time_begin_aq = []
last_aq_tmp = []
acquisition_thread = None
logging = False
user_ID = ""
directory_name = ""
log_file_path = ""


def get_usb_device_info(device):
    '''Get basic information for a USB device using pywinusb'''
    info = dict()
    vendorid = device.vendor_id
    productid = device.product_id
    nameFull = device.product_name
    nameLower = nameFull.lower()

    if nameLower.startswith('temp'):
        if not vendorid or not productid:
            return None
        info['vendorid'] = vendorid
        info['productid'] = productid
        info['manufacturer'] = device.vendor_name
        info['product'] = device.product_name
        info['busnum'] = "N/A"  # Not available with pywinusb
        info['devnum'] = device.device_path
        return info
    else:
        return None

def get_tmp_info():
    device_dict = dict()
    devices = hid.HidDeviceFilter().get_devices() # get all usb devices connected to PC
    for device in devices:
        device_info = get_usb_device_info(device)
        if device_info is not None:
            device_info['port'] = 'N/A'
            device_dict[device.device_path] = device_info
    #print(device_dict)
    return device_dict

def get_temperature(device_name, vendor_id, product_id):
    """Gets the temperature from a Temper USB thermometer."""
    global _temper_windows  
    if _temper_windows is None:
        _temper_windows = _TemperWindows()
    return _temper_windows.get_temperature(device_name, vendor_id, product_id)


def acquire_temperature(frequency, duration):
    """Acquires temperature at a specified frequency for a certain duration."""
    global logging, temperature_data, list_time_end_aq, list_time_begin_aq, last_aq_tmp
    period = 1/frequency

    device_info = get_tmp_info()

    if len(device_info) == 0:
        print("\n   [ERROR] No TEMP sensor found. Please plug-in the device and restart program.")
        os._exit(1)
        return
    else:
        for path, device in device_info.items():
            if device['product'].startswith("TEMP"):
                device_name = device['product']
                vendor_id = device['vendorid']
                product_id = device['productid']
                break  #just allow 1x temp sensor

    print(f"\n    Temperature Sensor: {device_name}")

    time.sleep(1)
    initial_time = datetime.now().strftime("%H:%M:%S")
    list_time_begin_aq.append(initial_time)
    while logging: #and (time.time() - start_time) <= duration
        temperature = get_temperature(device_name, vendor_id, product_id)
        if temperature is not None:
            timestamp = datetime.now().strftime("%H:%M:%S")
            temperature_data.append((timestamp, temperature))
            print(f"    Timestamp: {timestamp}, Temperature: {temperature:.2f} °C")
        else:
            print("No TEMP sensor found. Please plug-in the device.")
            os._exit(1)
            return None
        time.sleep(period)
    last_aq_tmp.append(temperature)
    list_time_end_aq.append(timestamp)
    save_to_log_file()


def start_acquisition(frequency):
    """Starts the temperature acquisition in a separate thread."""
    global logging, acquisition_thread, temperature_data
    #temperature_data = []  # Reset data
    logging = True
    duration = 0
    acquisition_thread = threading.Thread(target=acquire_temperature, args=(frequency, duration))
    acquisition_thread.start()

def stop_acquisition():
    """Stops the temperature acquisition."""
    global logging
    logging = False
    if acquisition_thread is not None:
        acquisition_thread.join()
    save_to_log_file()

def save_to_log_file():
    """Saves the logged temperature data to a CSV file."""
   
    '''
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)  # Create the directory if it doesn't exist
        #print(f"File '{directory_name}' created on current directory.")

    # Define the path for the log file
    log_file_path = os.path.join(directory_name, f'temperature_log_{datetime.now().strftime("%Hh-%Mmin-%Ss")}.csv')
    '''
    #print(f"log_file_path {log_file_path}")

    with open(log_file_path, 'w', newline='') as csvfile:
        fieldnames = ['Timestamp', 'Temperature (°C)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for timestamp, temperature in temperature_data:
            writer.writerow({'Timestamp': timestamp, 'Temperature (°C)': temperature})
    #print(f"Data saved to {log_file_path}")


def plot_data():
    """Plots the acquired temperature data."""
    timestamps, temperatures = zip(*temperature_data)
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, temperatures, marker='o', linestyle='-', color='b')

    ax = plt.gca()  
    ax.xaxis.set_major_locator(MaxNLocator(nbins=10)) 

    y_min = min(temperatures) - 0.1*(abs(max(temperatures) - min(temperatures)))
    y_max = max(temperatures) + 0.1*(abs(max(temperatures) - min(temperatures)))

    plt.ylim(y_min, y_max)
    plt.xticks(rotation=45)
    plt.xlabel('Timestamp')
    plt.ylabel('Temperature (°C)')
    plt.title('Temperature Acquisition')
    plt.tight_layout()
    plt.grid()
    
    for i in range(len(list_time_end_aq)-1):
        y_pos_random = float(round(random.uniform(0.15, 0.85), 2))
        plt.axvline(x = list_time_end_aq[i], color = 'r')
        plt.text(list_time_end_aq[i], y_min + y_pos_random * (abs(max(temperatures) - min(temperatures))), f'End: {list_time_end_aq[i]}', verticalalignment='bottom', color='r' )
        plt.text(list_time_end_aq[i], y_min + (y_pos_random-0.1) * (abs(max(temperatures) - min(temperatures))), f'New Start: {list_time_begin_aq[i + 1]}', verticalalignment='bottom', color='r' )
        i += 1
    #print(list_time_end_aq[len(list_time_end_aq)-1])
    plot_file_path = os.path.join(directory_name, f'temperature_log_{datetime.now().strftime("%Hh-%Mmin-%Ss")}.png')
    plt.savefig(plot_file_path)
    plt.show()


def help():
    print("\n Commands:\n      start: starts de data aquisition with 1Hz frequency.\n             It saves the data on RAM, the data is only stored on disk.\n             The data is saved on disk only after the 'stop' command.")
    print(         "\n      stop: stops the data aquisiton and saves the data on \n            /currentPath/{group ID}/temperature_log_{HOUR-MIN-SEC}.csv.\n            The file is a .csv, on the first collumn is the timestamp \n            and second collumn is the temperature (ºC).")
    print(         "\n      plot: only use after the stop command. It uses all the data \n            aquired since the first openning of the script. The user\n            can do multiple data aquisitions (spaced in time & without \n            closing the program) and still call the 'plot' command.")
    print(         "\n      help: shows command description.")
    print(         "\n      exit: closes the program and saves the last data aquisition taken \n            on the /currentPath/{group ID}/temperature_log_{HOUR-MIN-SEC}.csv \n ")
     
def program_intro():
    print("\n******************************  Laboratory I Classes  ******************************")
    print("The script was developed to aid on the temperature data acquisition on the Laboratory")
    print("work: 'Determination of the ice fusion enthalpy'.")
    print("This script uses the TEMPer1F USB temperature sensor to log the temperature over ")
    print("time.The script takes temperature measurements with 1Hz. At start up the user")
    print("should write an unique group identifier (Group ID) where the data will be stored.\nDepartment of Physics - University of Coimbra\nAuthor: José Sousa")
    print("************************************************************************************")
    help()

def main():
    program_intro()
    global directory_name 
    global user_ID
    global log_file_path

    user_ID = input("What's your group ID?\n>> ")

    if user_ID == "exit":
        user = input("Do you really want to exit? (y/n)\n>> ")
        if user == "y":
            return
        else:
            user_ID = input("What's your group ID? (now you can use exit as Group ID) \n>> ")

    current_directory = os.getcwd()
    directory_name = os.path.join(current_directory, "log", user_ID)


    if not os.path.exists(directory_name):
        os.makedirs(directory_name)  # Create the directory if it doesn't exist
        #print(f"File '{directory_name}' created on current directory.")

    log_file_path = os.path.join(directory_name, f'temperature_log_{datetime.now().strftime("%Hh-%Mmin-%Ss")}.csv')

    print(f"        Your data will be saved on: \n          {log_file_path}\n")

    with open(log_file_path, 'w', newline='') as csvfile:
        do_nothing = True

    while True:
        command = input("Enter command (start/stop/plot/help/exit): \n>> ").strip().lower()
        if command == 'start':
            freq = 1
            start_acquisition(freq)
        elif command == 'stop':
            stop_acquisition()
        elif command == 'plot':
            plot_data()
        elif command == 'exit':
            if logging:
                stop_acquisition()
            break
        elif command =='help':
            help()
        else:
            print("Invalid command. Please enter 'start', 'stop', 'plot', 'help' or 'exit'. ")

if __name__ == '__main__':
    main()