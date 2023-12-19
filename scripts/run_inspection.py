#!/usr/bin/env python3

##################################################
__NAME__ = f'Delvitech Inspection Runner'
__DESCRIPTION__ = 'utility to run a recipe multiple times continuosly'
__VERSION_ = 'v1.0.0'
__AUTHOR__ = 'LT'
##################################################
## Usage: call this script from terminal, read tutorial by calling it with the --help flag.
##################################################

import os
import argparse
import subprocess
import threading
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# import socketio

import requests

##################################################
############## MUTABLE PARAMETERS ################
##################################################

PROTO_SCHEME = 'http://'
PORT = 3000

ie_container = "134_inspection-engine_1"
acq_container = "134_acq_microservice_1"

##################################################
################## UTIL FUNCS ####################
##################################################

def login(ip, user, password, verbose):
    auth_dict = {"username": user, "password": password}

    r_login = requests.post(f'{PROTO_SCHEME}{ip}:{PORT}/v1/auth/login', json=auth_dict)
    if r_login.status_code == 200:
        login_token = r_login.json().get('access_token')
        if login_token:
            if verbose:
                print(f'ACCESS_TOKEN for {ip}: {login_token}')
            return login_token
        else:
            print('No access token found in the response')
    else:
        print(f'Login request failed with status code: {r_login.status_code}')

    return None

def sanitize_path(path):
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    return path

def check_response(response):
    is_good_response = 'pcba_descriptor' in response
    if is_good_response:
        print(f'done :)')
    else:
        print('failed :(')

    return is_good_response

##################################################

# sio = socketio.Client()  # Create the sio object once

# # Set up event handlers for the sio object
# @sio.on('lt_inspection_progress')
# def on_inspection_progress(data):
#     print("Received progress message:", data)

# @sio.on('lt_inspection_end')
# def on_inspection_end(data):
#     print("Received 'inspection_end' event:", data)
#     sio.disconnect()  # Disconnect from the socket when inspection is complete


def run_inspection(ip, token, recipe_id, recipe_ver, number_of_runs):
    if token:
        auth_header = {'Authorization': f'Bearer {token}'}
        url = f'{PROTO_SCHEME}{ip}:{PORT}/v1/inspection/draft/pcba/{recipe_id}/{recipe_ver}?prefix=lt_'

        payload = {
            "pcba_id": recipe_id,
            "pcba_version": recipe_ver,
            "save_all": False,
            "save_results": False,
            "alignment": True,
            "inspect": True,
            "acquire": True,
            "iteration": 1,
            "components": [],
            "windows": [],
            "user_id": 0,
            "generate_recipe_file": False,
            "generate_window_recipe_file": False,
            "generate_recipe_for_defects": False,
            "good_defect_ratio": 0,
            "max_ids": 0,
            "max_package_types": 0,
            "source_file_path": "",
            "dst_extraction_path": "",
            "clear_alignment_matrix_cache": False,
            "clear_window_recipe_cache": False,
            "production": False,
            "multiple_windows_snapshot": False
        }

        try:
            # Send the request to start the inspection
            r_run_recipe = requests.post(url, headers=auth_header, json=payload)

            if r_run_recipe.status_code == 200:
                # You can extract any information from the response here if needed
                response_data = r_run_recipe.json()
                print("Inspecting...")
                print(response_data)
                # logs = get_container_logs(container_name)

                # if "INSPECTION END STEP" in logs:
                #     print("INSPECTION END STEP")

            else:
                print("Error starting inspection:", r_run_recipe.text)
        except Exception as e:
            print(f"An error occurred: {e}")

    else:
        print('No valid authentication token available. Authentication may have failed.')

def get_container_logs(container_name):
    try:
        # Define the 'docker logs' command
        command = ["docker", "logs", container_name]

        # Run the command and capture the output
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            # Split the logs into lines
            log_lines = stdout.split('\n')
            
            # Return the last 10 lines (or less if there are fewer than 10 lines)
            return '\n'.join(log_lines[-10:])
        else:
            return f"Error retrieving logs: {stderr}"
    except Exception as e:
        return f"An error occurred: {e}"

