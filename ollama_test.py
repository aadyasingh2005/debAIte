import ollama

try:
    # Test connection
    models = ollama.list()
    print("Available models:", models)
    
    # Test chat
    response = ollama.chat(
        model='phi3',
        messages=[{'role': 'user', 'content': 'Hello! Can you tell me about AI?'}]
    )
    print("Response:", response['message']['content'])
    
except Exception as e:
    print(f"Error: {e}")
