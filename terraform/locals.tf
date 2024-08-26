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

locals {
  services = [
    "cloudapis.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "aiplatform.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "firebase.googleapis.com",
    "firebasehosting.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudbuild.googleapis.com",
    "firestore.googleapis.com"
  ]

  # tables = [
  #   {
  #     name   = var.bq_log_table,
  #     schema = "${path.module}/bq-schemas/audit_log_table.json"
  #   },
  #   {
  #     name   = "table_details_embeddings",
  #     schema = "${path.module}/bq-schemas/table_details_embeddings.json"
  #   },
  #   {
  #     name   = "tablecolumn_details_embeddings",
  #     schema = "${path.module}/bq-schemas/tablecolumn_details_embeddings.json"
  #   },
  #   {
  #     name   = "example_prompt_sql_embeddings",
  #     schema = "${path.module}/bq-schemas/example_prompt_sql_embeddings.json"
  #   }
  # ]

  # bq_tables = [for t in local.tables : {
  #   table_id           = t.name,
  #   schema             = file(t.schema),
  #   time_partitioning  = null,
  #   range_partitioning = null,
  #   expiration_time    = null,
  #   clustering         = [],
  #   labels             = {},
  # } if var.vector_store=="bigquery-vector" || t.name == var.bq_log_table]  
}