from pydantic import BaseSettings


class DbSettings(BaseSettings):
    MSSQL_CONNECTION_STRING: str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=dbtutorialsqlserver.database.windows.net;"
        "DATABASE=dbtutorial;"
        "Authentication=ActiveDirectoryMSI"
    )

    POSTGRES_USERNAME: str = "dbtutorialSQLDBAccessGroup@dbtutorialpostgresserver"
    POSTGRES_HOSTNAME: str = "dbtutorialpostgresserver.postgres.database.azure.com"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"


db_settings = DbSettings()
