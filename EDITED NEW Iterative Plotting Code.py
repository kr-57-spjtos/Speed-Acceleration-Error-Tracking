# -*- coding: utf-8 -*-
"""
Created on Mon Apr  7 16:29:16 2025

@author: jalom
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import re

# -----------------------------
# Part 1: Process each CSV file
# -----------------------------

# Create output directory for plots
output_dir_L = ".\\Plots_L" # made separate output dirs for each of LCR
output_dir_C = ".\\Plots_C"
output_dir_R = ".\\Plots_R"
os.makedirs(output_dir_L, exist_ok=True)
os.makedirs(output_dir_C, exist_ok=True)
os.makedirs(output_dir_R, exist_ok=True)
# make path string for ease of use
csvpath = ".\\Video_Analysis_Results\\csv" # make path to csv folder
vidpath = ".\\Video_Analysis_Results"  # make path to Video__Analysis__Results
testpath = "/Volumes/USB_DISK/TEST_CODE" # make path for test code 

# Process each CSV file in the current directory that ends with "_speed_data.csv"
# csv_files = [file for file in os.listdir(csvpath) if file.endswith("_speed_data.csv")] # main file group 
csv_files = [file for file in os.listdir(csvpath) if file.endswith("_speed_data.csv") and not file.startswith("._")] # test file group edited 
# Because the files were being double counted.
'''
for file in csv_files:
        print(file) # Somehow it keeps trying to run the code on two sets of files, so I edited csv_files

for file in csv_files:
    file_path = os.path.join(testpath, file) # set up filepath 
    # Read CSV file
    df = pd.read_csv(file, encoding='utf-8')
    print(file)
    print(df.columns) 
note: this was some test code I copy-pasted from the main file code to print the filenames before running the main code on the files
'''

for file in csv_files:
    try:
        file_path = os.path.join(csvpath, file) # set up filepath 
        # Read CSV file
        print(file)
        df = pd.read_csv(file_path, encoding='utf-8')

        # Extract setpoint from the filename (Assume format: *_F<setpoint>_*)
        match = re.search(r'F(\d+)', file_path)
        if match:
            setpoint = float(match.group(1))
        else:
            setpoint = None
            print(f"Warning: No setpoint found for {file_path}")

        # Add the setpoint column
        df["Setpoint"] = setpoint
        #speed_min = df["Speed_mm_per_min"].to_list()
        # Drop rows with missing or NaN values in speed or timestamp
        # df = df.dropna(how='any', subset=["Speed_mm_per_min", Timestamp_sec"])
        #print(df["Speed_mm_per_min"])
        # df = df.dropna(subset=["Speed_mm_per_min"])
        # print(df[Speed_mm_per_min"])
        # df = df.dropna(subset=df.columns[[1,3]], how='any')
        #i think it's having trouble getting the column name out of the csv but I'm not sure why or what to do about it. 
        #i should have run this code enough times (>0) to kill the NaN rows, right? (not on the main code though...)
        
        # Ensure numeric values for speed and timestamp

        df["Speed_mm_per_min"] = pd.to_numeric(df["Speed_mm_per_min"], errors='coerce')
        df["Timestamp_sec"] = pd.to_numeric(df["Timestamp_sec"], errors='coerce')
        #df = df.dropna(subset=["Speed_mm_per_min", "Timestamp_sec"]) 
        # Calculate relative error and add it as a new column
        df["Relative_Error"] = abs(df["Setpoint"] - df["Speed_mm_per_min"]) / df["Setpoint"]

        # Calculate average and standard deviation of relative error for this trial
        avg_error = df["Relative_Error"].mean()
        std_error = df["Relative_Error"].std()

        # Add average and standard deviation error to the dataframe (for record)
        df["Average_Error"] = avg_error
        df["Std_Dev_Error"] = std_error

        # Calculate average and standard deviation of Speed for this trial
        avg_speed = df["Speed_mm_per_min"].mean()
        std_speed = df["Speed_mm_per_min"].std()

        # Plot Speed vs Timestamp with Setpoint, average speed and std deviation (green band)
        plt.figure(figsize=(10, 6))
        plt.plot(df["Timestamp_sec"], df["Speed_mm_per_min"], marker='o', label="Speed (mm/min)")
        plt.plot(df["Timestamp_sec"], [setpoint] * len(df), color='red', linestyle='--', label="Setpoint")
        plt.axhline(avg_speed, color='blue', linestyle='--', label=f"Avg Speed: {avg_speed:.2f}")
        plt.fill_between(df["Timestamp_sec"],
                         avg_speed - std_speed,
                         avg_speed + std_speed,
                         color='green', alpha=0.3, label=f"Std: {std_speed:.2f}")
        plt.title(f"Speed vs Timestamp: {file}")
        plt.xlabel("Timestamp (sec)")
        plt.ylabel("Speed (mm/min)")
        plt.legend()
        plt.grid(True)
        if "C_" in file :
            speed_plot_filename = os.path.join(output_dir_C, file.replace(".csv", "_speed_vs_timestamp.png")) #sort by location into files
        elif "L_" in file :
            speed_plot_filename = os.path.join(output_dir_L, file.replace(".csv", "_speed_vs_timestamp.png"))
        else :
            speed_plot_filename = os.path.join(output_dir_R, file.replace(".csv", "_speed_vs_timestamp.png"))
        plt.savefig(speed_plot_filename)
        plt.close()

        # Plot Relative Error vs Timestamp with average and std deviation (green band)
        plt.figure(figsize=(10, 6))
        plt.plot(df["Timestamp_sec"], df["Relative_Error"], marker='x', color='purple', label="Relative Error")
        plt.axhline(avg_error, color='orange', linestyle='--', label=f"Avg Rel Error: {avg_error:.2f}")
        plt.fill_between(df["Timestamp_sec"],
                         avg_error - std_error,
                         avg_error + std_error,
                         color='green', alpha=0.3, label=f"Std: {std_error:.2f}")
        plt.title(f"Relative Error vs Timestamp: {file}")
        plt.xlabel("Timestamp (sec)")
        plt.ylabel("Relative Error")
        plt.legend()
        plt.grid(True)
        if "C_" in file :
            error_plot_filename = os.path.join(output_dir_C, file.replace(".csv", "_relative_error.png"))
        elif "L_" in file :
            error_plot_filename = os.path.join(output_dir_L, file.replace(".csv", "_relative_error.png"))
        else :
            error_plot_filename = os.path.join(output_dir_R, file.replace(".csv", "_relative_error.png"))
        plt.savefig(error_plot_filename)
        plt.close()

        # Save the updated DataFrame with added columns back to CSV
        df.to_csv(file_path, index=False)

    except Exception as e:
        print(f"Error processing {file}: {e}") 

print("Individual trial plots and updated CSVs saved.")

#ok moved everything to one directory and finally got stuff to work as a result

# --------------------------------------------------------
# Part 2: Create Master Summary CSV and Summary Plot Figures
# --------------------------------------------------------
# Make the code for creating a summary csv into a function that takes location as a param, then pass in "C_", "L_" and "R_" as locations
# Concatenate data from all CSV files ()




def make_summary_csv(location) :
    all_data = []
    # assign output_dir based on location
    if location == "C_" :
        output_dir = output_dir_C
    elif location == "L_" :
        output_dir = output_dir_L
    else :
        output_dir = output_dir_R
    #get files containing location
    for file in [c for c in csv_files if location in c]: 
        try:
            file_path = os.path.join(csvpath, file) # set up filepath 
            # Read CSV file
            print(file)
            # short_file = file[2:]
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Ensure numeric conversion in case it's needed
            df["Speed_mm_per_min"] = pd.to_numeric(df["Speed_mm_per_min"], errors='coerce')
            # df["Relative_Error"] = pd.to_numeric(df["Relative_Error"], errors='coerce')
            #df["Setpoint"] = pd.to_numeric(df["Setpoint"], errors='coerce') #try commenting this out because we should have run this code already
            all_data.append(df)
        except Exception as e:
            print(f"Error reading {file} for master summary {location}: {e}")
#this part works

    if all_data:
        master_df = pd.concat(all_data, ignore_index=True)
        # Group by Setpoint and compute overall statistics
        summary = master_df.groupby("Setpoint").agg(
            Trial_Count = ("Speed_mm_per_min", "count"),
            Avg_Speed = ("Speed_mm_per_min", "mean"),
            Std_Speed = ("Speed_mm_per_min", "std"),
            Avg_Relative_Error = ("Relative_Error", "mean"),
            Std_Relative_Error = ("Relative_Error", "std")
        ).reset_index()

        # Save master CSV file
        locpath = os.path.join(csvpath, location)
        master_csv_path = os.path.join(locpath, "master_speed_data.csv")
        os.makedirs(locpath, exist_ok=True)
        summary.to_csv(master_csv_path, index=False)  #there is an error thrown here 
        print(f"Master CSV file {location} saved at: {master_csv_path}")

        # Create Summary Plot 1: Setpoint vs Average Speed with error bars
        plt.figure(figsize=(10, 6))
        plt.errorbar(summary["Setpoint"], summary["Avg_Speed"], yerr=summary["Std_Speed"],
                    fmt='o', capsize=5)
        plt.title("Average Speed vs Setpoint" + location)
        plt.xlabel("Setpoint (mm/min)")
        plt.ylabel("Average Speed (mm/min)")
        plt.grid(True)
        speed_summary_plot = os.path.join(output_dir, location + "summary_speed_vs_setpoint.png")
        plt.savefig(speed_summary_plot)
        plt.close()

        # Create Summary Plot 2: Setpoint vs Average Relative Error with error bars
        plt.figure(figsize=(10, 6))
        plt.errorbar(summary["Setpoint"], summary["Avg_Relative_Error"], yerr=summary["Std_Relative_Error"],
                    fmt='o', capsize=5)
        plt.title("Average Relative Error vs Setpoint")
        plt.xlabel("Setpoint (mm/min)")
        plt.ylabel("Average Relative Error")
        plt.grid(True)
        relerr_summary_plot = os.path.join(output_dir, "summary_relative_error_vs_setpoint.png")
        plt.savefig(relerr_summary_plot)
        plt.close()

        print("Summary plots saved for " + location)
    else:
        print("No data available for master summary.")

make_summary_csv("C_")
make_summary_csv("L_")
make_summary_csv("R_")

#Huge oversight on my part I got the code to work and then failed to save it properly