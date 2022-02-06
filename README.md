# Tutorial: Connect App Service application to Azure SQL and PostgreSQL database using managed identity.

### Prerequisites
* [Azure Account](https://azure.microsoft.com/en-us/free/)
* [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/)
or [Azure Cloud Shell](https://docs.microsoft.com/en-us/azure/cloud-shell/overview)

We will create mainly free resources in this tutorial which are in scope of free Azure account.
You can find list of this resources [here.](https://azure.microsoft.com/en-us/pricing/free-services/)

### Overview
  
In this tutorial we will create simple infrastructure in Azure which will contain following resources:
* [Container Registry](https://docs.microsoft.com/en-us/azure/container-registry/)
* [App Service](https://docs.microsoft.com/en-us/azure/app-service/)
* [Azure SQL database](https://docs.microsoft.com/en-us/azure/azure-sql/database/)
* [Azure database for PostgreSQL](https://docs.microsoft.com/en-us/azure/postgresql/)

We will deploy simple application build with [FastApi](https://fastapi.tiangolo.com/).
Then we will test connection between application, Azure SQL and PostgreSQL using Managed Identity.

List of variables used in this tutorial:
```python
# Webapp
resourceGroup="dbtutorialRG"
registry="dbtutorialACR"
appservice="dbtutorialPLAN"
webapp="dbtutorialAPP"
location="westeurope"

# Azure SQL
sqladmin="dbtutorialsqlAdmin"
sqladmingroup="dbtutorialSQLDBAccessGroup"
sqlservername="dbtutorialsqlserver"
sqldb="dbtutorial"
# PostgreSQL
postgresserver="dbtutorialpostgresserver"
postgresusername="dbtutorialpostgresAdmin"
postgrespassword="Supersecret123$"

```

To avoid errors while provisioning resources to Azure I encourage you to use your own names. For example:

`resourceGroup="dbtutorialRG$RANDOM" `

Additionally we will set following variables in app config: `database_interface/config.py`
```python
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
```
For real project environment variable should be stored in [Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/).

We will use [SQLAlchemy](https://docs.sqlalchemy.org/en/14/core/engines.html) and [PyODBC](https://github.com/mkleehammer/pyodbc/wiki) to create connection to MSSQL database: `database_interface/mssql/session.py`
```python
from dataclasses import dataclass
from types import TracebackType
from typing import Optional
from typing import Type

import pyodbc
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from database_interface.config import db_settings

pyodbc.pooling = False

DATABASE_URL = URL.create("mssql+pyodbc", query={"odbc_connect": db_settings.MSSQL_CONNECTION_STRING})

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)


@dataclass
class MssqlSessionManager:
    def __post_init__(self) -> None:
        self.db_session = SessionLocal()

    def __enter__(self) -> SessionLocal:
        return self.db_session

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.db_session.close()

    async def __aenter__(self) -> SessionLocal:
        return self.db_session

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.db_session.close()
```

I will use [SQLAlchemy](https://docs.sqlalchemy.org/en/14/core/engines.html) and [Psycopg2](https://www.psycopg.org/docs/) to create connection to PostgreSQL database: `database_interface/postgres/session.py`
```python
from dataclasses import dataclass
from types import TracebackType
from typing import Optional
from typing import Type

from azure.core.credentials import AccessToken
from azure.identity import DefaultAzureCredential
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from database_interface.config import db_settings


def get_aad_token():
    scope: str = "https://ossrdbms-aad.database.windows.net/.default"
    credential: DefaultAzureCredential = DefaultAzureCredential()
    access_token: AccessToken = credential.get_token(scope)
    return access_token.token


DATABASE_URL = URL.create(
    "postgresql+psycopg2",
    username=db_settings.POSTGRES_USERNAME,
    password=get_aad_token(),
    host=db_settings.POSTGRES_HOSTNAME,
    port=db_settings.POSTGRES_PORT,
    database=db_settings.POSTGRES_DB
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)


@dataclass
class PostgresSessionManager:
    def __post_init__(self) -> None:
        self.db_session = SessionLocal()

    def __enter__(self) -> SessionLocal:
        return self.db_session

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.db_session.close()

    async def __aenter__(self) -> SessionLocal:
        return self.db_session

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.db_session.close()

```

We can extend this solution so we can connect from local environment -> [LINK](https://github.com/Azure/azure-sdk-for-python/tree/azure-identity_1.7.1/sdk/identity/azure-identity) 

## 1. Create resource for web application

### Create resource group

`az login`

```yaml
az group create --name $resourceGroup --location $location
```
![alt text](images/resource_group.png "Resource Group")

### Create Container Registry

```yaml
az acr create --name $registry --resource-group $resourceGroup --sku Basic
```
![alt text](images/acr.png "Container Registry")

### Clone repo, build and push image to Container Registry

```yaml
git clone git@github.com:adamkielar/fastapi-azuresql-managed-identity.git
cd fastapi-azuresql-managed-identity
az acr build -t tutorial-image:v1.0.0 -r $registry .
```
![alt text](images/acr-image.png "Image in ACR")

### Creat App Service Plan
```yaml
az appservice plan create --name $appservice --resource-group $resourceGroup --is-linux --sku B1
```
![alt text](images/app-plan.png "App Service Plan")

### Create App Service and enable system assigned Managed Identity
```yaml
az webapp create --resource-group $resourceGroup --plan $appservice --name $webapp --deployment-container-image-name dbtutorialacr.azurecr.io/tutorial-image:v1.0.0
az webapp config appsettings set --resource-group $resourceGroup --name $webapp --settings WEBSITES_PORT=8000
az webapp identity assign --resource-group $resourceGroup --name $webapp
```

![alt text](images/app-service.png "App Service")

### Grant managed identity permission to access container registry

```yaml
subscription_id=$(az account show --query id --output tsv)
principal_id=$(az webapp identity show --resource-group $resourceGroup --name $webapp --query principalId --output tsv)

az role assignment create --assignee $principal_id --scope /subscriptions/$subscription_id/resourceGroups/$resourceGroup/providers/Microsoft.ContainerRegistry/registries/$registry --role "AcrPull"

```

### Configure webapp to use managed identity to pull image from Azure Container Registry
```yaml
az resource update --ids /subscriptions/$subscription_id/resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/$webapp/config/web --set properties.acrUseManagedIdentityCreds=True

```

### Configure which docker image our app service should use
```yaml
az webapp config container set --name $webapp --resource-group $resourceGroup --docker-custom-image-name dbtutorialacr.azurecr.io/tutorial-image:v1.0.0 --docker-registry-server-url https://dbtutorialacr.azurecr.io

```
![alt text](images/deployment-center.png "Deployment Center")


### Create group in AAD that will have access to SQL server
```yaml
az ad group create --display-name $sqladmingroup --mail-nickname $sqladmingroup
```

### Add webapp service principal to the group
```yaml
group_id=$(az ad group show --group $sqladmingroup --query objectId --output tsv)
az ad group member add --group $group_id --member-id $principal_id
```
![alt text](images/aad-group.png "AAD Group")

## 2. Create Azure SQL
### Create a server without SQL Admin, with AD admin, AD Only enabled
```yaml
az sql server create --enable-ad-only-auth --external-admin-principal-type User --external-admin-name $sqladmingroup  --external-admin-sid $group_id -g $resourceGroup -n $sqlservername

```
![alt text](images/sql-server.png "Azure SQL Server")

### Create database:
```yaml
az sql db create --name $sqldb --server $sqlservername --resource-group $resourceGroup --collation Polish_CI_AS --edition GeneralPurpose --family Gen5 --capacity 2

```
![alt text](images/sql-database.png "Azure SQL database")

### Allow Azure services and resources to access server
```yaml
az sql server firewall-rule create --resource-group $resourceGroup --server $sqlservername --name dbtutorial --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0

```

## 3. Create Azure database for PostgreSQL
### Create server
```yaml
az postgres server create -l $location -g $resourceGroup -n $postgresserver -u $postgresusername -p $postgrespassword \
    --sku-name B_Gen5_1 --ssl-enforcement Enabled --minimal-tls-version TLS1_2 --public-network-access 0.0.0.0 \
    --backup-retention 10 --geo-redundant-backup Disabled --storage-size 51200 --version 11
```
For real project we should use virtual network service to connect our webapp to db.

![alt text](images/postgres-db.png "Postgres Database")

### Check database connection from Azure Cloud Shell
We only enabled access to postgres server for Azure resources.

```yaml
psql --host=$postgresserver.postgres.database.azure.com --port=5432 --username=$postgresusername@$postgresserver --dbname=postgres
```
![alt text](images/postgres_connect.png "Postgres Database")
### Set Active Directory admin for PostgresSQL. Choose our Admin group.

![alt text](images/ad-admin-postgres.png "Active Directory admin")

### Check database connection from Azure Cloud Shell using Access Token
```yaml
# Get token
az account get-access-token --resource-type oss-rdbms

# As response we will get json
{
  "accessToken": "TOKEN",
  "expiresOn": "...",
  "subscription": "...",
  "tenant": "...",
  "tokenType": "Bearer"
}

export PGPASSWORD="TOKEN"

psql "host=dbtutorialpostgresserver.postgres.database.azure.com port=5432  user=dbtutorialSQLDBAccessGroup@dbtutorialpostgresserver  dbname=postgres sslmode=require"
```
### Test application
Azure SQL
`https://dbtutorialapp.azurewebsites.net/api/v1/mssql_db`

![alt text](images/db-healthcheck.png "Azure SQL health check")

PostgreSQL `https://dbtutorialapp.azurewebsites.net/api/v1/postgres_db`

![alt text](images/postgres-healthcheck.png "PostgreSQL health check")
### Clean up and remove resources

```yaml
az group delete --name $resourceGroup 
```
