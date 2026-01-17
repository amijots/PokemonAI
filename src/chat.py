import json
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import tool
from langchain_classic.tools.retriever import create_retriever_tool
from langchain_core.prompts import ChatPromptTemplate

# NEW IMPORTS FOR SELF-QUERY
from langchain_classic.chains.query_constructor.schema import AttributeInfo 
from langchain_classic.retrievers.self_query.base import SelfQueryRetriever

# --- CONFIGURATION ---
DB_DIRECTORY = "./pokedex_db"
JSON_FILE = "./pokedex/pokedex.json"
MODEL_NAME = "llama3.1" # Strongly recommended for Self-Query logic

# --- 1. LOAD RESOURCES ---

print("⏳ Loading Vector Database...")
embedding_function = OllamaEmbeddings(model="nomic-embed-text")
db = Chroma(persist_directory=DB_DIRECTORY, embedding_function=embedding_function)

print("⏳ Loading Raw Pokedex (for Move Lookups)...")
with open(JSON_FILE, "r", encoding="utf-8") as f:
    POKEDEX_DATA = json.load(f)
POKEDEX_LOOKUP = {p['name'].lower(): p for p in POKEDEX_DATA}

# --- 2. DEFINE THE SELF-QUERY RETRIEVER ---

print("🧠 Configuring Metadata Filters...")

# A. Initialize the LLM specifically for the Retriever
# We use temperature=0 because logic/math filters need to be exact, not creative.
llm_retriever = ChatOllama(model=MODEL_NAME, temperature=0)

# B. Define the Metadata Schema
# This tells the LLM what fields are available in the database to filter by.
metadata_field_info = [
    AttributeInfo(
        name="name",
        description="The name of the Pokemon",
        type="string",
    ),
    AttributeInfo(
        name="id",
        description="The unique identifier for the Pokemon",
        type="integer",
    ),
    AttributeInfo(
        name="type",
        description="The primary elemental type of the Pokemon (e.g. Fire, Water, Grass)",
        type="string",
    ),
    AttributeInfo(
        name="color",
        description="The primary color of the Pokemon (e.g. Red, Blue, Green)",
        type="string",
    ),
    AttributeInfo(
        name="shape",
        description="The shape of the Pokemon (e.g. Quadruped, Bipedal, etc.)",
        type="string",
    ),
    AttributeInfo(
        name="ability",
        description="The primary ability of the Pokemon (e.g. Overgrow, Blaze)",
        type="string",
    ),
    AttributeInfo(
        name="hp",
        description="The base HP stat",
        type="integer",
    ),
    AttributeInfo(
        name="attack",
        description="The base Attack stat",
        type="integer",
    ),
    AttributeInfo(
        name="defense",
        description="The base Defense stat",
        type="integer",
    ),
    AttributeInfo(
        name="speed",
        description="The base Speed stat",
        type="integer",
    ),
    AttributeInfo(
        name="special_attack",
        description="The base Special Attack stat",
        type="integer",
    ),
    AttributeInfo(
        name="special_defense",
        description="The base Special Defense stat",
        type="integer",
    )
]

# C. Create the Smart Retriever
# This replaces db.as_retriever()
retriever = SelfQueryRetriever.from_llm(
    llm_retriever,
    db,
    "Brief summary of Pokemon stats, lore, and evolutions", # Description of the document content
    metadata_field_info,
    verbose=True # Set to True so you can see the filter being constructed in the console
)

# --- 3. DEFINE TOOLS ---

# TOOL A: The Smart Vector Search
tool_search = create_retriever_tool(
    retriever,
    "search_pokedex_context",
    "ALWAYS USE THIS FIRST. Searches for Pokemon descriptions, stats, types. Can filter by stats (e.g. Speed > 100)."
)

# TOOL B: The Move Checker
@tool
def check_move_tool(pokemon_name: str, move_name: str):
    """
    Checks if a Pokemon can learn a specific move. 
    Input: pokemon_name (e.g. 'Charizard'), move_name (e.g. 'Solar Beam').
    """
    p_name = pokemon_name.lower().strip()
    m_name = move_name.lower().strip()
    
    if p_name not in POKEDEX_LOOKUP:
        return f"Error: Pokemon '{pokemon_name}' not found in raw database."
    
    pokemon = POKEDEX_LOOKUP[p_name]
    known_moves = set(pokemon['moves'])

    if m_name in known_moves:
        return f"✅ Yes! {pokemon_name} is able to learn {move_name}."
    else:
        return f"❌ No. {pokemon_name} cannot learn {move_name}."

tools = [tool_search, check_move_tool]

# --- 4. SETUP THE AGENT ---

print(f"🤖 Initializing Main Agent with {MODEL_NAME}...")
llm_agent = ChatOllama(model=MODEL_NAME, temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Pokemon Professor. 
    1. ALWAYS use the 'search_pokedex_context' tool first to identify the Pokemon.
    2. If the user asks about stats (e.g. 'Who is faster than 100?'), the search tool handles the filtering automatically.
    3. If the user asks if a Pokemon can learn a specific move, YOU MUST use the 'check_move_tool'.
    """),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm_agent, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- 5. START CHAT LOOP ---

print("\n🔵 Pokemon Professor Ready! (Type 'quit' to exit)")
print("------------------------------------------------")

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ["quit", "exit"]:
        break
    
    try:
        response = agent_executor.invoke({"input": user_input})
        print(f"\nProfessor: {response['output']}")
    except Exception as e:
        print(f"\n❌ Error: {e}")