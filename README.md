# Azure Function - Process BOM Weather Stations

A basic function using the [lib-py-parse-bom-stations](https://github.com/weather-balloon/lib-py-parse-bom-stations)
module to process the Australian Bureau of Meteorology's
[list of weather stations](ftp://ftp.bom.gov.au/anon2/home/ncc/metadata/sitelists/stations.zip)
and put them into a storage account table.

The [deploy-datalake project](https://github.com/weather-balloon/deploy-datalake) deploys the required
Logic App and storage account to load the station data into a blob. This function watches that blob store
for the stations file and performs the table entries.

## Get started

Make sure you have [`pipenv`](https://pypi.org/project/pipenv/) installed.

Run the following to get started:

    make init

I notice that this can cause issues with setting up the required packages so
it can be useful (after that first run of `make init`) to run everything from
a `pipenv shell`:

    pipenv shell
    make init

Setup your system for [local function development](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local).

In order to run locally you'll need access to a storage account.
Hopefully [Azurite](https://github.com/Azure/Azurite) will support storage tables in the future
but I just setup an Azure storage account and grabbed the connection string from there.
Copy the `local.settings.json.sample` file to `local.settings.json` and add in your
connection string.

As per the `function.json` file, the function reacts to a change in the `bom-gov-au/stations/stations.txt`
blob. Create (in your storage account) a blob container named `bom-gov-au`.

You can now start up the function locally with:

    make start

To trigger the function you need upload the station data as `stations/stations.txt`.
The `test-data/stations.txt` is a small subset of the full data so is a useful starting point.

You should see that a `WeatherStations` table is created and rows added.

## Deploy

### Deploying from your RC to Azure

You can quickly spin up a test environment in Azure using the following:

    RG_NAME=fn-process-weather-stations-test
    SA_NAME=fpwst$USER
    RG_LOCATION=australiaeast
    AZURE_STORAGE_ACCOUNT=$SA_NAME

    az login

    az group create --name $RG_NAME --location $RG_LOCATION

    az storage account create --name $SA_NAME --resource-group $RG_NAME \
        --kind StorageV2 --sku Standard_LRS --https-only true

    az functionapp create --resource-group $RG_NAME --name $RG_NAME --storage-account $SA_NAME \
        --os-type Linux --runtime python --consumption-plan-location $RG_LOCATION

    az storage container create --name bom-gov-au --account-name $SA_NAME \
        --account-key $(az storage account keys list --account-name $SA_NAME \
        --query [0].value --output tsv)


    func azure functionapp publish $RG_NAME --build remote

### Using an ARM Template

    RG_NAME_PREFIX=wb-fn-process-weather-stations
    RG_LOCATION=australiaeast
    FN_ENVIRONMENT=dev
    FN_SERVICE=observations
    RG_NAME=$RG_NAME_PREFIX-$FN_ENVIRONMENT

    az group create --name $RG_NAME_PREFIX-$FN_ENVIRONMENT \
        --location $RG_LOCATION --tags environment=$FN_ENVIRONMENT service=$FN_SERVICE

    az group deployment validate --resource-group $RG_NAME --template-file azuredeploy.json

    az group deployment create --resource-group $RG_NAME --template-file azuredeploy.json

## References

- [Azure Functions Python developer guide](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Azure Python SDK - TableService](https://docs.microsoft.com/en-au/python/api/azure-cosmosdb-table/azure.cosmosdb.table.tableservice.tableservice?view=azure-python)
