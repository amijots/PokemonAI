import json
import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

# CONFIGURATION
JSON_FILE = "./pokedex/pokedex.json"
DB_DIRECTORY = "./pokedex_db"  # Folder where the vector DB will be saved

def main():
    # 1. Load the Raw Data
    if not os.path.exists(JSON_FILE):
        print(f"❌ Error: {JSON_FILE} not found. Run the download script first.")
        return

    print(f"📂 Loading data from {JSON_FILE}...")
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        pokedex_data = json.load(f)

    # 2. Convert to LangChain 'Documents'
    # We split the data: 'search_content' goes to Blob, 'stats/type' goes to Metadata
    documents = []
    
    for p in pokedex_data:
        # A. The Blob (What the AI reads)
        # We use the pre-made string from your download script
        text_blob = p.get('search_content')
        
        # B. The Metadata (What the Code filters)
        # We flatten the stats so they are easier to query (e.g. metadata['speed'] > 50)
        metadata = {
            "name": p['name'],
            "id": p['id'],
            # Store primary type for easy filtering
            "type": p['types'][0] if p['types'] else "Unknown", 
            "color": p['color'],
            "shape": p['shape'],
            "ability": p['abilities'][0],
            # Add stats individually for "SelfQueryRetriever" filtering
            "hp": p['stats']['hp'],
            "attack": p['stats']['attack'],
            "defense": p['stats']['defense'],
            "speed": p['stats']['speed'],
            "special_attack": p['stats']['special-attack'],
            "special_defense": p['stats']['special-defense']
        }
        
        doc = Document(page_content=text_blob, metadata=metadata)
        documents.append(doc)

    print(f"📝 Prepared {len(documents)} documents.")

    # 3. Initialize the Embedding Model
    # IMPORTANT: Use 'nomic-embed-text' for speed/quality. 
    # If you haven't pulled it yet, run: ollama pull nomic-embed-text
    print("🧠 Initializing Embedding Model (nomic-embed-text)...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # 4. Create (or Update) the Vector Database
    print(f"💾 Saving to {DB_DIRECTORY}... (This might take a minute)")
    
    # from_documents automatically:
    # 1. Sends text to Ollama -> Gets Vectors
    # 2. Saves Vectors + Metadata to the folder
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=DB_DIRECTORY,
        collection_name="pokedex_collection" 
    )

    print("✅ Success! Database created.")
    print(f"   To use it, load Chroma with persist_directory='{DB_DIRECTORY}'")

if __name__ == "__main__":
    main()