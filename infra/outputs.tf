output "project_number" {
  value = data.google_project.project.number
}

output "instance_name" {
  value       = var.vector_store == "cloudsql-pgvector" ? google_sql_database_instance.pg15_opendataqna[0].name : null
  description = "The instance name for the master instance"
}

output "public_ip_address" {
  description = "The first public (PRIMARY) IPv4 address assigned for the master instance"
  value       = var.vector_store == "cloudsql-pgvector" ? google_sql_database_instance.pg15_opendataqna[0].public_ip_address : null
}

output "postgres_db" {
  description = "database name"
  value       = var.vector_store == "cloudsql-pgvector" ? google_sql_database.pg_db[0].name : null
}

output "sql_user" {
  description = "user name generated for the instance"
  value       = var.vector_store == "cloudsql-pgvector" ? google_sql_user.pguser[0] : null
  sensitive = true
}

output "sql_user_password" {
  description = "user name generated for the instance"
  value       = var.vector_store == "cloudsql-pgvector" ? google_sql_user.pguser[0].password : null
  sensitive   = true
}

output "service_name" {
  value       = google_cloud_run_service.backend.name
  description = "Name of the created service"
}

output "revision" {
  value       = google_cloud_run_service.backend.status[0].latest_ready_revision_name
  description = "Deployed revision for the service"
}

output "service_url" {
  value       = google_cloud_run_service.backend.status[0].url
  description = "The URL on which the deployed service is available"
}

output "firebase_appId" {
  value = google_firebase_web_app.app_frontend.app_id
}

output "firebase_apiKey" {
  value = data.google_firebase_web_app_config.app_frontend_config.api_key
}

output "firebase_authDomain" {
  value = data.google_firebase_web_app_config.app_frontend_config.auth_domain
}

output "firebase_storageBucket" {
  value = lookup(data.google_firebase_web_app_config.app_frontend_config, "storage_bucket", "")
}

output "firebase_messagingSenderId" {
  value = lookup(data.google_firebase_web_app_config.app_frontend_config, "messaging_sender_id", "")
}

output "firebase_measurementId" {
  value = lookup(data.google_firebase_web_app_config.app_frontend_config, "measurement_id", "")
}

output "hosting_url" {
  value = google_firebase_web_app.app_frontend.app_urls
}