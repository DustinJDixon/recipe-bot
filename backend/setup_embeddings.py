import os
import json
from datasets import load_dataset
# Using AWS Bedrock instead of sentence-transformers
import pinecone
from pinecone import Pinecone
import boto3

def get_secret(secret_name):
    session = boto3.session.Session()
    client = session.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

def setup_pinecone():
    api_key = get_secret('pinecone-api-key')
    pc = Pinecone(api_key=api_key)
    index_name = "recipe-embeddings-titan"
    
    existing_indexes = [index.name for index in pc.list_indexes()]
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=pinecone.ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    
    return pc.Index(index_name)

def process_recipes():
    print("Loading dataset...")
    dataset = load_dataset("AkashPS11/recipes_data_food.com", split="train[:5000]")
    
    print(f"Dataset columns: {dataset.column_names}")
    print(f"First item: {dataset[0]}")
    
    print("Setting up AWS Bedrock for embeddings...")
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    print("Setting up Pinecone...")
    index = setup_pinecone()
    
    print("Clearing existing vectors...")
    try:
        index.delete(delete_all=True)
    except Exception as e:
        print(f"Note: Could not clear existing vectors: {e}")
    
    print("Processing recipes...")
    vectors = []
    batch_size = 100
    
    for i, recipe in enumerate(dataset):
        if i % 100 == 0:
            print(f"Processing recipe {i}/{len(dataset)}...")
        
        title = recipe['Name']
        
        quantities = recipe['RecipeIngredientQuantities']
        parts = recipe['RecipeIngredientParts']
        
        import re
        qty_list = re.findall(r'"([^"]+)"', quantities) if quantities else []
        part_list = re.findall(r'"([^"]+)"', parts) if parts else []
        
        ingredients = []
        for j in range(min(len(qty_list), len(part_list))):
            ingredients.append(f"{qty_list[j]} {part_list[j]}")
        
        ingredients_text = ", ".join(ingredients)
        instructions = recipe['RecipeInstructions']
        
        images = recipe.get('Images', '')
        image_list = re.findall(r'"(https://[^"]+)"', images) if images else []
        
        text = f"Title: {title}\nIngredients: {ingredients_text}\nInstructions: {instructions}"
        
        try:
            body = {"inputText": text}
            response = bedrock.invoke_model(
                modelId="amazon.titan-embed-text-v1",
                body=json.dumps(body),
                contentType="application/json"
            )
            result = json.loads(response['body'].read())
            embedding = result['embedding']
        except Exception as e:
            print(f"Error generating embedding for recipe {i}: {e}")
            continue
        
        if i % 500 == 0 and i > 0:
            print(f"Generated {i} embeddings so far...")
        
        vectors.append({
            "id": f"recipe_{i}",
            "values": embedding,
            "metadata": {
                "title": str(title),
                "ingredients": ingredients_text,
                "instructions": str(instructions),
                "cook_time": str(recipe.get('CookTime', '') or ''),
                "prep_time": str(recipe.get('PrepTime', '') or ''),
                "images": image_list[:3] if image_list else [],
                "description": str(recipe.get('Description', '') or ''),
                "category": str(recipe.get('RecipeCategory', '') or ''),
                "rating": float(recipe.get('AggregatedRating') or 0),
                "servings": int(recipe.get('RecipeServings') or 0)
            }
        })
    
    print(f"\nFinished processing {len(vectors)} recipes. Starting upload to Pinecone...")
    
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)
        print(f"Uploaded batch {i//batch_size + 1}/{(len(vectors) + batch_size - 1)//batch_size}")
    
    print(f"Setup complete! Uploaded {len(vectors)} recipes.")

if __name__ == "__main__":
    process_recipes()