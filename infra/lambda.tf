resource "aws_iam_role" "lambda_exec" {
  name = "recipe-bot-lambda-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_exec.name
}

resource "aws_iam_role_policy" "lambda_secrets" {
  name = "lambda-secrets-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "bedrock:InvokeModel"
        ]
        Resource = [
          aws_secretsmanager_secret.pinecone.arn,
          "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-instant-v1",
          "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
        ]
      }
    ]
  })
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend"
  output_path = "${path.module}/../backend/package.zip"
  excludes    = [
    "venv",
    "__pycache__",
    "*.pyc",
    ".git",
    "setup_embeddings.py",
    "package.zip"
  ]
}

resource "aws_lambda_function" "api" {
  function_name = "recipe-bot-api"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "main.handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 512

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  
  layers = ["arn:aws:lambda:us-east-1:034362072533:layer:ml-dependencies:1"]
}

resource "aws_lambda_function_url" "api_url" {
  function_name      = aws_lambda_function.api.function_name
  authorization_type = "NONE"
  
  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["*"]
    allow_headers     = ["content-type"]
    max_age          = 86400
  }
}