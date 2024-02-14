# Get Kinmen Address Coordinates

## Introduction
This Python script retrieves address coordinates data from the Kinmen Urban Development Bureau website.

## Features
- Retrieves town, road, lane, alley, and door information from the Kinmen Urban Development Bureau website.
- Uses multi-threading to process multiple towns concurrently.
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

## Configuration

- `MAX_RETRIES`: Maximum number of retries for failed requests.
- `API`: URL for the API used to retrieve data.
- `LOG_PATH`: Path to the log file.
- `CSV_FILE`: Path to the CSV file to save coordinates.
- `FIELDNAMES`: Names of the fields in the CSV file.
- `RESUME_FILE`: Path to the file to store processed locations.
- `BATCH_SIZE`: Number of towns to process concurrently.

## Notes

- Ensure internet connectivity for the program to work.
- The program may take some time to complete processing, depending on the number of towns and roads.
