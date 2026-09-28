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
            raise ValueError(f"Unsupported database type: {self._database_type}")

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
                cursor.execute("PRAGMA foreign_keys = ON;")

            # -------------------------------------------------
            # Users (Sprint 13 Identity Foundation)
            # -------------------------------------------------

            cursor.execute(f"""
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
                """)

            # -------------------------------------------------
            # Pipeline Runs
            # -------------------------------------------------

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS pipeline_runs(
                    id {pk},
                    user_id INTEGER,
                    execution_time {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE SET NULL
                );
                """)

            # -------------------------------------------------
            # Datasets
            # -------------------------------------------------

            cursor.execute(f"""
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
                """)

            # -------------------------------------------------
            # Quality Reports
            # -------------------------------------------------

            cursor.execute(f"""
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
                """)

            # -------------------------------------------------
            # Analytics Reports
            # -------------------------------------------------

            cursor.execute(f"""
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
                """)

            # -------------------------------------------------
            # Reports
            # -------------------------------------------------

            cursor.execute(f"""
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
                """)

            # -------------------------------------------------
            # AI Jobs (Sprint 14 Phase 2 Asynchronous Engine)
            # -------------------------------------------------

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS ai_jobs(
                    id {pk},
                    job_id TEXT UNIQUE NOT NULL,
                    pipeline_run_id INTEGER NOT NULL,
                    user_id INTEGER,
                    report_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    provider TEXT NOT NULL DEFAULT 'ollama',
                    model TEXT NOT NULL DEFAULT 'gemma3:4b',
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    error TEXT,
                    failure_category TEXT,
                    created_at {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    started_at {ts},
                    completed_at {ts},
                    updated_at {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pipeline_run_id)
                        REFERENCES pipeline_runs(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE SET NULL,
                    FOREIGN KEY (report_id)
                        REFERENCES reports(id)
                        ON DELETE SET NULL,
                    CONSTRAINT uq_ai_jobs_pipeline_run UNIQUE (pipeline_run_id)
                );
                """)

            # -------------------------------------------------
            # AI Reports (Sprint 14 Phase 2 Persistent Reports)
            # -------------------------------------------------

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS ai_reports(
                    id {pk},
                    job_id TEXT UNIQUE NOT NULL,
                    pipeline_run_id INTEGER NOT NULL,
                    user_id INTEGER,
                    report_id INTEGER,
                    executive_summary TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    explanations TEXT NOT NULL,
                    narrative TEXT NOT NULL,
                    model TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    execution_time {float_type} NOT NULL,
                    generated_at {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    key_findings TEXT,
                    business_implications TEXT,
                    risks TEXT,
                    opportunities TEXT,
                    actions TEXT,
                    limitations TEXT,
                    confidence TEXT,
                    structured_payload TEXT,
                    FOREIGN KEY (job_id)
                        REFERENCES ai_jobs(job_id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (pipeline_run_id)
                        REFERENCES pipeline_runs(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE SET NULL,
                    FOREIGN KEY (report_id)
                        REFERENCES reports(id)
                        ON DELETE SET NULL,
                    CONSTRAINT uq_ai_reports_pipeline_run UNIQUE (pipeline_run_id)
                );
                """)

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
            # Dataset Versions (Sprint 14 Phase 3 Governance)
            # -------------------------------------------------

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS dataset_versions(
                    id {pk},
                    version_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    source_filename TEXT NOT NULL,
                    content_type TEXT NOT NULL DEFAULT 'text/csv',
                    byte_size INTEGER NOT NULL DEFAULT 0,
                    checksum_sha256 TEXT NOT NULL,
                    row_count INTEGER NOT NULL DEFAULT 0,
                    column_count INTEGER NOT NULL DEFAULT 0,
                    is_source INTEGER NOT NULL DEFAULT 1,
                    parent_version_id TEXT,
                    storage_path TEXT NOT NULL,
                    schema_json TEXT,
                    created_at {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE SET NULL,
                    FOREIGN KEY (parent_version_id)
                        REFERENCES dataset_versions(version_id)
                        ON DELETE RESTRICT
                );
                """)

            # -------------------------------------------------
            # Cleaning Configurations (Sprint 14 Phase 3 Governance)
            # -------------------------------------------------

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS cleaning_configs(
                    id {pk},
                    config_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    missing_value_policy TEXT NOT NULL DEFAULT 'DROP_ROWS',
                    null_threshold {float_type},
                    fill_value TEXT,
                    affected_columns TEXT,
                    custom_strategy_name TEXT,
                    custom_params_json TEXT,
                    config_version INTEGER NOT NULL DEFAULT 1,
                    created_at {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE SET NULL
                );
                """)

            # -------------------------------------------------
            # Cleaning Executions (Sprint 14 Phase 3 Governance)
            # -------------------------------------------------

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS cleaning_executions(
                    id {pk},
                    execution_id TEXT UNIQUE NOT NULL,
                    pipeline_run_id INTEGER,
                    user_id INTEGER,
                    source_version_id TEXT NOT NULL,
                    cleaned_version_id TEXT,
                    config_id TEXT NOT NULL,
                    execution_status TEXT NOT NULL DEFAULT 'SUCCESS',
                    error_message TEXT,
                    source_row_count INTEGER NOT NULL DEFAULT 0,
                    cleaned_row_count INTEGER,
                    rows_removed INTEGER,
                    pct_rows_removed {float_type},
                    source_missing_count INTEGER,
                    cleaned_missing_count INTEGER,
                    source_completeness_pct {float_type},
                    cleaned_completeness_pct {float_type},
                    columns_removed TEXT,
                    affected_columns_detail TEXT,
                    execution_time_seconds {float_type},
                    executed_at {ts} NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pipeline_run_id)
                        REFERENCES pipeline_runs(id)
                        ON DELETE SET NULL,
                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE SET NULL,
                    FOREIGN KEY (source_version_id)
                        REFERENCES dataset_versions(version_id)
                        ON DELETE RESTRICT,
                    FOREIGN KEY (cleaned_version_id)
                        REFERENCES dataset_versions(version_id)
                        ON DELETE SET NULL,
                    FOREIGN KEY (config_id)
                        REFERENCES cleaning_configs(config_id)
                        ON DELETE RESTRICT
                );
                """)

            # -------------------------------------------------
            # Performance Indexes (Sprint 13 & Sprint 14 Phase 2)
            # -------------------------------------------------

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_runs_user_id ON pipeline_runs(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON datasets(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_datasets_pipeline_run_id ON datasets(pipeline_run_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_pipeline_run_id ON reports(pipeline_run_id);")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_quality_reports_pipeline_run_id ON quality_reports(pipeline_run_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_analytics_reports_pipeline_run_id ON analytics_reports(pipeline_run_id);"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_jobs_job_id ON ai_jobs(job_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_jobs_pipeline_run_id ON ai_jobs(pipeline_run_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_jobs_user_id ON ai_jobs(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_jobs_status ON ai_jobs(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_reports_job_id ON ai_reports(job_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_reports_pipeline_run_id ON ai_reports(pipeline_run_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_reports_user_id ON ai_reports(user_id);")

            # Sprint 14 Phase 4 & Remediation — AI Report Structured & Provenance Migrations
            for col_def in [
                ("source_version_id", "TEXT"),
                ("cleaned_version_id", "TEXT"),
                ("cleaning_execution_id", "TEXT"),
                ("context_version", "TEXT DEFAULT 'v1.0'"),
                ("key_findings", "TEXT"),
                ("business_implications", "TEXT"),
                ("risks", "TEXT"),
                ("opportunities", "TEXT"),
                ("actions", "TEXT"),
                ("limitations", "TEXT"),
                ("confidence", "TEXT"),
                ("structured_payload", "TEXT"),
            ]:
                try:
                    cursor.execute(f"ALTER TABLE ai_reports ADD COLUMN {col_def[0]} {col_def[1]};")
                except Exception:
                    pass

            # Sprint 14 Phase 3 — Governance indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_dataset_versions_version_id ON dataset_versions(version_id);"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dataset_versions_user_id ON dataset_versions(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dataset_versions_is_source ON dataset_versions(is_source);")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_dataset_versions_parent ON dataset_versions(parent_version_id);"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cleaning_configs_config_id ON cleaning_configs(config_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cleaning_configs_user_id ON cleaning_configs(user_id);")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_cleaning_executions_id ON cleaning_executions(execution_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_cleaning_executions_run ON cleaning_executions(pipeline_run_id);"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cleaning_executions_user ON cleaning_executions(user_id);")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_cleaning_executions_source ON cleaning_executions(source_version_id);"
            )

            # Sprint 14 Phase 4 — Provenance indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_reports_source_version ON ai_reports(source_version_id);")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_reports_cleaned_version ON ai_reports(cleaned_version_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_reports_cleaning_exec ON ai_reports(cleaning_execution_id);"
            )

            self._database_connection.commit()

        except Exception:

            self._database_connection.rollback()

            raise

        finally:

            cursor.close()
