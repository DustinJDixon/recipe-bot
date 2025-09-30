resource "aws_secretsmanager_secret" "pinecone" {
  name = "pinecone-api-key"
}

resource "aws_secretsmanager_secret_version" "pinecone_ver" {
  secret_id     = aws_secretsmanager_secret.pinecone.id
  secret_string = var.pinecone_api_key
}

