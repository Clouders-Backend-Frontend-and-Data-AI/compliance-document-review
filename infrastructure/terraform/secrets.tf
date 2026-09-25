resource "aws_secretsmanager_secret" "app" {
  name        = "${var.project_name}/production/app"
  description = "Production application secrets for Compliance Document Review"

  tags = {
    Name        = "${var.project_name}-app-secret"
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
