from src.database.database_connection import DatabaseConnection


class SchemaManager:
    """
    Creates and manages the AnalystGPT Enterprise database schema.
    Uses dialect-specific helpers to generate SQL for SQLite or PostgreSQL.
    """

    def __init__(self, database_connection: DatabaseConnection):
        self._database_connection = database_connection
        self._database_type = database_connection.database_type()

    # ---------------------------------------------------------

    def initialize_schema(self):
        """
        Create all required database tables.
        """

        supported = {
            "sqlite",
            "postgresql",
        }

        if self._database_type not in supported:
            raise ValueError(
                f"Unsupported database type: {self._database_type}"
            )

        self._create_schema()

    # ---------------------------------------------------------

    def _primary_key_sql(self) -> str:

        if self._database_type == "sqlite":
            return "INTEGER PRIMARY KEY AUTOINCREMENT"

        return "SERIAL PRIMARY KEY"

    # ---------------------------------------------------------

    def _timestamp_sql(self) -> str:

        if self._database_type == "sqlite":
            return "TEXT"

        return "TIMESTAMP WITH TIME ZONE"

    # ---------------------------------------------------------

    def _float_sql(self) -> str:

        if self._database_type == "sqlite":
            return "REAL"

        return "DOUBLE PRECISION"

    # ---------------------------------------------------------

    def _create_schema(self):

        connection = self._database_connection.get_connection()

        cursor = connection.cursor()

        try:

            pk = self._primary_key_sql()
            ts = self._timestamp_sql()
            float_type = self._float_sql()

            if self._database_type == "sqlite":
                cursor.execute(
                    "PRAGMA foreign_keys = ON;"
                )

            # -------------------------------------------------
            # Users (Sprint 13 Identity Foundation)
            # -------------------------------------------------

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS users(
                    id {pk},
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'ANALYST',
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_at {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # -------------------------------------------------
            # Pipeline Runs
            # -------------------------------------------------

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS pipeline_runs(
                    id {pk},
                    user_id INTEGER,
                    execution_time {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE SET NULL
                );
                """
            )

            # -------------------------------------------------
            # Datasets
            # -------------------------------------------------

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS datasets(
                    id {pk},
                    pipeline_run_id INTEGER NOT NULL,
                    user_id INTEGER,
                    dataset_name TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    column_count INTEGER NOT NULL,
                    FOREIGN KEY (pipeline_run_id)
                        REFERENCES pipeline_runs(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE SET NULL
                );
                """
            )

            # -------------------------------------------------
            # Quality Reports
            # -------------------------------------------------

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS quality_reports(
                    id {pk},
                    pipeline_run_id INTEGER NOT NULL,
                    completeness {float_type},
                    validity {float_type},
                    consistency {float_type},
                    uniqueness_score {float_type},
                    FOREIGN KEY (pipeline_run_id)
                        REFERENCES pipeline_runs(id)
                        ON DELETE CASCADE
                );
                """
            )

            # -------------------------------------------------
            # Analytics Reports
            # -------------------------------------------------

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS analytics_reports(
                    id {pk},
                    pipeline_run_id INTEGER NOT NULL,
                    total_numeric_columns INTEGER,
                    total_categorical_columns INTEGER,
                    correlation_summary TEXT,
                    FOREIGN KEY (pipeline_run_id)
                        REFERENCES pipeline_runs(id)
                        ON DELETE CASCADE
                );
                """
            )

            # -------------------------------------------------
            # Reports
            # -------------------------------------------------

            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS reports(
                    id {pk},
                    pipeline_run_id INTEGER NOT NULL,
                    user_id INTEGER,
                    report_path TEXT NOT NULL,
                    generated_time {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pipeline_run_id)
                        REFERENCES pipeline_runs(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE SET NULL
                );
                """
            )

            # -------------------------------------------------
            # Column Migrations (Sprint 13 Multi-User Upgrade)
            # -------------------------------------------------

            for table_name in ["pipeline_runs", "datasets", "reports"]:
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN user_id INTEGER;")
                    self._database_connection.commit()
                except Exception:
                    self._database_connection.rollback()

            # -------------------------------------------------
            # Performance Indexes (Sprint 13 Phase 3)
            # -------------------------------------------------

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_runs_user_id ON pipeline_runs(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON datasets(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_datasets_pipeline_run_id ON datasets(pipeline_run_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_pipeline_run_id ON reports(pipeline_run_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_reports_pipeline_run_id ON quality_reports(pipeline_run_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_reports_pipeline_run_id ON analytics_reports(pipeline_run_id);")

            self._database_connection.commit()

        except Exception:

            self._database_connection.rollback()

            raise

        finally:

            cursor.close()