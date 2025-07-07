# T4DS-AAAStorms
### Anticipatory Action for the Americas (Storms)
This work is licensed under a <a rel="license" href="https://creativecommons.org/licenses/by-nc/4.0">Creative Commons Attribution-NonCommercial 4.0 International Public License</a>.


## Table of Contents:

- [Admin Data and Contact Information](#admin-data-and-contact-information)
- [AWS Tags](#aws-tags)
- [Background](#background)
- [Data Inventory Summary](#data-inventory-summary)
  * [Data Flow Diagram](#data-flow-diagram)
- [Architecture](#architecture)
  * [Architecture Diagram](#architecture-diagram)
  * [Orchestration](#orchestration)
  * [Functions](#functions)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [AWS Resource Utilization Estimates](#aws-resource-utilization-estimates)
- [Summary of Skills for Consultants](#summary-of-skills-for-consultants)

### Admin Data and Contact Information
This project is a collaboration between T4D Data Science and Research and Learning (Guatemala).
Note that this md file is also available at the [documentation page](http://aaastorms-docs.s3-website-us-east-1.amazonaws.com/) for users without GitHub access. This page is publicly accessible. 

Contact information:
For development-related support and troubleshooting, please contact the T4DS Dev listed below. For information about the project, please contact Research and Learning.

- T4DS Dev: Alicia Morrison, amorrison@mercycorps.org
- T4DS Support: Aaron Eubank, aeubank@mercycorps.org
- R&L: Ellen Reid, ereid@mercycorps.org

### AWS Tags
AWS resources are tagged as:

1. project - aaastorms
2. region - americas
3. partner - research_and_learning
4. t4ds_dev - <email@mercycorps.org>
5. partner_poc - <email@mercycorps.org>

### Background
The purpose of Anticipatory Action for the Americas – Tropical Storms (AAA Storms) is to develop a risk framework for the Americas region that supports early release of remittances for resiliency and recovery.  
Mercy Corps, in partnership with Remitly and the Immigration Policy Lab at Stanford, is planning to scale up the forecast-based remittance service, as piloted under the Carnegie Climate Migration project in 2022. The forecast-based remittance service is a communication service that lets remittance senders know if a tropical storm is expected to hit an area where they regularly send money. Remittance senders in the United States receive an early warning notification through their mobile application, along with a financial incentive to send remittances to their contacts in Central America. The pilot of the forecast-based remittance service was completed in Huehuetenango, Guatemala, during the 2022 hurricane season. With the scale-up, we will expand the service to more communities in Central America (including Guatemala, Honduras, El Salvador, and Nicaragua) during the 2023 hurricane season. The design and operationalization of the pilot were successful and can be improved based on the experience of Tropical Storm Lisa in November 2022 and recommendations from our team and partners.

### Data Inventory Summary
The primary data source for AAAStorms is [NOAA National Hurricane Center](https://www.nhc.noaa.gov/) and the WFP ADAM Live platform. The NOAA data is accessed through the [NHC RSS GIS Feed](https://www.nhc.noaa.gov/aboutrss.shtml).

#### Data Flow Diagram
The data flow diagram demonstrates how data flows through the system and provides an overview of what happens at each stage of the application ETL process.
![Data Flow Diagram](https://github.com/mercycorps/t4ds-aaastorms/blob/main/pck/dataflow_diagram1.jpg)

### Architecture
#### Architecture Diagram
The architecture diagram shows the AWS tools and services used to link processes in the application.
![Architecture Diagram](https://github.com/mercycorps/t4ds-aaastorms/blob/main/pck/architecture_diagram1.jpg)

#### Orchestration
The AAAStorms application runs on two separate loops, a 12-hour loop to check for storms in pretrigger status and a 6-hour loop to check for storms in trigger status. These loops invoke slightly different state machines in AWS Step Functions. The 12H loop collects all storm data that is in trigger OR pretrigger status. The 6H loop collects only storm data that is in trigger status. Once a storm leaves trigger or pretrigger status, it will no longer be reported.

State Machine Definitions:
1. [12H Loop](stepfunction_12H.json)
2. [6H Loop](stepfunction_6H.json)

#### Functions
The AAAStorms application uses AWS Lambdas to run each stage of the ETL process.

Functions:
1. [etl](https://github.com/mercycorps/t4ds-aaastorms/tree/main/src/etl) - calls the NOAA RSS GIS feed and parses the information; saves the raw information to the aaastorms-stormdata bucket
2. [etlTriggers](https://github.com/mercycorps/t4ds-aaastorms/tree/main/src/etlTriggers) - retrieves the storm data and creates a trigger dataset based on the available information; saves the trigger dataset to aaastorms-stormtriggers
3. [report](https://github.com/mercycorps/t4ds-aaastorms/tree/main/src/report) - retrieves the storm triggers and builds an HTML report using a Python jinja template; the report function uses Amazon SES to send a formatted report to each email in the [config.py](https://github.com/mercycorps/t4ds-aaastorms/blob/main/src/report/config.py) file. The reports are saved to aaastorms-stormreports

### Deployment
The AAAStorms application is deployed using the serverless framework.
[You can learn how to use this open-source CLI tool in conjunction with AWS here](https://www.serverless.com/framework/docs/getting-started).
The AAAStorms ETL and report are a single service. Each function is containerized using Docker and uses a function-level .yml file to support Lambda configuration.

### Troubleshooting
What do I do if...
- I need to update the email distribution list?
  The email distribution list is updated in the `config.py` file found in the [report](https://github.com/mercycorps/t4ds-aaastorms/tree/main/src/report) module.
- I am getting too many reports? Or not enough?
  Report frequency is controlled by the timing of the [Step Function State Machines](https://github.com/mercycorps/t4ds-aaastorms/tree/main/pck); in order to change the report frequency, you can alter the [Event Bridge](https://us-east-1.console.aws.amazon.com/events/home?region=us-east-1#/rules) triggers that initiate the State Machines.
- I don't like the format of the report?
  The report format is established in the [Jinja template](https://github.com/mercycorps/t4ds-aaastorms/tree/main/src/report/templates); you can update the HTML template to change the format. Note that if you want to insert new variables into the report, you will need to update the `build_reports` function in the [report](https://github.com/mercycorps/t4ds-aaastorms/blob/main/src/report/reporting.py) module.
- Want to turn the system off?
  The system can be "turned off" by disabling the [Event Bridge](https://us-east-1.console.aws.amazon.com/events/home?region=us-east-1#/rules) triggers that initiate the State Machines.

### AWS Resource Utilization Estimates

- AWS Lambda: $0.00 / month (free tier)
- AWS Step Functions: $0.00 / month (free tier)
- AWS S3: $0.00 (free tier for 12 months, thereafter priced at $0.023 per GB)
- AWS S3 Static Web Hosting (for documentation page): $0.00 / month
- AWS SES: $0.00 (free tier for 12 months, thereafter priced at $0.10/1000 emails)
- Serverless Deployment: $0.00
- GitHub Repository: Enterprise subscription through IT

### Summary of Skills for Consultants
In the event that T4DS is unable to support further development of this project, we have included a summary of skills and qualifications that you may want to consider including on a consultant solicitation.
[Consultant Scope](https://github.com/mercycorps/t4ds-aaastorms/blob/main/pck/consultant_scope.txt)
