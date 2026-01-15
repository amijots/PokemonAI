import requests
import json
import time
import os

# CONFIGURATION
# Set to None to download ALL pokemon (1000+), or an integer (e.g., 151) for Gen 1.
POKEMON_LIMIT = 1 
OUTPUT_FILE = "pokedex.json"

def fetch_json(url):
    """Helper to fetch JSON with simple error handling and rate limiting."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_evolution_chain(chain_url):
    """Fetches and parses the evolution chain recursively."""
    data = fetch_json(chain_url)
    if not data:
        return "Unknown"
    
    chain = data['chain']
    evo_list = []
    
    def parse_chain(node):
        species_name = node['species']['name']
        
        # Check if there are evolutions
        if node['evolves_to']:
            for next_node in node['evolves_to']:
                # Get the details (Level up, Stone, etc.)
                details = next_node['evolution_details'][0]
                trigger = details.get('trigger', {}).get('name')
                min_level = details.get('min_level')
                item = details.get('item')
                item_name = item['name'] if item else None
                
                method = "unknown means"
                if trigger == "level-up" and min_level:
                    method = f"level {min_level}"
                elif item_name:
                    method = f"using {item_name}"
                elif trigger == "trade":
                    method = "trading"
                
                evo_string = f"{species_name} evolves into {next_node['species']['name']} via {method}"
                evo_list.append(evo_string)
                parse_chain(next_node) # Recursive call
        
    parse_chain(chain)
    return ". ".join(evo_list) if evo_list else "This Pokemon does not evolve."

def clean_text(text):
    """Removes newlines and form feeds from PokeAPI flavor text."""
    return text.replace('\n', ' ').replace('\f', ' ').strip()

def main():
    print(f"🚀 Starting Pokedex download (Limit: {POKEMON_LIMIT})...")
    
    # 1. Get the list of all Pokemon
    list_url = f"https://pokeapi.co/api/v2/pokemon?limit={POKEMON_LIMIT}"
    pokemon_list = fetch_json(list_url)['results']
    
    final_pokedex = []
    
    for index, p in enumerate(pokemon_list):
        name = p['name']
        print(f"[{index+1}/{POKEMON_LIMIT}] Fetching {name}...")
        
        # 2. Get Main Pokemon Data (Types, Stats)
        p_data = fetch_json(p['url'])
        if not p_data: continue

        # 3. Get Species Data (Description, Evolution URL)
        species_url = p_data['species']['url']
        s_data = fetch_json(species_url)
        if not s_data: continue
        
        # Extract English Flavor Text (Description)
        description = "No description available."
        for entry in s_data['flavor_text_entries']:
            if entry['language']['name'] == 'en':
                description = clean_text(entry['flavor_text'])
                break # Just take the first English one found
        
        # 4. Get Evolution Chain (Only if we haven't cached this chain, but for simplicity we fetch)
        # Note: In a production app, you would cache this URL to avoid re-fetching the same chain 3 times.
        evo_chain_url = s_data['evolution_chain']['url']
        evolution_text = get_evolution_chain(evo_chain_url)

        # 5. Format Data for the LLM
        # We flatten the structure so the LLM can read it easily.
        entry = {
            "name": name.capitalize(),
            "id": p_data['id'],
            "types": [t['type']['name'] for t in p_data['types']],
            "stats": {s['stat']['name']: s['base_stat'] for s in p_data['stats']},
            "description": description,
            "evolution_info": evolution_text,
            # Create a "blob" of text for the Vector DB to index later
            "search_content": f"Name: {name.capitalize()}. Types: {', '.join([t['type']['name'] for t in p_data['types']])}. Stats: {", ".join([f'{s['stat']['name']} {s['base_stat']}' for s in p_data['stats']])}. Description: {description} Evolution: {evolution_text}"
        }

        final_pokedex.append(entry)
        
        # Be nice to the API
        time.sleep(0.1)

    # 6. Save to File
    with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
        json.dump(final_pokedex, f, indent=4)
    
    print(f"\n✅ Done! Saved {len(final_pokedex)} entries to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()