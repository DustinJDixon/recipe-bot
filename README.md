# Recipe Bot 🍳

An AI-powered conversational recipe assistant that helps users find the perfect recipe through natural conversation. Built with modern serverless architecture on AWS.

## Features

- **Conversational AI**: Natural language interaction using AWS Bedrock Claude
- **Semantic Recipe Search**: 5,000+ recipes with AI-powered semantic search via Pinecone
- **Smart Recommendations**: Handles dietary restrictions, cuisine preferences, and cooking time
- **Modern UI**: Responsive React chat interface with recipe details modal
- **Cost-Optimized**: Designed for minimal AWS costs (~$1.24/month for personal use)

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js       │    │   AWS Lambda     │    │   Pinecone      │
│   Frontend      │───▶│   Backend        │───▶│   Vector DB     │
│   (S3/CloudFront)│    │   (Bedrock AI)   │    │   (Recipes)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Tech Stack:**
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Backend**: Python, AWS Lambda, AWS Bedrock (Claude + Titan)
- **Database**: Pinecone vector database with semantic embeddings
- **Infrastructure**: Terraform, AWS S3, CloudFront, Secrets Manager
- **Data**: 5,000 recipes from HuggingFace dataset

## Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform installed
- Node.js 18+ and Python 3.12+
- Pinecone account (free tier)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd recipe-bot
```

### 2. Infrastructure Setup

```bash
cd infra
cp terraform.tfvars.template terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

### 3. Backend Setup

```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Load recipes into Pinecone (one-time setup)
python setup_embeddings.py
```

### 4. Frontend Setup

```bash
cd ../frontend
npm install
# Create .env.local with your API Gateway URL
echo "NEXT_PUBLIC_API_URL=https://your-api-gateway-url" > .env.local
npm run build
```

### 5. Deploy Frontend

```bash
# Upload to S3 (replace with your bucket name)
aws s3 sync out/ s3://your-frontend-bucket --delete
```

## Configuration

### Required AWS Services

- **Bedrock**: Enable Claude Instant and Titan Embeddings models
- **Lambda**: Function URL enabled for API access
- **S3**: Static website hosting for frontend
- **CloudFront**: CDN distribution
- **Secrets Manager**: Store Pinecone API key

### Environment Variables

**Backend (AWS Secrets Manager):**
- `pinecone-api-key`: Your Pinecone API key

**Frontend (.env.local):**
- `NEXT_PUBLIC_API_URL`: Your Lambda Function URL

## Usage

1. **Start Conversation**: The bot greets you and asks about your cooking mood
2. **Natural Chat**: Describe what you want - "quick Italian lunch" or "healthy dinner"
3. **Get Recommendations**: Bot suggests recipes based on your preferences
4. **View Details**: Click recipe names to see ingredients and instructions
5. **Refine Search**: Ask for more questions or different options

### Example Conversation

```
Bot: Hi! What kind of mood are you in for cooking?
You: Something quick and healthy for lunch
Bot: Great! What type of cuisine sounds good?
You: Mediterranean
Bot: Perfect! Here are some recipes:
     1. Greek Quinoa Salad ⭐ 4.5/5
     2. Mediterranean Wrap ⭐ 4.8/5
```

## Cost Breakdown

**Monthly Costs (100 queries/month):**
- AWS Lambda: ~$0.20
- AWS Bedrock: ~$0.40
- S3 + CloudFront: ~$0.00 (free tier)
- Pinecone: ~$0.64 (5,000 recipes)
- **Total: ~$1.24/month**

## Development

### Project Structure

```
recipe-bot/
├── frontend/          # Next.js React app
│   ├── app/
│   │   └── components/Chat.tsx
│   └── package.json
├── backend/           # Python Lambda function
│   ├── main.py       # Lambda handler
│   ├── setup_embeddings.py
│   └── requirements.txt
├── infra/            # Terraform infrastructure
│   ├── main.tf
│   ├── lambda.tf
│   └── frontend.tf
└── README.md
```

### Local Development

**Backend:**
```bash
cd backend
python main.py  # Test locally
```

**Frontend:**
```bash
cd frontend
npm run dev     # Development server
npm run build   # Production build
```

### Adding More Recipes

To load more recipes (up to 16,000 for free tier):

```bash
cd backend
# Edit setup_embeddings.py: change split="train[:5000]" to split="train[:16000]"
python setup_embeddings.py
```

## Troubleshooting

**Common Issues:**

1. **Lambda timeout**: Increase timeout in `lambda.tf`
2. **CORS errors**: Check Lambda Function URL configuration
3. **No recipes found**: Verify Pinecone index and API key
4. **High costs**: Monitor Bedrock usage in AWS console

**Debug Commands:**
```bash
# Check Lambda logs
aws logs tail /aws/lambda/recipe-bot-function --follow

# Test Pinecone connection
python -c "from pinecone import Pinecone; pc = Pinecone(api_key='your-key'); print(pc.list_indexes())"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Recipe data from [HuggingFace recipes dataset](https://huggingface.co/datasets/AkashPS11/recipes_data_food.com)
- Built with AWS Bedrock, Pinecone, and modern web technologies