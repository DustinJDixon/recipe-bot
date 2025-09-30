"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  role: string;
  content: string;
  recipes?: Recipe[];
}

interface Recipe {
  title: string;
  ingredients: string;
  instructions: string;
  cook_time: string;
  prep_time: string;
  rating: number;
  images: string[];
  description: string;
  category: string;
  servings: number;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Send initial greeting when component mounts
    if (messages.length === 0) {
      const initialMessage = {
        role: "assistant" as const,
        content: "Hi there! I'm your personal recipe assistant. I'd love to help you find the perfect dish to cook today! 🍳\n\nTo get started, tell me: What kind of mood are you in for cooking? Are you looking for something quick and easy, or do you have time for something more elaborate?",
        recipes: []
      };
      setMessages([initialMessage]);
    }
  }, []);

  async function sendMessage() {
    if (!input.trim() || isLoading) return;
    
    const userMessage = { role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '');
      const res = await fetch(`${apiUrl}/chat`, {
        method: "POST",
        body: JSON.stringify({ 
          query: input,
          conversation_history: messages.map(m => ({ role: m.role, content: m.content }))
        }),
        headers: { "Content-Type": "application/json" },
      });
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data = await res.json();
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: data.answer,
        recipes: data.recipes || []
      }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I'm having trouble connecting. Please try again." }]);
    } finally {
      setIsLoading(false);
    }
    
    setInput("");
  }

  const renderMessageContent = (message: Message) => {
    if (!message.recipes || message.recipes.length === 0) {
      return message.content;
    }

    // Parse content and add recipe links
    let content = message.content;
    message.recipes.forEach((recipe, index) => {
      const recipeTitle = recipe.title;
      if (content.includes(recipeTitle)) {
        content = content.replace(
          recipeTitle,
          `<button class="recipe-link text-orange-600 hover:text-orange-800 underline font-semibold" data-recipe-index="${index}">${recipeTitle}</button>`
        );
      }
    });

    return (
      <div 
        dangerouslySetInnerHTML={{ __html: content }}
        onClick={(e) => {
          const target = e.target as HTMLElement;
          if (target.classList.contains('recipe-link')) {
            const recipeIndex = parseInt(target.getAttribute('data-recipe-index') || '0');
            setSelectedRecipe(message.recipes![recipeIndex]);
          }
        }}
      />
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 p-6 text-white">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <span className="text-2xl">🍳</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold">RecipeBot</h1>
              <p className="text-orange-100">Your AI cooking companion</p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="h-96 overflow-y-auto p-6 space-y-4 bg-gray-50">
          {messages.length === 0 && (
            <div className="text-center text-gray-900 mt-20">
              <div className="text-6xl mb-4">👋</div>
              <h3 className="text-xl font-semibold mb-2">Welcome to RecipeBot!</h3>
              <p>I'll help you find the perfect recipe by asking a few questions about your preferences.</p>
              <div className="flex flex-wrap justify-center gap-2 mt-4">
                {["Dinner tonight", "Something healthy", "Quick and easy", "Comfort food"].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setInput(suggestion)}
                    className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm hover:bg-orange-200 transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {messages.map((message, i) => (
            <div key={i} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                message.role === "user" 
                  ? "bg-gradient-to-r from-orange-500 to-red-500 text-white" 
                  : "bg-white shadow-md border border-gray-200"
              }`}>
                <div className="flex items-start space-x-2">
                  {message.role === "assistant" && (
                    <div className="w-6 h-6 bg-gradient-to-r from-orange-500 to-red-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-white text-xs">🤖</span>
                    </div>
                  )}
                  <div className={`text-sm leading-relaxed ${
                    message.role === "assistant" ? "text-gray-900" : ""
                  }`}>
                    {renderMessageContent(message)}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white shadow-md border border-gray-200 rounded-2xl px-4 py-3 max-w-xs">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 bg-gradient-to-r from-orange-500 to-red-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-xs">🤖</span>
                  </div>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-6 bg-white border-t border-gray-200">
          <div className="flex space-x-4">
            <input
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent placeholder-gray-500 text-gray-900"
              placeholder="Tell me what you're in the mood for..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl hover:from-orange-600 hover:to-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium shadow-lg hover:shadow-xl"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                "Send"
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Recipe Detail Modal */}
      {selectedRecipe && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="bg-gradient-to-r from-orange-500 to-red-500 p-6 text-white rounded-t-2xl">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold mb-2">{selectedRecipe.title}</h2>
                  <div className="flex items-center space-x-4 text-orange-100">
                    <span>⭐ {selectedRecipe.rating}/5</span>
                    <span>🍽️ {selectedRecipe.servings} servings</span>
                    <span>⏱️ {selectedRecipe.cook_time}</span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedRecipe(null)}
                  className="text-white hover:text-orange-200 text-2xl"
                >
                  ×
                </button>
              </div>
            </div>
            
            <div className="p-6">
              {selectedRecipe.images.length > 0 && (
                <img 
                  src={selectedRecipe.images[0]} 
                  alt={selectedRecipe.title}
                  className="w-full h-48 object-cover rounded-xl mb-6"
                />
              )}
              
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Ingredients</h3>
                <div className="bg-gray-50 p-4 rounded-xl">
                  <ul className="text-gray-700 space-y-1">
                    {selectedRecipe.ingredients.split(', ').map((ingredient, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-orange-500 mr-2">•</span>
                        <span>{ingredient}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Instructions</h3>
                <div className="bg-gray-50 p-4 rounded-xl">
                  <ol className="text-gray-700 space-y-3">
                    {selectedRecipe.instructions
                      .replace(/^c\(|\)$/g, '') // Remove c( and )
                      .split('", "')
                      .map(step => step.replace(/^"|"$/g, '')) // Remove quotes
                      .map((step, index) => (
                        <li key={index} className="flex items-start">
                          <span className="bg-orange-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-semibold mr-3 mt-0.5 flex-shrink-0">
                            {index + 1}
                          </span>
                          <span>{step}</span>
                        </li>
                      ))
                    }
                  </ol>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}