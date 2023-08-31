import requests
import logging
import json
from datetime import datetime
import pytz
import psycopg2
from config import API_KEY, REQUESTER_ID, DB_HOST, DB_USER, DB_PASS, DB_DATABASE

# Configure logging format
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Configuration handling (e.g., using command-line arguments or environment variables)
def load_configuration():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        return config.get('target_project_name', '')

# Fetch project data by project ID
def fetch_project_data(project_id, headers):
    project_data_url = f'https://cloud.imi-hydronic.com/api/v1/projects/{project_id}'
    try:
        response = requests.get(project_data_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error('Error fetching project data: %s', e)
        return None

# Convert UTC time string to CET
def convert_utc_to_cet(utc_time_str):
    utc_time = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%SZ')
    utc_timezone = pytz.timezone('UTC')
    cet_timezone = pytz.timezone('Europe/Berlin')  # CET time zone
    cet_time = utc_timezone.localize(utc_time).astimezone(cet_timezone)
    cet_time_str = cet_time.strftime('%Y-%m-%d %H:%M:%S %Z')
    timestamp = int(cet_time.timestamp())
    return cet_time_str, timestamp

# Fetch TA-Smart data by datapoints URL
def fetch_tasmart_data(datapoints_url, headers):
    try:
        response = requests.get(datapoints_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error('Error fetching TA-Smart data: %s', e)
        return None

# Function to insert data into the database
def insert_into_database(data_to_insert):
    try:
        # Establish a connection to the PostgreSQL database
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_DATABASE,
        )

        # Create a database cursor
        cursor = conn.cursor()

        # Define the SQL INSERT statement (adjust the table name and columns as needed)
        insert_sql = "INSERT INTO tasmart_data_table (timestamp, tasmart_id, measured_flow, measured_power) VALUES (%s, %s, %s, %s)"

        # Execute the INSERT statement with data
        cursor.execute(insert_sql, (data_to_insert['timestamp'], data_to_insert['tasmart_id'], data_to_insert['measured_flow'], data_to_insert['measured_power']))

        # Commit the transaction
        conn.commit()

        logger.info('Data inserted into the database successfully.')

    except Exception as e:
        # Handle database insertion error
        logger.error('Error inserting data into the database: %s', e)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def main():
    try:
        target_project_name = load_configuration()
        headers = {
            'Requester-ID': REQUESTER_ID,
            'Authorization': f'ApiKey {API_KEY}',
        }
        projects_url = 'https://cloud.imi-hydronic.com/api/v1/projects'
        
        response = requests.get(projects_url, headers=headers)
        response.raise_for_status()
        projects = response.json()

        target_project = next((p for p in projects if p['name'] == target_project_name), None)

        if target_project:
            project_id = target_project['id']
            project_data = fetch_project_data(project_id, headers)

            if project_data:
                tasmarts = project_data.get('tasmarts', [])

                for tasmart in tasmarts:
                    datapoints_url = f'https://cloud.imi-hydronic.com{tasmart["href"]["datapoints"]}?limit=1&properties[]=measured_flow&properties[]=measured_power'
                    tasmart_data = fetch_tasmart_data(datapoints_url, headers)

                    if tasmart_data:
                        # Print the ID of the current TA-Smart separated by a newline
                        logger.info('')
                        logger.info('\033[1mID of TA-Smart: %s \033[0m', tasmart['id'])

                        # Print the "time," "measured_flow," and "measured_power" properties
                        for point in tasmart_data['points']:

                            cet_time_str, timestamp = convert_utc_to_cet(point['time'])
                            measured_flow = int(point['measured_flow'])
                            measured_power = int(point['measured_power'])
                            tasmart_id = tasmart['id']

                            logger.info('Time from API: %s', point['time'])
                            logger.info('Time CET: %s', cet_time_str)
                            logger.info('Timestamp (CET): %s', timestamp)
                            logger.info('Measured Flow: %s', measured_flow)
                            logger.info('Measured Power: %s', measured_power)

                            data_to_insert = {
                                'timestamp': timestamp,
                                'tasmart_id': tasmart_id,
                                'measured_flow': measured_flow,
                                'measured_power': measured_power
                            }

                            # Insert the data into the database
                            insert_into_database(data_to_insert)

                    else:
                        logger.warning('No data found for TA-Smart: %s', tasmart['id'])
            else:
                logger.warning('Project data not found for project: %s', target_project_name)
        else:
            logger.warning('Project not found: %s', target_project_name)

    except Exception as e:
        logger.error('Error: %s', e)

    # Add a newline for easier reading
    logger.info('')

if __name__ == '__main__':
    main()
