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

    def _add_column_if_missing(self, cursor, table: str, column: str, definition: str) -> None:
        """
        Add a column only when it is absent, WITHOUT relying on a failed statement.

        The migrations used to try `ALTER TABLE ... ADD COLUMN` and swallow the
        error when the column already existed. On PostgreSQL that is fatal:
        DDL is transactional, so the `rollback()` after the (expected) failure
        discarded every CREATE TABLE issued before it, and the bare `pass`
        variant left the transaction aborted so every later statement failed.
        Verified against PostgreSQL 16: a fresh database ended with 0 of 11
        tables and could never recover on retry.

        `table`, `column` and `definition` are internal constants, never input.
        """
        if self._database_type == "postgresql":
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {definition};")
            return

        # SQLite has no ADD COLUMN IF NOT EXISTS.
        cursor.execute(f"PRAGMA table_info({table});")
        if any(row[1] == column for row in cursor.fetchall()):
            return
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition};")

    def _ensure_case_insensitive_user_uniqueness(self, cursor) -> None:
        """
        Enforce unique usernames and emails regardless of case (L6).

        The column UNIQUE constraints are case-sensitive while every lookup
        uses LOWER(), so two concurrent registrations of 'Alice' and 'alice'
        could both succeed. Existing case-duplicates are reported rather than
        silently merged: an operator has to decide which account survives.
        On PostgreSQL the index creation itself fails and names the duplicate
        key; SQLite gets an explicit check for a clearer message.
        """
        for column in ("username", "email"):
            if self._database_type == "sqlite":
                cursor.execute(
                    f"SELECT LOWER({column}) AS value FROM users GROUP BY LOWER({column}) HAVING COUNT(*) > 1;"
                )
                duplicates = cursor.fetchall()
            else:
                duplicates = []
            if duplicates:
                raise RuntimeError(
                    f"users.{column} has values that differ only by case; resolve the duplicate "
                    "accounts before starting the application."
                )
            cursor.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS uq_users_{column}_lower ON users(LOWER({column}));")

    def _create_schema(self):
        """
        Create or migrate the whole schema in ONE transaction.

        On PostgreSQL this makes initialization atomic: it either commits
        completely or rolls back to the previous state, so a failed attempt
        can simply be retried.
        """

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
                self._add_column_if_missing(cursor, table_name, "user_id", "INTEGER")

            # Token invalidation counter (audit 2026-09-29, I2)
            self._add_column_if_missing(cursor, "users", "token_version", "INTEGER NOT NULL DEFAULT 0")

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
            # Revoked access tokens (pre-Sprint-15 hardening, SEC-09)
            # -------------------------------------------------
            # Keyed by the token's `jti`; rows are pruned once `expires_at`
            # (epoch seconds) has passed, so the table stays bounded.

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS revoked_tokens(
                    jti TEXT PRIMARY KEY,
                    expires_at BIGINT NOT NULL,
                    revoked_at BIGINT NOT NULL
                );
                """)

            # -------------------------------------------------
            # Login throttle counters (audit 2026-09-29, I3 / M12)
            # -------------------------------------------------
            # Epoch seconds. Survive restarts and are shared by API workers.

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS login_failures(
                    scope TEXT NOT NULL,
                    key TEXT NOT NULL,
                    failures INTEGER NOT NULL,
                    locked_until {float_type} NOT NULL,
                    last_failure {float_type} NOT NULL,
                    PRIMARY KEY (scope, key)
                );
                """)

            # -------------------------------------------------
            # Durable audit trail (pre-Sprint-15 hardening, SEC-25)
            # -------------------------------------------------
            # No foreign keys on purpose: audit rows must outlive the users and
            # resources they describe.

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS audit_events(
                    id {pk},
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    occurred_at {ts} NOT NULL,
                    actor_id INTEGER,
                    actor_username TEXT,
                    target_id INTEGER,
                    target_resource TEXT,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    details_json TEXT
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_revoked_tokens_expires ON revoked_tokens(expires_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_actor ON audit_events(actor_id);")
            self._ensure_case_insensitive_user_uniqueness(cursor)

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
                self._add_column_if_missing(cursor, "ai_reports", col_def[0], col_def[1])

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
