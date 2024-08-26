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

resource "local_file" "config_ini" {
  content = templatefile("${path.module}/templates/config.ini.tftpl", {
    embedding_model        = var.embedding_model,
    description_model      = var.description_model,
    vector_store           = var.vector_store,
    debugging              = var.debugging,
    logging                = var.logging,
    kgq_examples           = var.kgq_examples,
    firestore_region       = var.firestore_region,
    use_column_samples     = var.use_column_samples,
    project_id             = var.project_id,
    pg_region              = var.pg_region,
    pg_instance            = var.pg_instance,
    pg_database            = var.pg_database,
    pg_user                = var.pg_user
    pg_password            = var.pg_password
    bq_dataset_region      = var.bq_dataset_region
    bq_opendataqna_dataset = var.bq_opendataqna_dataset
    bq_log_table           = var.bq_log_table
    }
  )
  filename = "../config.ini"
}

resource "null_resource" "install_dependencies" {
  # depends_on = [local_file.config_ini]
  triggers = {
    always_run = "${timestamp()}"
  }
  provisioner "local-exec" {
    
    working_dir = "${path.module}"
    command = "sh ${path.module}/scripts/install-dependencies.sh"
  }
}

resource "null_resource" "create_and_store_embeddings" {
  depends_on = [local_file.config_ini, null_resource.install_dependencies,module.bigquery, google_sql_database_instance.pg15_opendataqna[0]]
  triggers = {
    always_run = "${timestamp()}"
  }
  provisioner "local-exec" {
    
    working_dir = "${path.module}"
    command = "sh ${path.module}/scripts/execute-python-files.sh './scripts'"
  }
}