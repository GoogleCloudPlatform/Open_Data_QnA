# resource "google_project" "default" {
#   provider = google-beta

#   project_id = var.project_id
#   name       = data.google_project.project.name
#   org_id     = data.google_project.project.org_id

#   labels = {
#     "firebase" = "enabled"
#   }
# }

resource "google_firebase_project" "default" {
  provider = google-beta
  project  = var.project_id

  provisioner "local-exec" {
    
    working_dir = "${path.module}"
    command = "sh ${path.module}/scripts/copy-firebase-json.sh"
  }
}

resource "google_firebase_web_app" "app_frontend" {
    provider = google-beta
    project = var.project_id
    display_name = var.firebase_web_app_name
}

data "google_firebase_web_app_config" "app_frontend_config" {
  provider   = google-beta
  web_app_id = google_firebase_web_app.app_frontend.app_id
  project = var.project_id
}

resource "local_file" "constants_ts" {
  depends_on = [ google_firebase_web_app.app_frontend, google_cloud_run_service.backend ]
  content = templatefile("${path.module}/templates/constants.ts.tftpl", {
    projectId         = var.project_id
    appId             = google_firebase_web_app.app_frontend.app_id
    apiKey            = data.google_firebase_web_app_config.app_frontend_config.api_key
    authDomain        = data.google_firebase_web_app_config.app_frontend_config.auth_domain
    storageBucket     = lookup(data.google_firebase_web_app_config.app_frontend_config, "storage_bucket", "")
    messagingSenderId = lookup(data.google_firebase_web_app_config.app_frontend_config, "messaging_sender_id", "")
    # measurementId     = lookup(data.google_firebase_web_app_config.app_frontend_config, "measurement_id", ""),
    endpoint_opendataqna    = google_cloud_run_service.backend.status[0].url
    }
  )
  filename = "../frontend/src/assets/constants.ts"
}


