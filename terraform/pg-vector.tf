resource "google_sql_database_instance" "pg15_opendataqna" {
  count = var.vector_store=="cloudsql-pgvector" && var.use_existing_cloudsql_instance=="no"? 1:0
  name                = var.pg_instance
  project             = var.project_id
  region              = var.pg_region
  database_version = "POSTGRES_15"
  root_password    = "abcABC123!"
  settings {
    tier = "db-custom-2-7680"
    password_validation_policy {
      min_length                  = 6
      reuse_interval              = 2
      complexity                  = "COMPLEXITY_DEFAULT"
      disallow_username_substring = true
      password_change_interval    = "30s"
      enable_password_policy      = true
    }
    # ip_configuration {
    #   authorized_networks {
    #     name  = var.pg_network_name
    #     value = var.pg_authorised_ip_range
    #   }
    #   ipv4_enabled = true
    # }
  }
  deletion_protection = false
  depends_on = [ module.project_services ]
}

resource "google_sql_database" "pg_db" {
  count = var.vector_store=="cloudsql-pgvector" && var.use_existing_cloudsql_instance=="no"? 1:0
  name            = var.pg_database
  project         = var.project_id
  instance        = google_sql_database_instance.pg15_opendataqna[count.index].name
  depends_on      = [google_sql_database_instance.pg15_opendataqna]
}

resource "google_sql_user" "pguser" {
  count = var.vector_store=="cloudsql-pgvector" && var.use_existing_cloudsql_instance=="no"? 1:0
  name     = var.pg_user
  project  = var.project_id
  instance = google_sql_database_instance.pg15_opendataqna[count.index].name
  password = var.pg_password
  depends_on = [
    google_sql_database_instance.pg15_opendataqna,
  ]
}
