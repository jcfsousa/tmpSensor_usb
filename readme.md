# Templab1: TEMPer1F USB Temperature Sensor Reader

## Brief Description

- This script was developed for use in the Laboratory I classes of the Department of Physics at the University of Coimbra within the scope of the Laboratory Work 'Determination of the ice fusion enthalpy'.
- Python script to read from the TEMPer1F USB temperature sensor at 1Hz and log the temperature data.
- Users can plot the acquired data directly (the script autosaves plots) or use the `.csv` log file for future data analysis.


## Prerequisites

- This script only works on windows since we are using the pywinusb library
- Python 3.10 or later
- Libraries: `pywinusb`, `matplotlib`


## Installation 

### Windows:

Run the following command in the project root directory:

```
py -m pip install -e .
```

## How to run 

- Navigate to the root directory of the project, i.e., /PATH_TO_DIRECTORY/tmplab1/.
- **On Windows**: Either double-click the tmp.py file or open a terminal in that directory and run:

```
py tmp.py
```


## Commands
- **start**: Starts data acquisition with a 1Hz frequency. Data is stored in RAM and saved to disk only after the stop command.
- **stop**: Stops data acquisition and saves the data to /currentPath/{group ID}/temperature_log_{HOUR-MIN-SEC}.csv. The file is a .csv, with the first column being the timestamp and the second column the temperature (°C).
- **plot**: Use only after the stop command. This command plots all data acquired since the script started. Multiple acquisitions can be performed without closing the program, and the user can still call the plot command.
- **help**: Shows command descriptions.
- **exit**: Closes the program and saves the last data acquisition taken on /currentPath/{group ID}/temperature_log_{HOUR-MIN-SEC}.csv.


## Acknowledgments

- All the props to Tom Churchill, the scrip was heavely based on his code: https://github.com/tom-churchill/temper-windows.git

