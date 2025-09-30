output "api_url" {
  value = aws_lambda_function_url.api_url.function_url
}

output "s3_bucket_name" {
  value = aws_s3_bucket.frontend.bucket
}

output "website_url" {
  value = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "s3_website_url" {
  value = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
}