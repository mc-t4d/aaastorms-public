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
  * [Container Architecture](#container-architecture)
  * [Orchestration](#orchestration)
  * [Functions](#functions)
- [Deployment](#deployment)
  * [Prerequisites](#prerequisites)
  * [Configuration](#configuration)
  * [Deployment Steps](#deployment-steps)
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

#### Container Architecture
The AAAStorms application uses a **containerized serverless architecture** with the following components:

**Containerized Lambda Functions:**
- Each of the three main functions (ETL, ETL Triggers, Report) is packaged as a separate Docker container
- Containers are built automatically by the Serverless Framework during deployment
- Base image: `public.ecr.aws/lambda/python:3.9` (AWS Lambda Python runtime)
- Each container includes function-specific Python dependencies and code

**Container Build Process:**
1. Serverless Framework reads Dockerfiles from each function directory (`src/etl/`, `src/etlTriggers/`, `src/report/`)
2. Builds Docker images for `linux/amd64` platform
3. Automatically pushes images to AWS ECR (Elastic Container Registry)
4. Creates/updates Lambda functions to use the container images
5. Configures proper IAM permissions for Lambda to access ECR

**Benefits:**
- **Isolation**: Each function has its own dependencies and runtime environment
- **Scalability**: Lambda automatically scales containers based on demand
- **Consistency**: Same runtime environment across development and production
- **Cost-Effective**: Pay only for execution time, containers spin up on-demand

#### Orchestration
The AAAStorms application runs on two separate loops, orchestrated by AWS Step Functions:

- **12-hour loop**: Checks for storms in pretrigger OR trigger status
- **6-hour loop**: Checks for storms in trigger status only

These loops invoke state machines that coordinate the three Lambda functions in sequence. The Step Functions are automatically deployed as part of the serverless configuration and handle error retry logic and conditional branching based on storm data.

State Machine Definitions:
1. [12H Loop](pck/stepfunction_12H.json)
2. [6H Loop](pck/stepfunction_6H.json)

#### Functions
The AAAStorms application uses containerized AWS Lambda functions to run each stage of the ETL process:

1. **[etl](src/etl/)** - Calls the NOAA RSS GIS feed and parses storm information; saves raw data to the `aaastorms-stormdata` S3 bucket
2. **[etlTriggers](src/etlTriggers/)** - Retrieves storm data and creates trigger datasets based on available information; saves trigger data to `aaastorms-stormtriggers` S3 bucket
3. **[report](src/report/)** - Retrieves storm triggers and builds HTML reports using Python Jinja templates; sends formatted reports via Amazon SES to emails configured in [config.py](src/report/config.py); saves reports to `aaastorms-stormreports` S3 bucket

### Deployment

#### Prerequisites
Before deploying, ensure you have:

1. **AWS CLI** configured with appropriate credentials
2. **Serverless Framework** installed globally: `npm install -g serverless`
3. **Docker** installed and running on your machine
4. **Node.js and npm** for installing the serverless-step-functions plugin
5. **AWS Account** with permissions for Lambda, ECR, S3, SES, Step Functions, and IAM

#### Configuration

**Important**: Before deployment, you must update the `serverless.yml` file with your specific configuration:

1. **Update Organization**: Change the `org` field to your Serverless Framework organization:
   ```yaml
   org: your-serverless-org-name
   ```

2. **Automatic Account ID**: The configuration automatically uses `${aws:accountId}` to resolve your AWS account ID - no manual replacement needed.

3. **Install Required Plugin**:
   ```bash
   npm install --save-dev serverless-step-functions
   ```

#### Deployment Steps

**Critical**: The following environment variables are **required** for successful deployment due to Docker buildx compatibility issues:

```bash
# Set required environment variables (CRITICAL - deployment will fail without these)
export DOCKER_BUILDKIT=1
export DOCKER_CLI_EXPERIMENTAL=enabled
export BUILDX_NO_DEFAULT_ATTESTATIONS=1

# Deploy to development environment (default)
serverless deploy

# Or deploy to production
serverless deploy --stage prod
```

**What happens during deployment:**
1. Serverless Framework builds Docker containers for each function
2. Images are pushed to your AWS ECR repositories (created automatically)
3. Lambda functions are created/updated with container images
4. Step Function state machines are deployed
5. S3 buckets, IAM roles, and permissions are configured
6. The complete storm monitoring system becomes operational

**Deployment Output:**
After successful deployment, you should see:
- 3 Lambda functions (etl, etlTriggers, report)
- 2 Step Function state machines (12H and 6H loops)
- ECR repositories with your container images
- S3 buckets for data storage

### Troubleshooting

#### Deployment Issues
- **ECR Permissions Error**: Ensure the environment variables above are set before deployment
- **Docker Build Failures**: Verify Docker is running and you have sufficient disk space
- **Account ID Mismatch**: Confirm your AWS account ID is correctly configured in serverless.yml

#### Operational Issues
- **Update email distribution list**: Modify the `config.py` file in the [report](src/report/) module
- **Change report frequency**: The frequency is controlled by EventBridge triggers that initiate the Step Function state machines
- **Modify report format**: Update the [Jinja templates](src/report/templates/); for new variables, update the `build_reports` function in [reporting.py](src/report/reporting.py)
- **Turn off the system**: Disable the EventBridge triggers in the AWS console

### AWS Resource Utilization Estimates

- **AWS Lambda**: $0.00 / month (free tier)
- **AWS Step Functions**: $0.00 / month (free tier)
- **AWS ECR**: $0.00 (free tier for 12 months, thereafter $0.10/GB/month)
- **AWS S3**: $0.00 (free tier for 12 months, thereafter $0.023/GB/month)
- **AWS S3 Static Web Hosting** (for documentation): $0.00 / month
- **AWS SES**: $0.00 (free tier for 12 months, thereafter $0.10/1000 emails)
- **Serverless Framework**: $0.00 (open source)
- **GitHub Repository**: Enterprise subscription through IT

### Summary of Skills for Consultants
In the event that T4DS is unable to support further development of this project, we have included a summary of skills and qualifications that you may want to consider including on a consultant solicitation.
[Consultant Scope](pck/consultant_scope.txt)
