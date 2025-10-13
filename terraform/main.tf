resource "aws_dynamodb_table" "crypto_prices" {
  name           = "crypto-prices"
  billing_mode   = "PAY_PER_REQUEST"  # On-demand pricing
  hash_key       = "PK"
  range_key      = "timestamp" # sort key

  attribute {
    name = "PK"
    type = "S"  # String
  }

  attribute {
    name = "timestamp"
    type = "S"  # String
  }

  ttl {
    enabled        = true
    attribute_name = "ttl"
  }

  tags = {
    Name        = "crypto-prices"
    Environment = "production"
    Purpose     = "Store cryptocurrency prices"
  }
}

output "dynamodb_table_name" {
  value       = aws_dynamodb_table.crypto_prices.name
  description = "Name of the DynamoDB table"
}

output "dynamodb_table_arn" {
  value       = aws_dynamodb_table.crypto_prices.arn
  description = "ARN of the DynamoDB table"
}