/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

variable "project_id" {
  type = string
}

variable "embedding_model" {
  type = string
  default = "vertex"
  description = "name of the model that you want to use to create embeddings. Options: 'vertex' or 'vertex-lang'"
}

variable "description_model" {
  type = string
  default = "gemini-1.5-pro"
  description = "name of the model that you want to use to generate missing description for tables and columns. Options: 'gemini-1.0-pro', 'gemini-1.5-pro', 'text-bison-32k', 'gemini-1.5-flash'"
}

variable "vector_store" {
  type = string
  default = "bigquery-vector"
  description = "name of the datastore you want to use to store text embeddings of your meta data. Options: bigquery-vector, cloudsql-pgvector"
}

variable "debugging" {
  type = string
  default = "yes"
  description = "yes, if you want to enable debugging. No, otherwise"
}

variable "logging" {
  type = string
  default = "yes"
  description = "yes, if you want to enable application logging. No, otherwise"
}

variable "kgq_examples" {
  type = string
  default = "yes"
  description = "yes, if you want to use known good sqls for few shot prompting and creating cache. No, otherwise"
}

variable "use_column_samples" {
  type = string
  default = "no"
  description = "yes, if you want to add some sample column values to the embeddings to enrich it with more information. No, otherwise"
}

variable "use_existing_cloudsql_instance" {
  default = "no"
  type    = string
  description = "If you want to use an existing cloudsql instance to store the vector embeddings, then choose 'yes' else choose 'no'. Terraform will create a new cloudsql instance if 'no' is chosen."
}

variable "pg_instance" {
  default     = "pg15-opendataqna"
  type        = string
  description = "Name of the Cloudsql postgres instance to store vector embeddings. Keep this empty if vector db is bigquery."
}

variable "pg_region" {
  default     = "us-central1"
  type        = string
  description = "Location of the pg_instance"
}


variable "pg_database" {
  type        = string
  default     = "opendataqna-db"
  description = "Name of the Database associated with pg_instance"
}

variable "pg_user" {
  type        = string
  default     = "pguser"
  description = "user name for the database"
}

variable "pg_password" {
  type        = string
  default     = "pg123"
  description = "password for pg_user"
}

variable "bq_opendataqna_dataset" {
  type        = string
  default     = "opendataqna"
  description = "This dataset will be used to store text embeddings and application logs. If pg-vector is chosen as vector db, only application logs will be stored here."
}

variable "bq_dataset_region" {
  type    = string
  default = "us-central1"
  description = "Location of bq_opendataqna_dataset."
}

variable "bq_log_table" {
  type        = string
  default     = "audit_log_table"
  description = "Name of the table where audit logs will be stored. This table will be create under the bq_opendataqna_dataset."
}

variable "spanner_instance" {
  default     = "spanner-opendataqna"
  type        = string
  description = "Name of the Cloud Spanner instance to store vector embeddings. Keep this empty if vector db is bigquery/postgres."
}

variable "spanner_region" {
  default     = "us-central1"
  type        = string
  description = "Location of the spanner_instance"
}

variable "spanner_database" {
  type        = string
  default     = "opendataqna-db"
  description = "Name of the Database associated with spanner_instance"
}

variable "firestore_region" {
  type        = string
  default     = "us-central1"
  description = "Location of the firestore database."
}

variable service_account {
  type = string
  default = "opendataqna"
  description = "service account used by backend service"
}

variable "deploy_region" {
  
  type = string
  default = "us-central1"
  description = "region where cloudrun service will be deployed"
}

variable "cloud_run_service_name" {
  type = string
  default = "opendataqna"
  description = "name of the cloud run service where backend apis will be deployed"
}

variable "firebase_web_app_name" {
  type = string
  default = "opendataqna"
  description = "name of the firebase web app."
}

