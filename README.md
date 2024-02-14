# Get Kinmen Address Coordinates

## Introduction
This Python script retrieves address coordinates data from the Kinmen Urban Development Bureau website.

## Features
- Retrieves town, road, lane, alley, and door information from the Kinmen Urban Development Bureau website.
- Converts coordinates from TWD97 to WGS84.
- Logs information about the retrieval process.
- Writes the retrieved coordinates to a CSV file.

## Dependencies
- Python 3.x
- requests
- loguru
- pyproj
- beautifulsoup4

## Installation
1. Clone the repository:

    ```
    git clone https://github.com/skyksl066/getKinmenAddressCoordinates.git
    ```

2. Install dependencies:

    ```
    pip install -r requirements.txt
    ```

## Usage
1. Run the script:

    ```
    python app.py
    ```

2. The retrieved coordinates will be saved in a CSV file named `data.csv`.

## Notes
- Modify `MAX_RETRIES` in `app.py` to adjust the maximum number of retries for failed requests.
- Change the `LOG_PATH` variable in `app.py` to specify the path for the log file.
- The program saves its progress in `resume.txt`, allowing it to resume from where it left off in case of interruption.
