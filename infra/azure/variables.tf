variable "resource_group_name" {
  type        = string
  description = "The name of the resource group for Aegis audit infrastructure"
  default     = "rg-aegis-audit-prod"
}

variable "location" {
  type        = string
  description = "Azure region for deployment"
  default     = "japaneast"
}

variable "environment" {
  type        = string
  description = "Environment name"
  default     = "prod"
}

variable "event_hubs_capacity" {
  type        = number
  description = "Event Hubs Throughput Units (1-20 TU, approx 1,000 events/sec per TU)"
  default     = 4
}

variable "retention_period_days" {
  type        = number
  description = "WORM storage immutable retention period in days (min 3 years = 1095, max 10 years = 3650)"
  default     = 1095 # 3 years
}

variable "log_analytics_retention_days" {
  type        = number
  description = "Hot tier retention in Log Analytics Workspace in days"
  default     = 30
}
