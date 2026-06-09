@description('Azure region for web resources.')
param location string

@description('Prefix used to build resource names.')
param namePrefix string

@description('Subnet used for App Service VNet integration.')
param appSubnetId string

@description('App Service Plan SKU name.')
param appServiceSkuName string = 'P1v3'

@description('Runtime stack for the Linux web apps.')
param linuxFxVersion string = 'DOTNETCORE|8.0'

@description('Storage account name exposed to the web tier through configuration.')
param storageAccountName string

@description('Cosmos DB endpoint exposed to the web tier through configuration.')
param cosmosEndpoint string

@description('Cosmos DB database name exposed to the web tier through configuration.')
param cosmosDatabaseName string

@description('Tags applied to the web resources.')
param tags object = {}

var planName = '${namePrefix}-plan'
var workspaceName = '${namePrefix}-law'
var appInsightsName = '${namePrefix}-appi'
var apiSiteName = take(replace('${namePrefix}-api', '-', ''), 60)
var portalSiteName = take(replace('${namePrefix}-portal', '-', ''), 60)

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
  }
}

resource servicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: planName
  location: location
  tags: tags
  sku: {
    name: appServiceSkuName
    tier: contains(appServiceSkuName, 'P') ? 'PremiumV3' : 'Standard'
    size: appServiceSkuName
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

resource apiSite 'Microsoft.Web/sites@2023-12-01' = {
  name: apiSiteName
  location: location
  tags: union(tags, {
    role: 'api'
  })
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: servicePlan.id
    httpsOnly: true
    virtualNetworkSubnetId: appSubnetId
    siteConfig: {
      linuxFxVersion: linuxFxVersion
      alwaysOn: true
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      vnetRouteAllEnabled: true
      appSettings: [
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'MONADO_STORAGE_ACCOUNT'
          value: storageAccountName
        }
        {
          name: 'MONADO_COSMOS_ENDPOINT'
          value: cosmosEndpoint
        }
        {
          name: 'MONADO_COSMOS_DATABASE'
          value: cosmosDatabaseName
        }
        {
          name: 'MONADO_ROLE'
          value: 'api'
        }
      ]
    }
  }
}

resource portalSite 'Microsoft.Web/sites@2023-12-01' = {
  name: portalSiteName
  location: location
  tags: union(tags, {
    role: 'portal'
  })
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: servicePlan.id
    httpsOnly: true
    virtualNetworkSubnetId: appSubnetId
    siteConfig: {
      linuxFxVersion: linuxFxVersion
      alwaysOn: true
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      vnetRouteAllEnabled: true
      appSettings: [
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'MONADO_API_BASE_URL'
          value: 'https://${apiSite.properties.defaultHostName}'
        }
        {
          name: 'MONADO_ROLE'
          value: 'portal'
        }
      ]
    }
  }
}

output appServicePlanName string = servicePlan.name
output apiWebAppName string = apiSite.name
output portalWebAppName string = portalSite.name
output apiHostname string = apiSite.properties.defaultHostName
output portalHostname string = portalSite.properties.defaultHostName
