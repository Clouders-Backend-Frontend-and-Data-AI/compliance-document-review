output "vpc_id" {
  description = "Application VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Public subnet ID"
  value       = aws_subnet.public.id
}

output "security_group_id" {
  description = "Application security group ID"
  value       = aws_security_group.app.id
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.backend.repository_url
}
output "ec2_instance_id" {
  description = "EC2 application instance ID"
  value       = aws_instance.app.id
}

output "ec2_public_ip" {
  description = "EC2 application public IP"
  value       = aws_instance.app.public_ip
}

output "ec2_public_dns" {
  description = "EC2 application public DNS"
  value       = aws_instance.app.public_dns
}

output "ec2_instance_type" {
  description = "EC2 instance type"
  value       = aws_instance.app.instance_type
}
output "github_actions_role_arn" {
  description = "IAM role assumed by GitHub Actions through OIDC"
  value       = aws_iam_role.github_actions.arn
}
output "app_secret_arn" {
  description = "ARN of the production application secret"
  value       = aws_secretsmanager_secret.app.arn
}
