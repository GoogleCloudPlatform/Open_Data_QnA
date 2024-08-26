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

resource "null_resource" "org_policy_temp" {
  depends_on = [module.project_services]

  provisioner "local-exec" {
    
    working_dir = "${path.module}"
    command = "sh ${path.module}/scripts/execute-gcloud-cmd.sh ${var.project_id} YES"
  }
}

resource "null_resource" "delete_org_policy_temp" {
  provisioner "local-exec" {
    working_dir = "${path.module}"
    command = "sh ${path.module}/scripts/execute-gcloud-cmd.sh ${var.project_id} NO"
  }

  depends_on = [module.project_services, null_resource.org_policy_temp, google_cloud_run_service.backend ]
}

module "genai_cloudrun_service_account" {
  source     = "terraform-google-modules/service-accounts/google"
  version    = "~> 4.0"
  project_id = var.project_id
  names      = [var.service_account]
  project_roles = [
    "${var.project_id}=>roles/cloudsql.client",
    "${var.project_id}=>roles/bigquery.admin",
    "${var.project_id}=>roles/aiplatform.user",
    "${var.project_id}=>roles/datastore.owner"
  ]
  depends_on = [module.project_services]
}


resource "google_project_iam_member" "default_ce_sa_role" {
  for_each = toset([
    "roles/storage.admin",
    "roles/artifactregistry.admin",
    "roles/firebase.admin",
    "roles/cloudbuild.builds.builder",
    "roles/logging.logWriter"
  ])
  role = each.key
  member = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  project = var.project_id
  depends_on = [module.project_services]
}

resource "google_project_iam_member" "default_cloudbuild_sa_role" {
  for_each = toset([
    "roles/firebase.admin",
    "roles/artifactregistry.admin",
    "roles/serviceusage.apiKeysAdmin",
    "roles/cloudbuild.builds.builder"
  ])
  role = each.key
  member = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  project = var.project_id
  depends_on = [module.project_services]
}

resource "google_cloud_run_service_iam_member" "invoker" {
  location = google_cloud_run_service.backend.location
  project  = google_cloud_run_service.backend.project
  service  = google_cloud_run_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
  depends_on = [ google_cloud_run_service.backend ]
}
