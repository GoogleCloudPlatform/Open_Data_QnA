
# Infrastructure deployment
The provided terraform streamlines the setup of this solution and serves as a blueprint for deployment. The script provides a one-click, one-time deployment option. However, it doesn't include CI/CD capabilities and is intended solely for initial setup.

> [!NOTE]
> Current version of the Terraform Google Cloud provider does not support deployment of a few resources, this soultion uses null_resource to create those resources using Google Cloud SDK.

## Table of Contents
- [Terraform folder structure](#terraform-folder-structure)
  - [Structure](#structure)
  - [.tf Files Description](#tf-files-description)
  - [Scripts](#scripts)
  - [Template files](#template-files)
- [Step 0: Prerequisites](#step-0-prerequisites)
  - [Data Sources](#data-sources-set-up)
  - [Enable Firebase](#enable-firebase)
  - [Local Configuration](#optional-local-configuration)
  - [Terraform Deployment](#terraform-deployment)
- [Step 1a: One-click Deployment](#step-1-one-click-deployment) [choose either 1a or 1b]
- [Step 1b: Step by step Deployment](#step-1-step-by-step-deployment) [choose either 1a or 1b]
- [Step 2: Review your environment](#step-2-review-your-environment)
- [Deployed Resources](#deployed-resources)
- [Troubleshooting Known Issues](#troubleshooting-known-issues)

## Terraform folder structure
#### Structure
```
Open_Data_QnA/
    |
    |--->terraform/
          |---> .tf files
          |---> scripts/
          |             |--> .sh, .py
          |---> templates/
                        |--> .tftpl files

```
1. .tf files - terraform scripts to spin up resources.
1. scripts/ - A folder containing all the required shell scripts and python files.
1. templates/ - the templates in this directory are used to replace all necessary configuration values for the application in config.ini and constants.ts

#### .tf Files Description
1. versions.tf - Contains provider blocks with appropriate versions that are needed to deploy the resources
1. locals.tf - Contains the list of APIs to be enabled and BQ tables to be created.
1. main.tf - Imports data about the mentioned project and also activates required APIs in the project.
1. iam.tf - Handles implementation of all the necessary IAM roles to various members like service accounts and users.
1. bq.tf - This script is responsible for creating Bigquery dataset.
1. pg-vector.tf - This is responsible for spinning up the CloudSQL instance, database, username and password.
1. embeddings-setup.tf - This script is responsible for the below tasks.
    * Update [config.ini](../config.ini) with values provided in variables.tf / terraform.tfvars.
    * Fetch list of data sources from [data_source_list.csv](../scripts/data_source_list.csv).
    * Create vector embeddings for the metadata associated with the listed tables.
    * Fetch known good sqls from [known_good_sql.csv](../scripts/known_good_sql.csv) (if opted) and create vector embeddings for the same.
    * Store table metadata embeddings and known good sql embeddings to the vector data store.
1. backend.tf - Creates firstore database and cloud run service with dummy container image.
1. frontend.tf - Responsible for creating the below resources.
    * Updates firebase.json
    * Creates firebase web app
    * Imports config data about the web app.
    * Updates [constants.ts](../frontend/src/assets/constants.ts) with relevant values from web app's config.
1. outputs.tf - Contains the important details about the resources that will be deployed. Example: instance name, ip address etc, cloud run url. This will be printed out on the console when the terraform executes successfully.
1. variables.tf - Contains the list of variables, their default values and descriptions.
1. terraform.tfvars - Can be used to override default values in variables.tf

#### Scripts
1. [deploy-all.sh](scripts/deploy-all.sh) - This shell script is used for one-click deployment. this executes the terraform scripts as well as the gcloud commands for deploying latest cloud build images for backend and frontend
1. [install-dependencies.sh](scripts/install-dependencies.sh) - This script installs poetry module which is used to manage the dependencies required for the application. This shell script is used within the terraform script [embeddings-setup.tf](embeddings-setup.tf)
1. [create-and-store-embeddings.py](scripts/create-and-store-embeddings.py) - This is a python file that executes the relevant functions to create and store vector embeddings
1. [execute-python-files.sh](scripts/execute-python-files.sh) - This shell script is used within the terraform script [embeddings-setup.tf](embeddings-setup.tf) to execute the [create-and-store-embeddings.py](scripts/create-and-store-embeddings.py)
1. [execute-gcloud-cmd.sh](scripts/execute-gcloud-cmd.sh) - This shell script can overwrite an org policy or delete the over-written rule based on the input parameters.
1. [copy-firebase-json.sh](scripts/copy-firebase-json.sh) - This script is used to overwrite firebase.json file with the information required by the application. This is information is copied from [firebase_setup.json](../frontend/firebase_setup.json)
1. [backend-deployment.sh](scripts/backend-deployment.sh) - This shell script updates the cloud run service created by terraform, with the latest code.
1. [frontend-deployment.sh](scripts/frontend-deployment.sh) - This shell script submits the latest build for the frontent code.

#### Template Files
1. [config.ini.tftpl](./templates/config.ini.tftpl) - This template is used to populate [config.ini](../config.ini) with corresponding values from variables.tf or terraform.tfvars. This file is populated via [embeddings-setup.tf](embeddings-setup.tf).
1. [constants.ts.tftpl](./templates/constants.ts.tftpl) - This template is used to populate [constants.ts](../frontend/src/assets/constants.ts). This file is populated via [frontend.tf](frontend.tf)

## Step 0: Prerequisites

Prior to executing terraform, ensure that the below mentioned steps have been completed.

#### Data Sources Set Up

1. Source data should already be available. If you do not have readily available source data, use the notebooks [0_CopyDataToBigQuery.ipynb](../notebooks/0_CopyDataToBigQuery.ipynb) or [0_CopyDataToCloudSqlPG.ipynb](../notebooks/0_CopyDataToCloudSqlPG.ipynb) based on the preferred source to populate sample data.
2. Ensure that the [data_source_list.csv](../scripts/data_source_list.csv) is populated with the list of datasources to be used in this solution. Terraform will take care of creating the embeddings in the destination. Use [data_source_list_sample.csv](../scripts/data_source_list_sample.csv) to fill the [data_source_list.csv](../scripts/data_source_list.csv)
3. If you want to use known good sqls for few shot prompting, ensure that the [known_good_sql.csv](../scripts/known_good_sql.csv) is populated with the required data. Terraform will take care of creating the embeddings in the destination.

#### Enable Firebase
Firebase will be used to host the frontend of the application.

1. Go to https://console.firebase.google.com/
1. Select add project and load your Google Cloud Platform project
1. Add Firebase to one of your existing Google Cloud projects
1. Confirm Firebase billing plan
1. Continue and complete

#### (Optional) Local configuration
If you are running this outside Cloud Shell you need to set up your Google Cloud SDK Credentials

```shell
gcloud config set project <your_project_id>
gcloud auth application-default set-quota-project <your_project_id>
```

#### Terraform deployment
> [!NOTE]  
> Terraform apply command for this application uses gcloud config to fetch & pass the set project id to the scripts. Please ensure that gcloud config has been set to your intended project id before proceeding.

1. Install [terraform 1.7 or higher](https://developer.hashicorp.com/terraform/install).
1. [OPTIONAL] Update default values of variables in [variables.tf](variables.tf) according to your preferences. You can find the description for each variable inside the file. This file will be used by terraform to get information about the resources it needs to deploy. If you do not update these, terraform will use the already specified default values in the file.
1. Move to the terraform directory in the terminal: ```Open_Data_QnA/terraform```.
1. There are 2 ways to deploy this application: 
    * **[One-click deployment](#step-1-one-click-deployment)** : Use this method when you want to do a single click deployment i.e execute terraform and shell scripts for frontend & backend services deployment all at once.
    * **[Step by step deployment](#step-1-step-by-step-deployment)**: Use this method if you want to deploy teraaform resources, frontend and backend services separately after manual validation of configuration files.

> [!IMPORTANT]  
> The Terraform scripts require specific IAM permissions to function correctly. The user needs either the broad `roles/resourcemanager.projectIamAdmin` role or a custom role with tailored permissions to manage IAM policies and roles.
> Additionally, one script TEMPORARILY disables Domain Restricted Sharing Org Policies to enable the creation of a public endpoint. This requires the user to also have the `roles/orgpolicy.policyAdmin` role.

## Step 1: One-Click Deployment
### Deployment command and script overview
```sh
sh ./scripts/deploy-all.sh
```
This script will perform the following steps:
1. **Run terraform scripts** - These terraform scripts will generate all the GCP resources and configurations files required for the frontend & backend. It will also generate embeddings and store it in the destination vector db.
1. **Deploy cloud run backend service with latest backend code** - The terraform in the previous step uses a dummy container image to deploy the initial version of cloud run service. This is the step where the actual backend code gets deployed.
1. **Deploy frontend app** - All the config files, web app etc required to create the frontend are deployed via terraform. However, the actual UI deployment takes place in this step.

### After deployment
***Auth Provider***

You need to enable at least one authentication provider in Firebase, you can enable it using the following steps:
1. Go to https://console.firebase.google.com/project/your_project_id/authentication/providers (change the `your_project_id` value)
2. Click on Get Started (if needed)
3. Select Google and enable it
4. Set the name for the project and support email for project
5. Save

## Step 1: Step by step Deployment
#### Start Terraform deployment

```sh
terraform init
terraform apply -var=project_id=$(gcloud config get project)
```

This terraform will generate all configurations files required in the frontend and backend_apis. It will also generate embeddings and store it in the destination vector db

#### After Terraform deployment
***Auth Provider***

You need to enable at least one authentication provider in Firebase, you can enable it using the following steps:
1. Go to https://console.firebase.google.com/project/your_project_id/authentication/providers (change the `your_project_id` value)
2. Click on Get Started (if needed)
3. Select Google and enable it
4. Set the name for the project and support email for project
5. Save

#### Validate the config files
This deployment uses the templates in the [templates/](templates/) directory to replace all necessary configuration values for the application. Before deploying the application check that all the values have been populated correctly in the [config.ini](../config.ini) file and [constants.ts](../frontend/src/assets/constants.ts) file.

#### Application deployment
To deploy the backend cloud run service for the application, run the following command. You will find all the needed values from terraform output. Expected working directory : ```Open_Data_QnA/terraform``` 
```
sh scripts/backend-deployment.sh --servicename <cloudrun_service_name> --project <your_project_id> --region <region> --sa <your_cloud_run_sa>
```
To deploy the frontent of the application, you need to execute the below command:
```
sh scripts/frontend-deployment.sh --project <your_project_id> --region <region>
```

## Step 2: Review your environment
Once deployment is completed the scripts (terraform & shell scripts) will output relevant resource values.

Resulting example outputs:
```sh
instance_name = "pg15-opendataqna-2"
postgres_db = "opendataqna-db-2"
public_ip_address = "XX.XXX.XXX.XXX"
service_account = "opendataqna@your-project-id.iam.gserviceaccount.com"
service_name = "opendataqna-v2"
service_url = "https://opendataqna-xxxxxxxx.a.run.app"
```
Your url to access the frontend is usually in this format: "https://your-project-id.web.app"

## Deployed resources
This deployment creates all the resources described in the main [README.md](../README.md) file, the following is a list of the created resources:
1. Enable Google Cloud Service APIs. List can be found in [locals.tf](locals.tf)
2. [BiqQuery](https://console.cloud.google.com/bigquery) Dataset and tables:
    - **1 Dataset**: where the log table and embedding tables will be created.
    - **Tables**:
        - **Audit Log table**: This table will store all application logs
        - **Table Metadata Embeddings table**: Created only when Bigquery is chosen as the vector db. This will contain all table meta data and its text embeddings. 
        - **Column Embeddings table**: Created only when Bigquery is chosen as the vector db. This will contain all column meta data and its text embeddings.
        - **Example SQL table**: Created only when Bigquery is chosen as the vector db and marked kgq_examples='yes' in tfvars. This contains all the known good sqls and their respective text embeddings. You need to populate the [known_good_sql.csv](../scripts/known_good_sql.csv) before deployment. Terraform will take care of creation of embeddings in the destination.
3. **CloudSQL instance**: Created if cloudsql-pgvector is chosen as the vector store.
4. **pg-vector database**: Created if cloudsql-pgvector is chosen as the vector store. This database will store all text embeddings.
    - **Tables**:
        - **Table Metadata Embeddings table**: Created only when cloudsql-pgvector is chosen as the vector db. This will contain all table meta data and its text embeddings.
        - **Column Embeddings table**: Created only when cloudsql-pgvector is chosen as the vector db. This will contain all column meta data and its text embeddings.
        - **Example SQL table**: Created only when cloudsql-pgvector is chosen as the vector db and marked kgq_examples='yes' in tfvars. This contains all the known good sqls and their respective text embeddings.
> [!NOTE]  
> The above mentioned tables in **CloudSQL & BigQuery** are created via the python script [create-and-store-embeddings.py](scripts/create-and-store-embeddings.py)


> [!IMPORTANT]  
> If you have an existing CloudSQL instance that you want to use for storing vector embeddings, then update the variable - **use_existing_cloudsql_instance = "yes"**. Terraform will not create any new cloudsql instance, database or user name & password. It will be assumed that these resources already exist.

5. A backend service account for cloud run service with the required permissions
6. All embedding tables will be populated via terraform.
7. [Cloud Run](https://console.cloud.google.com/run) for backend APIs
8. A Firestore database for storing chat history
9. Firebase web app for hosting frontend.

## Troubleshooting Known Issues
1. #### `pipx: command not found`
    * This error will be caused by execution of [install-dependencies.sh](./scripts/install-dependencies.sh) file.
    * The error indicates that even though you've installed pipx, your shell isn't aware of its location. This usually means the directory where pipx is installed hasn't been added to your system's PATH environment variable.
    * Resolution:
        1. We have already tried to ensure that pipx gets added to PATH via execution of the command `export PATH="$PATH:$(python3 -c "import sysconfig; print(sysconfig.get_paths()['scripts'])")"` in the [install-dependencies.sh](./scripts/install-dependencies.sh) file. This command is specifically designed to return the path to the global site-packages directory (where system-wide packages are installed) and add to PATH temporarily. However, This command might not be giving you the correct directory where pipx is installed.
        2. If you encounter this error, you can try replacing the above command with `export PATH="$PATH:$(python3 -m site --user-base)/bin"`. This command is specifically designed to return the path to the user-specific site-packages directory and add to PATH temporarily.
        3. If the above step also fails, you will need to manually find the PATH where pipx is installed. Once you know the location, just replace `export PATH="$PATH:$(python3 -c "import sysconfig; print(sysconfig.get_paths()['scripts'])")"` inside [install-dependencies.sh](./scripts/install-dependencies.sh) with `export PATH="$PATH:/path/to/pipx/directory"`. Replace `/path/to/pipx/directory` with the actual path you found.

1. #### `poetry: command not found`
    * This error will be caused by execution of [install-dependencies.sh](./scripts/install-dependencies.sh) file.
    * The error indicates that even though you've installed poetry, your shell isn't aware of its location. This usually means the directory where pipx is installed hasn't been added to your system's PATH environment variable.
    * Resolution:
        1. Although we have ensured that poetry will automatically get added to PATH via commands `pipx ensurepath` and `source ~/.bashrc` in the [install-dependencies.sh](./scripts/install-dependencies.sh) file, if the script still fails with this error, you need to manually find the path where poetry is installed.
        2. Add the new PATH to `~/.bashrc` file and source it before re-running the script again. 

1. #### `aiohttp.client_exceptions.ClientConnectorCertificateError`
    * `aiohttp.client_exceptions.ClientConnectorCertificateError: Cannot connect to host sqladmin.googleapis.com:443 ssl:True [SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1006)')]`
    * SSL/TLS and Certificates: Secure connections over the internet (HTTPS) rely on SSL/TLS protocols. These protocols use digital certificates to verify the identity of the server you're connecting to. Your system needs a set of trusted root certificates to validate these server certificates.
    * Missing Root Certificates: If your system lacks the necessary root certificates or they are outdated, it can't establish trust with the server, leading to the CERTIFICATE_VERIFY_FAILED error.
    * Resolution:
        1. Install or Update certifi - certifi is a package that provides a curated collection of Root Certificates for validating the trustworthiness of SSL certificates while making secure network requests.
        Install or update it using pip:
        ```
        pip install --upgrade certifi
        ```
        2. Set the SSL_CERT_FILE environment variable
        Tell your Python environment to use the certificates provided by certifi:
        ```
        export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
        ```
        This command finds the location of the certificate file provided by certifi and sets the SSL_CERT_FILE environment variable to that path.
        
        3. Retry your code.

1. #### `Firebase project not found`
    * `Error creating WebApp: googleapi: Error 404: Firebase project XXXXXXXXX not found.`
    * This error is encountered when you fail to add firebase to your project before execution of the scripts.
    * Follow the instructions for [enabling firebase](#enable-firebase) under [pre-requisites](#prerequisites) section of the README

1. #### `Error: Provider produced inconsistent result after apply`
    * Sometimes, when Terraform creates or updates a resource on your cloud provider, there can be a slight delay before that change is fully reflected in the provider's system. This can cause Terraform to see an inconsistency between what it expects and what the provider reports, leading to an error.
    * As a result, you might encounter an error message if Terraform attempts to read information about a newly created or updated resource before the provider's system has fully processed the change.
    * Solutions:
        1. **Manual Deletion and Retry**: Delete the problematic resource directly on the remote system and re-run terraform apply.
        2. **Terraform Import**: Use `terraform import` to synchronize the resource's state from the remote system into your Terraform state file, then re-run `terraform apply`. Follow the [How to Import Resources into a Remote State Managed by Terraform Cloud](https://support.hashicorp.com/hc/en-us/articles/360061289934-How-to-Import-Resources-into-a-Remote-State-Managed-by-Terraform-Cloud) for detailed steps.


