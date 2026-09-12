output "event_hubs_connection_string" {
  description = "Connection string for Event Hubs namespace"
  value       = azurerm_eventhub_namespace.aegis.default_primary_connection_string
  sensitive   = true
}

output "event_hub_name" {
  description = "Target Event Hub entity name"
  value       = azurerm_eventhub.audit_events.name
}

output "worm_storage_account_name" {
  description = "Azure Storage Account for Immutable WORM logs"
  value       = azurerm_storage_account.aegis_worm.name
}

output "worm_container_name" {
  description = "Container with Time-based Immutability Policy"
  value       = azurerm_storage_container.aegis_worm_container.name
}

output "log_analytics_workspace_id" {
  description = "Workspace ID for Azure Log Analytics / Sentinel"
  value       = azurerm_log_analytics_workspace.aegis.workspace_id
}
