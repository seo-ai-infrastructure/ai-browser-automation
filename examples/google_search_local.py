from browser_use.llm.openai.chat import ChatOpenAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Ollama base URL from environment variable, with a default
ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

async def main():
    # Initialize the agent using the local LLM endpoint
    agent = Agent(
        task="Go to Google, search for 'browser-use github', and return the first result.",
        llm=ChatOpenAI(
            base_url=ollama_base_url,
            api_key="ollama",  # placeholder - Ollama ignores this
            model="llama4:scout",  # Using Llama4:scout - best for browser automation
            temperature=0.7,
        ),
    )
    
    # Run the agent and get the result
    result = await agent.run()
    print("Task Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
