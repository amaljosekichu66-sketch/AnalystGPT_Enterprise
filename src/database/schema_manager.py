import sqlite3


class SchemaManager:
    """
    Creates and manages the AnalystGPT Enterprise database schema.
    """

    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def create_tables(self):
        """
        Create all required database tables.
        """
        cursor = self._connection.cursor()

        # Enable SQLite foreign key support
        cursor.execute("PRAGMA foreign_keys = ON;")

        # ------------------------------------------------------------------
        # Pipeline Runs
        # ------------------------------------------------------------------

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL
        );
        """)

        # ------------------------------------------------------------------
        # Datasets
        # ------------------------------------------------------------------

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_run_id INTEGER NOT NULL,
            dataset_name TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            column_count INTEGER NOT NULL,

            FOREIGN KEY (pipeline_run_id)
                REFERENCES pipeline_runs(id)
                ON DELETE CASCADE
        );
        """)

        # ------------------------------------------------------------------
        # Quality Reports
        # ------------------------------------------------------------------

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_reports(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_run_id INTEGER NOT NULL,
            completeness REAL,
            validity REAL,
            consistency REAL,
            uniqueness_score REAL,

            FOREIGN KEY (pipeline_run_id)
                REFERENCES pipeline_runs(id)
                ON DELETE CASCADE
        );
        """)

        # ------------------------------------------------------------------
        # Analytics Reports
        # ------------------------------------------------------------------

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics_reports(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_run_id INTEGER NOT NULL,
            total_numeric_columns INTEGER,
            total_categorical_columns INTEGER,
            correlation_summary TEXT,

            FOREIGN KEY (pipeline_run_id)
                REFERENCES pipeline_runs(id)
                ON DELETE CASCADE
        );
        """)

        # ------------------------------------------------------------------
        # Reports
        # ------------------------------------------------------------------

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_run_id INTEGER NOT NULL,
            report_path TEXT NOT NULL,
            generated_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (pipeline_run_id)
                REFERENCES pipeline_runs(id)
                ON DELETE CASCADE
        );
        """)

        self._connection.commit()

    def initialize_schema(self):
        """
        Initialize the complete database schema.
        """
        self.create_tables()