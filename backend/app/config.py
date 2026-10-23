import os

APP_ENV = os.getenv("APP_ENV", "development")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "smartcampus")
DB_USER = os.getenv("DB_USER", "smartcampus")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def get_db_dsn() -> str:
    return (
        f"host={os.getenv('DB_HOST', DB_HOST)} "
        f"port={os.getenv('DB_PORT', DB_PORT)} "
        f"dbname={os.getenv('DB_NAME', DB_NAME)} "
        f"user={os.getenv('DB_USER', DB_USER)} "
        f"password={os.getenv('DB_PASSWORD', DB_PASSWORD)}"
    )
