# HSU Planner

This is implementation of an AI planner using Python. The program allows users to pass planning problems as Json files and get the solution as a Json file, along with visual representations of solutions. The program translates the planning problem into a graoh structure and uses a search algorithm to find the solution. To perform the graph search both forward and backward search are implemented, but the backward is being used as defualt as it shows better performance. Currently, both search algorithms are implemented using BFS, but the program is designed to be easily extended to other search algorithms. There are three main advantages with this planner. First, different than most of planners, it is designed to find all feasible solutions, not just one. Second, based on the aforementioned feature, it is possible to enumerate all feasible solutions and compare them based on different criteria. Third, the program extends the concept of planning to scheduling, which means it also provides detailed schedules for the solutions.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

Instructions on how to install the project and how to get started.

- git clone https://conf.informatik.uni-hamburg.de/dtec/planner.git
- Run pip install -r requirements.txt
- Locate your Json input file in the inputs directory, and provide the file name as the input argument along with an arbitrary name for the corresponding output folder. If you wish to see the solution and the visual representation of the solution, use the --print and --visualize arguments, respectively. Run the program using the following command:
    - ```python src/main.py --input <input_file> --output <output_file> --print --visualize```

- To see the help menu, run the following command:

    - ```python src/main.py --help```

## Usage

Instructions on how to use the project and how to get started.

- Example 1:
    - ```python src/main.py --input sample1.json --output sample1 --print --visualize```
    - This will make a folder named sample1 in the outputs directory saves the following files:
        - plans/*.png: The visual representations of the plans found. Below you can see an example of the visual representation of the plan found for the sample1.json file:
          ![sample_plan_output](assets/sample_plan_output.png)
        - schedules/*.png: The visual representations of the schedules for the plans found. Below you can see an example of the visual representation of the schedule found for the sample1.json file:
          ![sample_schedule_output](assets/sample_scheduled_plan_output.png)
        - sample1.json: The detailed solution in Json format. The output Json file contains the following information:
            - optimizeFor: The objective function used to optimize the plan.
            - Minimum Plan: The value of minimum plan found.
            - Maximum Plan: The value of maximum plan found.
            - Number of Plans: The number of plans found.
            - Plans: The detailed plans found. Moreover, each plan contains the following information:
                - plan_id
                - plan_value
                - actions: Also actions contain the following information:
                    - id
                    - preconditions: list of preconditions
                    - finalStateId: The final state of the action
                    - startingPoint: The starting point of the action based on the result of scheduling
                    - endingPoint: The ending point of the action based on the result of scheduling
                    - costs: The cost of the action
                    - producerId:  Id of the producer of the action
                    - processingTimeInWeeks
                    - workingTimeInHours


## dockerized standalone script
build the image:
```
docker build -t hsu-planner-dckr .
```

use the script in docker:
```
docker run hsu-planner-dckr --help
```

```
docker run -v "$(pwd)/inputs:/usr/src/app/inputs/" -v "$(pwd)/outputs:/usr/src/app/outputs/" hsu-planner-dckr --input sample2.json --output sample2 --print --visualize
```

## flask wrapper
* `src/planner_flask.py` is a wrapper around the script, and serves an API.
* locally you can let it serve at `http://localhost:8000` by running in this repo root: `docker-compose up -d`


### API Endpoint(s)
#### Trigger Task

- **URL**: `/trigger-task`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Description**: Triggers a background task to run a specified Python script with given input data. The task's progress is not tracked directly through this API, but completion is notified via a callback URL.

##### Request Body

| Field             | Type   | Required | Description                                                                                                                                 |
|-------------------|--------|----------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `inputJsonData` | JSON   | Yes      | The input data for the task.                                                                                                                |
| `callbackUrl`    | String | Yes      | The URL to which the task's completion notification will be sent.                                                                           |
| `maxCost`        | Int    | No       | A parameter to specify max cost of a plan. default: -1                                                                                      |
| `outputParam`    | String | No       | A parameter to specify the output file name. Must consist of letters, digits, underscores, periods, and dashes. Default is an empty string. |

##### Response

**Success:**

- **Code**: `202 Accepted`
    - **Content**: `{"message": "Task started"}`

**Errors:**

- **Code**: `400 Bad Request`
    - **Content**: Error message indicating what is wrong with the request (e.g., missing required fields, invalid JSON).

- **Code**: `429 Too Many Requests`
    - **Content**: `{"error": "Maximum number of concurrent tasks reached", "running_tasks": <current_tasks>}`

##### Example Request

```json
{
  "input_json_data": {
     // input json data for task which will forward it to the planner script
    },
  "callback_url": "http://example.local/callback",
  "output_param": "MYTASK_ID"
}
```

### Callback Notification

When a task is completed, the system sends a callback to the specified `callback_url` with a `POST` request. This callback contains the status of the task, a unique identifier, and the output data generated by the task.

#### Callback Request

- **Method**: `POST`
- **Content-Type**: `application/json`
- **Body**:

| Field    | Type   | Description                                                   |
|----------|--------|---------------------------------------------------------------|
| `status` | String | The completion status of the task. Expected value: `"completed"`. |
| `id`     | String | The unique identifier for the output data. This is specified by the `output_param` in the task trigger request. |
| `data`   | JSON   | The output data generated by the task, formatted as JSON.     |

#### Example Callback Request Body

```json
{
  "status": "completed",
  "id": "MYTASK_ID",
  "data": {
    // output data from the task
  }
}
```


## Contributing

Guidelines for contributing to the project and how to submit pull requests.

## License

Information about the project's license and any additional terms or conditions.
