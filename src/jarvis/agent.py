import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
# from langgraph.prebuilt import create_react_agent
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import jarvis_tools
from dotenv import load_dotenv

load_dotenv()

# Initialize the SQLite memory saver for persistent memory
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False) #
memory = SqliteSaver(conn) #

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

system_instruction = """
You are Jarvis, a highly intelligent and capable AI personal assistant. 
You can remember past conversations, access the user's system to open applications, read local .txt/.pdf files, change system volume, play music dynamically from YouTube, and visually analyze their screen. 
Always be concise, professional, and helpful. 
"""

# jarvis_agent = create_react_agent(
#     model=llm,
#     tools=jarvis_tools,
#     prompt=system_instruction,
#     # state_modifier=system_instruction,
#     checkpointer=memory
# )

jarvis_agent = create_agent(
    model=llm,
    tools=jarvis_tools,
    system_prompt=system_instruction, # 'prompt' is now 'system_prompt'
    checkpointer=memory
)