def check_acquisition_logs(acq_container):
    target_lines = [
        "Projector score for side 0 is",
        "Projector score for side 1 is",
        "Projector score for side 2 is",
        "Projector score for side 3 is",
    ]
    
    processed_lines = set()
    scores = {0: [], 1: [], 2: [], 3: []}  # Store scores for each side

    while True:
        acq_logs = get_container_logs(acq_container)
        for line in acq_logs.split('\n'):
            for target_line in target_lines:
                if target_line in line and line not in processed_lines:
                    parts = line.split()
                    if len(parts) >= 8:
                        try:
                            score = float(parts[-1])
                            if score < args.score:
                                print(f"Log: {line}")
                                processed_lines.add(line)
                                side = int(re.search(r'\d+', target_line).group())  # Extract side number using regex
                                scores[side].append(score)
                        except (ValueError, IndexError):
                            print(f"Error processing line: {line}")
        
        # Create a plot of scores for each side
        #plot_scores(scores)

def plot_scores(scores):
    # Create a plot for each side
    for side, side_scores in scores.items():
        plt.figure()
        plt.plot(range(1, len(side_scores) + 1), side_scores, marker='o', linestyle='-')
        plt.title(f"Scores for Side {side}")
        plt.xlabel("Run")
        plt.ylabel("Score")
        plt.grid(True)
        plt.savefig(f"side_{side}_scores.png")

##################################################

def main(args):
    usr, pwd = args.credentials.split(':')
    src_login_token = login(ip=args.from_ip,
                                user=usr,
                                password=pwd,
                                verbose=args.verbose)
    
    acq_log_thread = threading.Thread(target=check_acquisition_logs, args=(acq_container,))
    acq_log_thread.daemon = True
    acq_log_thread.start()

    # Loop for the specified number of runs
    for run in range(args.times):
        print(f"Starting inspection run {run + 1} of {args.times}")

        # Run the inspection
        run_inspection(ip=args.from_ip, token=src_login_token, recipe_id=args.id, recipe_ver=args.version, number_of_runs=1)

        ie_logs = get_container_logs(ie_container)
        if "INSPECTION END STEP" in ie_logs:
            print("INSPECTION END STEP detected in Inspection Engine logs. Proceeding to the next run.")

    print(f"All {args.times} inspection runs completed.")
    

if __name__ == '__main__':
    class SaneFormatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter): pass
    parser = argparse.ArgumentParser(prog=__NAME__,
                                     usage='run_inspection.py [-h] [--credentials CREDENTIALS] [--id ID] [--version VERSION] [--from-ip FROM_IP] [--times TIMES] [--score SCORE] [--verbose]',
                                     description=f'{__NAME__} ({__VERSION_}), maintained by {__AUTHOR__}.\n{__DESCRIPTION__}',
                                     epilog='example usage:\nrun_inspection.py --id=42\n\t\t\t  --times=1000\n',
                                     formatter_class=SaneFormatter)

    # Add script arguments
    parser.add_argument('--id',
                        help="Recipe ID to be inspected",
                        type=int)
    parser.add_argument('--version',
                        type=int,
                        help="Recipe version to be retrieved. Use only with --from-ip argument.",
                        default=1)
    
    parser.add_argument('--from-ip',
                           help="IP address to retrieve the Recipe from. Must specify ID and VERSION.",
                        default='localhost')
    
    parser.add_argument('--times',
                        help="Numbers of inspections to run",
                        type=int,
                        default=1)
    
    parser.add_argument('--score',
                        required=True, 
                        help="Projectors score to look for",
                        type=float)
    
    parser.add_argument('--credentials',
                        default='admin:password',
                        help="user and password to login in Neith. Must have the format 'user:password'.")

    parser.add_argument('--verbose',
                        action='store_true',
                        default=False,
                        help="show access tokens for IP connections.")
    
    # Parse arguments and check compatibility
    args = parser.parse_args()

    main(args)

