resource "google_firestore_database" "chathistory_db" {
  project     = var.project_id
  name        = "opendataqna-session-logs"
  location_id = var.firestore_region
  type        = "FIRESTORE_NATIVE"
  depends_on  = [ module.project_services ]
}

resource "google_cloud_run_service" "backend" {
  name     = var.cloud_run_service_name
  location = var.deploy_region
  project  = var.project_id

  template {
    spec {
      containers {
        image = "us-docker.pkg.dev/cloudrun/container/hello"
      }
      service_account_name = module.genai_cloudrun_service_account.email
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [ module.project_services,null_resource.org_policy_temp, module.genai_cloudrun_service_account, local_file.config_ini,]
}
