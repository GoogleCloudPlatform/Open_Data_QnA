
# Infrastructure deployment
Terraform deployment simplifies the deployment of this solution and can be used as blueprint of the solution. The terraform script acts a one-time single click deployment solution. This does not offer CI / CD capabilites and should be should be solely used for the purpose of a one time single click deployment.

*Note*: Current version of the Terraform Google Cloud provider does not support deployment of a few resources, this soultion uses null_resource to create those resources using Google Cloud SDK.

## Prerequisites:

Prior to executing terraform, perform the below step:

1. Source data should already be available. If you do not have readily available source data, use the notebooks [0_CopyDataToBigQuery.ipynb](../notebooks/0_CopyDataToBigQuery.ipynb) or [0_CopyDataToCloudSqlPG.ipynb](../notebooks/0_CopyDataToCloudSqlPG.ipynb) based on the preferred source.
2. Ensure that the [data_source_list.csv](../scripts/data_source_list.csv) is populated with the list of datasources to be used in this solution. Terraform will take care of populating the data and creation of embeddings in the destination. Use [data_source_list_sample.csv](../scripts/data_source_list_sample.csv) to fill the data_source_list.csv
3. If you want to use known good sqls for few shot prompting, ensure that the [known_good_sql.csv](../scripts/known_good_sql.csv) is populated with the required data. Terraform will take care of populating the data and creation of embeddings in the destination.
2. Install terraform 1.7 or higher.

### (Optional) Local configuration
If you are running this outside Cloud Shell you need to set up your Google Cloud SDK Credentials

```shell
gcloud config set project <your_project_id>
gcloud auth application-default set-quota-project <your_project_id>
```

## Terraform deployment

1. [OPTIONAL] Update default values of variables in [variables.tf] according to your preferences. You can find the description for each variable inside the file. This file will be used by terraform to get information about the resources it needs to deploy. If you do not update these, terraform will use the already specified default values in the file.
2. Move to the terraform directory: ```Open_Data_QnA/infra``` 
3. Run the following commands:

*Note*: This deployment requires Terraform 1.7 or higher

Start the terraform deployment
```sh
terraform init
terraform apply -var=project_id=$(gcloud config get project)
```

This terraform will generate all configurations files required in the frontend and backend_apis. It will also generate embeddings and store it in the destination vector db

### After Terraform deployment
***Auth Provider***

You need to enable at least one authentication provider in Firebase, you can enable it using the following steps:
1. Go to https://console.firebase.google.com/project/your_project_id/authentication/providers (change the `your_project_id` value)
2. Click on Get Started (if needed)
3. Select Google and enable it
4. Set the name for the project and support email for project
5. Save

#### Validate the config files
This deployment uses the templates in the [templates/](templates/) diractory to replace all necessary configuration values for the application. Before deploying the application check that all the values have been populated correctly in the [config.ini](../config.ini) file and [constants.ts](../frontend/src/assets/constants.ts) file.

## Application deployment
To deploy the backend cloud run service for the application, run the following command. You will find all the needed values from terraform output. Expected working directory : ```Open_Data_QnA/infra``` 
```
sh scripts/backend-deployment.sh --servicename <cloudrun_service_name> --project <your_project_id> --region <region> --sa <your_cloud_run_sa>
```
To deploy the frontent of the application, you need to execute the below command:
```
sh scripts/frontend_deployment.sh --project <your_project_id>
```

## Review your environment
Once deployment is completed terraform will output relevant resource values.

Resulting example outputs:
```sh
backend_deployment = "https://opendataqna-xxxxxxxx.a.run.app"
backend_service_account = "opendataqna@your-project-id.iam.gserviceaccount.com"
frontend_deployment = "https://your-project-id.web.app"
```
You can use the app by accessing to the frontend_deployment URL.

### Deployed resources
This deployment creates all the resources described in the main [README.md](../README.md) file, the following is a list of the created resources:
- Required Google Cloud services
- [BiqQuery](https://console.cloud.google.com/bigquery) Dataset and tables:
    - 1 Dataset: where the log table and embedding tables (if chosen as vector db) will be created.
    - Tables:
        - Audit Log table: This table will store all application logs
        - Table Metadata Embeddings table: Created only when Bigquery is chosen as the vector db. This will contain all table meta data and its text embeddings. 
        - Column Embeddings table: Created only when Bigquery is chosen as the vector db. This will contain all column meta data and its text embeddings.
        - Example SQL table: Created only when Bigquery is chosen as the vector db and marked kgq_examples='yes' in tfvars. This contains all the known good sqls and their respective text embeddings. You need to populate the [known_good_sql.csv](../scripts/known_good_sql.csv). Terraform will take care of populating the data and creation of embeddings in the destination.
- CloudSQL instance: Created if cloudsql-pgvector is chosen as the vector store.
- pg-vector database: Created if cloudsql-pgvector is chosen as the vector store. This database will store all text embeddings
    - Tables:
        - Table Metadata Embeddings table: Created only when cloudsql-pgvector is chosen as the vector db. This will contain all table meta data and its text embeddings.
        - Column Embeddings table: Created only when cloudsql-pgvector is chosen as the vector db. This will contain all column meta data and its text embeddings.
        - Example SQL table: Created only when cloudsql-pgvector is chosen as the vector db and marked kgq_examples='yes' in tfvars. This contains all the known good sqls and their respective text embeddings.
- A backend service account for cloud run service with the required permissions
- All embedding tables will be populated via terraform.
- [Cloud Run](https://console.cloud.google.com/run) for backend APIs
- A Firestore database for storing chat history
- Firebase for frontend deployment

## Know Issues

