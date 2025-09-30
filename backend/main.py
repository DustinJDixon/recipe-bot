import json
import boto3
import pinecone
from pinecone import Pinecone

def get_secret(secret_name):
    try:
        client = boto3.client('secretsmanager', region_name='us-east-1')
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except Exception as e:
        print(f"Error getting secret: {e}")
        return None

def get_embedding(text):
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        body = {
            "inputText": text
        }
        
        response = bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v1",
            body=json.dumps(body),
            contentType="application/json"
        )
        
        result = json.loads(response['body'].read())
        return result['embedding']
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def search_recipes(query, top_k=5):
    try:
        query_embedding = get_embedding(query)
        if not query_embedding:
            return []
        
        api_key = get_secret('pinecone-api-key')
        if not api_key:
            return []
            
        pc = Pinecone(api_key=api_key)
        index = pc.Index("recipe-embeddings-titan")
        
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        return results['matches']
    except Exception as e:
        print(f"Error searching recipes: {e}")
        return []

def generate_conversational_response(query, recipes, conversation_history, user_wants_questions=False, dietary_restrictions=False):
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        conversation_context = ""
        if conversation_history:
            conversation_context = "Previous conversation:\n"
            for msg in conversation_history[-10:]: 
                conversation_context += f"{msg['role'].title()}: {msg['content']}\n"
            conversation_context += "\n"
        
        recipe_context = ""
        if recipes:
            recipe_context = "Available recipes that match:\n"
            for i, recipe in enumerate(recipes, 1):
                metadata = recipe['metadata']
                recipe_context += f"\n{i}. {metadata['title']}\n"
                recipe_context += f"   Category: {metadata.get('category', 'N/A')}\n"
                recipe_context += f"   Cook Time: {metadata.get('cook_time', 'N/A')}\n"
                recipe_context += f"   Rating: {metadata.get('rating', 'N/A')}/5\n"
                recipe_context += f"   Ingredients: {metadata['ingredients'][:100]}...\n"
        
        is_early_conversation = len(conversation_history) < 4
        has_specific_details = any(word in query.lower() for word in ['chicken', 'beef', 'pasta', 'italian', 'chinese', 'healthy', 'quick', 'minutes', 'vegetarian', 'vegan'])
        
        if user_wants_questions or dietary_restrictions:
            prompt = f"""You are a helpful, conversational recipe assistant. The user wants you to ask more questions or has mentioned dietary restrictions.

{conversation_context}Current user message: "{query}"

Instructions:
- Look at the conversation history to see what you already know (meal type, cuisine, dietary needs, etc.)
- If they mentioned dietary restrictions (gluten, dairy, vegan, etc.), acknowledge it and ask a related follow-up question
- Ask ONE specific follow-up question that builds on the conversation and avoids repeating what you already know
- Focus on new details like: spice level, cooking method, specific ingredients they have, cooking skill level, texture preferences
- Be friendly and conversational
- Don't suggest any recipes - just ask a thoughtful question
- NEVER repeat questions about things already established (meal type, cuisine, etc.)

Response:"""
        else:
            prompt = f"""You are a helpful, conversational recipe assistant. Your goal is to have a natural conversation and suggest recipes when appropriate.

{conversation_context}Current user message: "{query}"

{recipe_context}

Instructions:
- Be conversational and friendly, like a knowledgeable cooking friend
- If the user mentions a specific dish (pizza, burger, pasta, etc.), suggest recipes immediately
- If they're vague ("something quick", "dinner"), ask follow-up questions:
  * What meal are they planning?
  * How much time do they have?
  * Any dietary preferences or restrictions?
  * What type of cuisine they prefer?
- When you have recipes to suggest, mention the recipe name clearly so it can be clicked
- Ask one thoughtful question at a time when more info is needed
- Be encouraging and make cooking sound fun

Response:"""
        
        body = {
            "prompt": prompt,
            "max_tokens_to_sample": 400,
            "temperature": 0.8
        }
        
        response = bedrock.invoke_model(
            modelId="anthropic.claude-instant-v1",
            body=json.dumps(body),
            contentType="application/json"
        )
        
        result = json.loads(response['body'].read())
        return result['completion']
    except Exception as e:
        print(f"Error generating response: {e}")
        if user_wants_questions or dietary_restrictions:
            if dietary_restrictions:
                if 'gluten' in query.lower() or 'flour' in query.lower():
                    return "Got it - you need gluten-free options! Do you prefer naturally gluten-free dishes like rice-based meals, or are you okay with gluten-free substitutes?"
                elif 'dairy' in query.lower():
                    return "Understood - no dairy! Are you looking for naturally dairy-free dishes or recipes that can be made with dairy alternatives?"
                elif 'vegan' in query.lower():
                    return "Perfect - vegan it is! Do you prefer hearty plant-based proteins like beans and lentils, or lighter vegetable-focused dishes?"
            else:
                conversation_text = ' '.join([msg['content'] for msg in conversation_history[-4:]])
                if 'italian' in conversation_text.lower():
                    return "Since you like Italian food, are you in the mood for something pasta-based, or would you prefer something like risotto or a hearty soup?"
                elif 'mexican' in conversation_text.lower():
                    return "For Mexican food, do you prefer something mild and creamy, or are you up for some spice and heat?"
                else:
                    return "What cooking method sounds good to you - something you can make in one pan, or are you okay with a few steps?"
        elif recipes:
            response = f"Great! I found some recipes that might work. Here are my top suggestions:\n\n"
            for i, recipe in enumerate(recipes[:3], 1):
                metadata = recipe['metadata']
                response += f"{i}. {metadata['title']} (⭐ {metadata.get('rating', 'N/A')}/5)\n"
            response += "\nWhich one sounds good, or would you like me to ask a few more questions to find something even better?"
            return response
        elif len(conversation_history) < 2:
            return "I'd love to help you find the perfect recipe! What meal are you planning - breakfast, lunch, or dinner?"
        elif len(conversation_history) < 4:
            return "Tell me a bit more - are you in the mood for something healthy and light, or something more indulgent and comforting?"
        else:
            return "Based on what you've told me, what type of cuisine sounds good? Italian, Mexican, Asian, or something else?"

