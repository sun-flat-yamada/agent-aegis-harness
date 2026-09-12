terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# 1. リソースグループ
resource "azurerm_resource_group" "aegis" {
  name     = var.resource_group_name
  location = var.location
  tags = {
    Project     = "agent-aegis-harness"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# 2. Azure Event Hubs (高スループット Ingestion プレーン)
resource "azurerm_eventhub_namespace" "aegis" {
  name                = "evh-aegis-${var.environment}"
  location            = azurerm_resource_group.aegis.location
  resource_group_name = azurerm_resource_group.aegis.name
  sku                 = "Standard"
  capacity            = var.event_hubs_capacity
  auto_inflate_enabled = true
  maximum_throughput_units = 10

  tags = azurerm_resource_group.aegis.tags
}

resource "azurerm_eventhub" "audit_events" {
  name                = "aegis-audit-events"
  namespace_name      = azurerm_eventhub_namespace.aegis.name
  resource_group_name = azurerm_resource_group.aegis.name
  partition_count     = 8
  message_retention   = 7 # 7日間保持
}

# 3. Azure Blob Storage (法的 WORM 不変ストレージ 3〜10年保持)
resource "azurerm_storage_account" "aegis_worm" {
  name                     = "staegisauditworm${var.environment}"
  resource_group_name      = azurerm_resource_group.aegis.name
  location                 = azurerm_resource_group.aegis.location
  account_tier             = "Standard"
  account_replication_type = "GRS" # 地理冗長
  access_tier              = "Cool"
  min_tls_version          = "TLS1_2"

  blob_properties {
    versioning_enabled = true
  }

  tags = azurerm_resource_group.aegis.tags
}

resource "azurerm_storage_container" "aegis_worm_container" {
  name                  = "aegis-audit-worm"
  storage_account_name  = azurerm_storage_account.aegis_worm.name
  container_access_type = "private"
}

resource "azurerm_storage_container_immutability_policy" "worm_policy" {
  storage_container_resource_manager_id = azurerm_storage_container.aegis_worm_container.resource_manager_id
  immutability_period_in_days           = var.retention_period_days
  protected_append_writes_all_enabled   = true
}

# 4. Azure Log Analytics Workspace & Microsoft Sentinel (Hot 検索・KQL)
resource "azurerm_log_analytics_workspace" "aegis" {
  name                = "log-aegis-audit-${var.environment}"
  location            = azurerm_resource_group.aegis.location
  resource_group_name = azurerm_resource_group.aegis.name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_analytics_retention_days

  tags = azurerm_resource_group.aegis.tags
}
