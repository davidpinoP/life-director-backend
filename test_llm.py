import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load env variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print(f"Testing with API Key: {api_key[:10]}...{api_key[-5:] if api_key else 'None'}")

async def test_llm():
    try:
        client = AsyncOpenAI(api_key=api_key)
        print("Sending request to OpenAI...")
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a test."},
                {"role": "user", "content": "Say hello."}
            ],
            max_tokens=10
        )
        
        print("✅ Success!")
        print("Response:", response.choices[0].message.content)
        
    except Exception as e:
        print("❌ Error:")
        print(str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm())