def handler(event, context):
    """Lambda handler"""
    
    try:
        body = json.loads(event['body'])
        query = body.get('query', '')
        conversation_history = body.get('conversation_history', [])
        
        if not query:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Query is required'})
            }
        
        user_wants_questions = any(phrase in query.lower() for phrase in [
            'ask more', 'more questions', 'ask questions', 'tell me more', 'something else',
            'keep asking', 'what else', 'more info', 'ask me', 'more options', 'different'
        ])
        
        dietary_restrictions = any(word in query.lower() for word in [
            'gluten', 'dairy', 'lactose', 'vegan', 'vegetarian', 'nut', 'shellfish', 'egg', 'flour', 'wheat'
        ])
        
        recipes = []
        if not user_wants_questions:
            should_search = (
                any(word in query.lower() for word in ['pizza', 'burger', 'pasta', 'sandwich', 'salad', 'soup', 'stir fry', 'tacos', 'burrito', 'sushi', 'curry', 'steak', 'chicken', 'fish', 'rice', 'noodles', 'pancakes', 'eggs', 'omelet']) or
                any(word in query.lower() for word in ['recipe', 'cook', 'make', 'prepare']) or
                ('suggest' in query.lower() and 'recipe' in query.lower()) or
                ('recommend' in query.lower() and 'recipe' in query.lower()) or
                (len(conversation_history) >= 2 and any(cuisine in query.lower() for cuisine in ['italian', 'mexican', 'chinese', 'indian', 'thai', 'french', 'american', 'asian']))
            )
            
            if should_search:
                search_query = query
                if len(conversation_history) >= 2:
                    recent_context = ' '.join([msg['content'] for msg in conversation_history[-4:] if msg['role'] == 'user'])
                    search_query = f"{recent_context} {query}"
                    
                    if dietary_restrictions:
                        if 'gluten' in query.lower() or 'flour' in query.lower() or 'wheat' in query.lower():
                            search_query += " gluten-free no flour no wheat"
                        if 'dairy' in query.lower() or 'lactose' in query.lower():
                            search_query += " dairy-free lactose-free"
                        if 'vegan' in query.lower():
                            search_query += " vegan plant-based"
                else:
                    search_query = query
                            
                print(f"Searching for: {search_query}")
                recipes = search_recipes(search_query)
                print(f"Found {len(recipes)} recipes")
        
        answer = generate_conversational_response(query, recipes, conversation_history, user_wants_questions, dietary_restrictions)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'answer': answer,
                'recipes': [r['metadata'] for r in recipes[:3]] if recipes and not (user_wants_questions and not dietary_restrictions) else []
            })
        }
        
    except Exception as e:
        print(f"Handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Server error: {str(e)}"})
        }