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

module "bigquery" {
  source                      = "terraform-google-modules/bigquery/google"
  version                     = "~> 7.0"
  dataset_id                  = var.bq_opendataqna_dataset
  dataset_name                = var.bq_opendataqna_dataset
  project_id                  = var.project_id
  location                    = var.bq_dataset_region
  default_table_expiration_ms = null

  tables     = local.bq_tables
  depends_on = [module.project_services]
}