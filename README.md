# IMI API Data Retrieval Script

This Python script retrieves energy consumption data from TA-Smart valves using the IMI API, and saves it into a PostgreSQL database on AWS.

## WHY?

The goal of this project is an internal prototype only (please make sure this is just a prototype!) with the scope of work to:
- Test IMI APIs (keep in mind we are the first one using them in the world...)
- Understand if the data needed for Enerbrain is available via API
- Understand the best approach to retreive energy consumption data via API

Currently in Enerbrain we retreive this data via Modbus using an eGateway Modbus, however this method has some issues (each valve needs to be connected to an eGateway Modbus, with the need to maintain the phisical infrastructure to retreive the data)

A best way to do this would be using IMI APIs.

## Documentation about IMI and their APIs

IMI is an international producer of Hydraulic Valves, and the product that is subject of this API integration is their TA-Smart.

This is an example of a TA-Smart with a pipe diameter of 65mm:
![TA-Smart image](https://www.imi-hydronic.com/sites/default/files/styles/large/https/assets.imi-hydronic.com/Pictures/Image_Gallery_TA/Photos/TA-Smart/TA-Smart_DN65_w_sensor_2.gif?itok=gJ8RX4yd)

The API Documentation can be found in the /documentation folder, updated on the 4th Sept 2023. Future updates can be requested to the IMI R&D team asking to Bastien Ravot at ![bastien.ravot@imi-hydronic.com](bastien.ravot@imi-hydronic.com)

The TA-Smart Documentation can be found on the ![IMI website](https://www.imi-hydronic.com/it/product/ta-smart)

IMI also provides a full Web App where users can access all the data from the IMI TA-Smart Valves. The IMI Web App platform can be accessed via ![this link](https://cloud.imi-hydronic.com/projects/469bb186-150a-49ee-a86f-da1947e0bd0e/ta-smart/b5e6a019-ce22-4814-a5db-8badb169d8c6).


### energy_counter_regime_1 and 2... what the hell are them?
Energy in a TA_Smart is saved in multiple ways... we can access for example the realtime power used, but also two energy counters, 1 and 2.
Why are they 2? And what do they represent?
In reality IMI developed 2 registers to allow maximum flexibility, but during the installation of the valves phisically on site, it is up to the installers to decide what to do with this registers!

At Lingotto for example only energy_counter_regime_1 is used, and 2 is always = 0.

To be honest I don't know what IMI had in mind to have 2 registers, but they explained one could be used for cooling power and one for heating power, however they didn't developed the firmware of the valves yet for this...
For now it would be healty to save both to our database just in case but most likely regime_2 will always be = 0.


## Prerequisites - before starting!

### About IMI
Before playing around with the script, make sure you actually understand what is a IMI TA-Smart Valve! Ask colleagues of OPS about it, and learn from the documentation, because there are several data that can be collected.

Also, be aware that IMI is "learning how to do APIs as well...", and this means they openly admitted this is the first time they created APIs and documentation about them... If you have questions, their R&D team is available on Slack and Filippo Ferraris can help to do the introductions to the right people. 

If you have comments about the APIs, questions, or even tips to give to IMI, they'll be very happy to receive them!

### Get IMI credentials and API KEYs
Before starting, be familiar with the ![HyCloud](https://cloud.imi-hydronic.com) App by IMI and get the credential to access it. (username and password).
To have those credentials you need to ask to IMI R&D team.

To access the APIs you'll need both a company REQUESTER_ID and an API_KEY.

To get a REQUESTER_ID you need to contact directly IMI R&D team. They provide a single REQUESTER_ID per company, we do have one in Enerbrain, and Filippo Ferraris can provide it separately from this repository.

An API_KEY can be individually generated from ![HyCloud](https://cloud.imi-hydronic.com)

### Setup your environment to test this script

Starting point is to setup on AWS:
- EC2 on AWS to run the script periodically (crontab)
- RDS database / PostgreSQL

Make sure you have the following prerequisites installed on the EC2:
- Python 3.x
- PostgreSQL database
- Required Python packages (you can install them using `pip`, see comments below):
  - `requests`
  - `psycopg2`
  - `pytz`

## Installation

SSH to your EC2 (or connect to it in other ways)

1. **Clone this repository** to your EC2 machine:

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

Note: you may need to install pip... as by default is not installed on Amazon Linnux 2023. To install pip it can be enough to run "sudo yum install python3-pip -y" or maybe you need to download the full installation package if yum doesn't find it... 

## Configuration

1. **Create a `config.json` file** in the project directory with the following structure:

   ```json
   {
       "target_project_name": "Your_Target_Project_Name"
   }
   ```

   Replace `"Your_Target_Project_Name"` with the name of the target project that you can find in hyCloud by IMI.

   Note: for the moment I'm using Lingotto project, that contains 7 valves installed and online. However this is an important point in configuring this script in production: a study should be done on the best implementation method... if by Project or by individual valve...
   However the code should be simple enough to edit to switch from Project mode to Single Valve.

2. **Modify the `config.py` file** with your API KEYs and database connection details:

   ```python
   API_KEY = 'xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'
   REQUESTER_ID = 'xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx'


   DB_HOST = "your_database_host"
   DB_USER = "your_database_user"
   DB_PASS = "your_database_password"
   DB_DATABASE = "your_database_name"
   ```

   DB_xxx variables are to setup the connection to an RDS PostgreSQL.
   Make sure to have the authorization between EC2 and RDS setup correctly.

   Note: this obviously is for testing purpouses. The real production envionment should follow the correct database structure and architecture that I totally ignore.

3. Setup the PostgreSQL database

   To be able to save data in the database you need to set it up.
   Connect to it via 
   ```shell
   psql -h your-database-host -U your-username -d your-database-name
   ```
   and from the database prompt, use the command:
   ```shell
   CREATE TABLE tasmart_data_table (
	   id SERIAL PRIMARY KEY,
	   timestamp INTEGER,
	   tasmart_id VARCHAR(255),
	   measured_flow INTEGER,
	   measured_power INTEGER,
	   energy_counter_regime_1 INTEGER,
	   energy_counter_regime_2 INTEGER
   );
   ```

   Note: at the moment I'm using the tasmart_id to identify each single TA-Smart in the project, however discussing it with the IMI team they confirmed that we can use also the variables "full_sn" and "short_sn"


## Usage

To run the script, execute the following command:

```shell
python3 imi_api.py
```

or 

```shell
python imi_api.py
```

(choose according to the python command in your environment)


## Scheduled Execution

To schedule the script to run every 15 minutes, you can use a tool like Cron on Unix-based systems. Here's an example Cron job:

```shell
*/15 * * * * /path/to/your/script/run_imi_api.sh
```

Make sure to adjust the path to your script accordingly.

## Next steps, known issues, additional notes

### Ways to access the single Valves (via projects, or via individual ID)
This script iterates all the valves present in a single Project using the Project Name.
This is a stong liability for a production environment, as if from hyCloud a user changes the name of a Project, the script will end in an error...

Probably a better way to do this would be to link single valves to single registers in our backend.

However it must be said that valves won't be moved... once a valve is installed it will be the same valve forever (until a serious break...)

### Indivudal requests = large volumes of requests to IMI backend
As each invididual valve needs a single request each, if there are 1000 valves in total, each 15 minutes we'll end up sending 1000 individual requests and this can cause issues (from my bad knowledge and ignorance)
This is a known issue by IMI and they will most likely improve their API in the future revisions

### Link a single valve with our Backend
This is all to be thought and created...

### Convert the energy counter to the actual consumption in kWh
We can grab data from the valve, but the registers energy_counter_regime_1 and 2 are simple "odometer style counter" (always increasing). To my knowledge this is identical to eGauge APIs data, therefore we could copy the way we interpret the data.

### IMI APIs don't have limits...
Be aware currently there are no limits in the use of the API but they will implement them using API KEYs of the customers.
Therefore... be careful to not trigger issues.

### EC2 vs Lambda
I'm aware setting this up with a Lambda would be WAY cheaper and efficient, but I did set it up with an EC2 as I wanted to have an easier use of logging / experimenting / playing around with this test...
This is just for testing purpouses, therefore for production environment there are for sure better ways of doing it!

### Granularity of data
The maximum granularity of the historical consumption data we use in Enerbrain (to my knowledge) is 15 min. Therefore it makes sense to also save valves data every 15 minutes.
However, we do calculations of baselines / energy savings / analysis typically with hourly granularity... therefore it is to be checked with ENG and OPS what is the ideal granularity.

### data that we can save
At the moment I'm saving only the data I thought was useful for testing...
The bare-minimum would be only the consumption registers (energy_counter_regime_1 and 2) because those would be the data we use for baselines and calculations and are the ones useful for the customers.
However some additional data could be interesting for statistical perspective and to diagnose issues.
I would suggest checking with ENG and OPS what other data could be useful to collect from the list available from the valve.
If additional data is not too expensive, I would even save everything...

(I've asked IMI, and they collect in their cloud currently ALL the data EVERY 15 seconds... that is quite insane to be honest, but they explained they don't have limits of database and they want to then use this data to do diagnostic on their own valves for future R&D development on the product).

