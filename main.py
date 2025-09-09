# Before running, make sure to install the required libraries:
# pip install langchain-google-genai langchain langchain_community
# You will also need to have your GOOGLE_API_KEY set as an environment variable.

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define a simple tool that the agent can use.
# This tool simulates a basic calculator.
@tool
def calculate(expression: str) -> str:
    """Evaluates a mathematical expression."""
    try:
        # Using eval() for a simple demonstration.
        # In a production environment, a safer method should be used.
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

# Initialize the ChatGoogleGenerativeAI model.
# Make sure your GOOGLE_API_KEY is configured in your environment.
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# Define the tools available to the agent.
tools = [calculate]

# Create the prompt template for the agent.
# The `tools` and `tool_names` variables are dynamically inserted by LangChain.
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant. You have access to a calculator tool."),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# Create the agent using the tool-calling method.
# This function automatically configures the LLM to use the provided tools.
agent = create_tool_calling_agent(llm, tools, prompt)

# Create the AgentExecutor.
# This is the runnable object that executes the agent and its tools.
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Define the main function to run the agent.
if __name__ == "__main__":
    # Example usage:
    # 1. A simple question that doesn't require a tool.
    print("Running with a simple query:")
    simple_response = agent_executor.invoke({"input": "What is the capital of France?"})
    print(f"Result: {simple_response['output']}\n")

    # # 2. A question that requires the agent to use the 'calculate' tool.
    # print("Running with a query that requires the 'calculate' tool:")
    # math_response = agent_executor.invoke({"input": "What is 120 times 5?"})
    # print(f"Result: {math_response['output']}\n")

    # # 3. Another question that requires the tool.
    # print("Running with a more complex math query:")
    # complex_math_response = agent_executor.invoke({"input": "What is the square root of 64?"})
    # print(f"Result: {complex_math_response['output']}\n")

    # # 4. A query with chat history.
    # print("Running with chat history:")
    # chat_history = [HumanMessage(content="What is 50 divided by 2?"), AIMessage(content="The result is 25.0")]
    # history_response = agent_executor.invoke({"input": "Now multiply that by 10.", "chat_history": chat_history})
    # print(f"Result: {history_response['output']}\n")
