import os
import sys
import logging
import re
import json
import tempfile
import subprocess
import threading
from threading import Semaphore, Lock
from environs import Env
import requests
from flask import Flask, jsonify, request

# Initialize Flask app
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

env = Env()
env.read_env()

# Semaphore to limit to 3 concurrent subprocesses
MAX_CONCURRENT_TASKS = 3
semaphore = Semaphore(MAX_CONCURRENT_TASKS)

# Lock and counter for running tasks
running_tasks_lock = Lock()
RUNNING_TASKS_COUNT = 0

# storage, tempfs("/tmp") or memory("/dev/shm")
BASE_FOLDER = env("BASE_FOLDER", "/dev/shm")
PERSIST_FOLDERS = env.bool("PERSIST_FOLDERS", default=False)

VALID_FILENAME_REGEX = re.compile(r'^[a-zA-Z0-9.%_-]+$')


if "/dev/shm" in BASE_FOLDER and PERSIST_FOLDERS:
    logging.error("Usage of /dev/shm as BASE_FOLDER with persistence enabled via PERSIST_FOLDERS, is not allowed and would keep keep files in memory for ever")
    sys.exit(4)


def run_task_and_release_semaphore(callback_url, input_data, output_param, max_cost):
    global RUNNING_TASKS_COUNT
    try:
        with running_tasks_lock:
            RUNNING_TASKS_COUNT += 1
        # Create colision-free dir for lifetime of this block, similar to GNU mktemp
        with tempfile.TemporaryDirectory(dir=BASE_FOLDER, delete=PERSIST_FOLDERS) as temp_dir:
            logging.info('Temporary directory path: %s', temp_dir)

            # Create inputs dir inside temp_dir
            inputs_dir = os.path.join(temp_dir, "inputs")
            os.makedirs(inputs_dir, exist_ok=True)

            logging.info('Write input json payload to file')
            input_file_path = os.path.join(inputs_dir, "input.json")
            with open(input_file_path, 'w', encoding="utf-8") as input_file:
                json.dump(input_data, input_file)
            command = ["python", "/usr/src/app/src/main.py", "--input", "input.json", "--output", output_param, "--max-cost", str(max_cost)]

            # run command inside temp dir
            process = subprocess.Popen(command, cwd=temp_dir)
            process.wait()

            # Read output json file and notify via callback url
            output_dir_path = os.path.join(temp_dir, "outputs", output_param)
            output_file_path = os.path.join(
                output_dir_path, output_param + ".json")
            logging.info('output file path is: %s', output_file_path)
            with open(output_file_path, 'r', encoding="utf-8") as output_file:
                out_js = json.load(output_file)
                logging.info("json out: %s", out_js)
            try:
                requests.post(callback_url, json={
                              "status": "completed", "id": output_param, "data": out_js}, verify = False)
            except requests.RequestException as e:
                # Handle errors in making the callback HTTP call
                logging.error(f"Error making callback HTTP request: {e}")
    finally:
        # Decrement running tasks count and release the semaphore
        with running_tasks_lock:
            RUNNING_TASKS_COUNT -= 1
        semaphore.release()


# Flask endpoint to trigger tasks in background
@app.route('/trigger-task', methods=['POST'])
def trigger_task():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json()

    input_json_data = data.get('inputJsonData')
    if not input_json_data:
        return jsonify({"error": "Missing 'inputJsonData'"}), 400

    callback_url = data.get('callbackUrl')
    if not callback_url:
        return jsonify({"error": "Missing 'callbackUrl'"}), 400
    # ToDO: URL validation, e.g.: endswith(domain.com), docker service urls

    # Default to empty string if not provided
    output_param = data.get('outputParam', '')
    # check for valid filenames, minimize cmd injection
    if not VALID_FILENAME_REGEX.match(output_param):
        return jsonify({"error": "Invalid input for 'outputParam'. Only letters, digits, underscores, periods, and dashes are allowed."}), 400

    # Default to empty string if not provided
    max_cost = data.get('maxCost', -1)

    if semaphore.acquire(blocking=False):
        # Start a background thread, pass both callback_url and input json and output pattern
        # ToDO: if callback_url cannot be unique, require and add UUID here from payload
        threading.Thread(target=run_task_and_release_semaphore, args=(
            callback_url, input_json_data, output_param, max_cost)).start()
        return jsonify({"message": "Task started"}), 202
    else:
        with running_tasks_lock:
            current_tasks = RUNNING_TASKS_COUNT
        return jsonify({"error": "Maximum number of concurrent tasks reached", "running_tasks": current_tasks}), 429


if __name__ == '__main__':
    app.run(debug=True)