# IMI API Data Retrieval Script

This Python script retrieves data from the IMI API, converts timestamps to CET time, and inserts it into a PostgreSQL database.

## Prerequisites

Before running the script, make sure you have the following prerequisites installed:

- Python 3.x
- PostgreSQL database
- Required Python packages (you can install them using `pip`):
  - `requests`
  - `psycopg2`
  - `pytz`

## Installation

1. **Clone this repository** to your local machine:

   ```shell
   git clone https://github.com/filippoferraris/tasmart_api.git
   ```

2. **Navigate to the project directory**:

   ```shell
   cd tasmart_api
   ```

3. **Install the required Python packages**:

   ```shell
   pip install -r requirements.txt
   ```

## Configuration

1. **Create a `config.json` file** in the project directory with the following structure:

   ```json
   {
       "target_project_name": "Your_Target_Project_Name"
   }
   ```

   Replace `"Your_Target_Project_Name"` with the name of the target project that you can find in hyCloud by IMI.

2. **Modify the `config.py` file** with your API KEYs and database connection details:

   ```python
   API_KEY = 'xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'
   REQUESTER_ID = 'xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'


   DB_HOST = "your_database_host"
   DB_USER = "your_database_user"
   DB_PASS = "your_database_password"
   DB_DATABASE = "your_database_name"
   ```

## Usage

To run the script, execute the following command 
(I'm showing here python3 command assuming to run the script from an EC2 Amazon Linux 2003. Substitute with "python" instead if needed)

```shell
python3 imi_api.py
```

## Scheduled Execution

To schedule the script to run every 15 minutes, you can use a tool like Cron on Unix-based systems. Here's an example Cron job:

```shell
*/15 * * * * /path/to/your/script/run_imi_api.sh
```

Make sure to adjust the path to your script accordingly.
