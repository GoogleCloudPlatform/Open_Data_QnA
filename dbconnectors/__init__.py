from .core import DBConnector
from .PgConnector import PgConnector, pg_specific_data_types
from .BQConnector import BQConnector, bq_specific_data_types
from .FirestoreConnector import FirestoreConnector
from .SpannerConnector import SpannerConnector, spanner_specific_data_types
from utilities import (PROJECT_ID,
                       PG_INSTANCE, PG_DATABASE, PG_USER, PG_PASSWORD, PG_REGION,BQ_REGION,
                       BQ_OPENDATAQNA_DATASET_NAME,BQ_LOG_TABLE_NAME,
                       SPANNER_INSTANCE, SPANNER_OPENDATAQNA_DATABASE)

pgconnector = PgConnector(PROJECT_ID, PG_REGION, PG_INSTANCE, PG_DATABASE, PG_USER, PG_PASSWORD)
bqconnector = BQConnector(PROJECT_ID,BQ_REGION,BQ_OPENDATAQNA_DATASET_NAME,BQ_LOG_TABLE_NAME)
firestoreconnector = FirestoreConnector(PROJECT_ID,"opendataqna-session-logs")
spannerconnector = SpannerConnector(PROJECT_ID, SPANNER_INSTANCE, SPANNER_OPENDATAQNA_DATABASE)

__all__ = ["pgconnector", "pg_specific_data_types", "bqconnector","firestoreconnector"]