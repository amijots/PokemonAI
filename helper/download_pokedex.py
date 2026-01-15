import requests
import json
import time
import os

# CONFIGURATION
# Set to high number to download ALL pokemon (1000+), or an integer (e.g., 151) for Gen 1.
POKEMON_LIMIT = 1025
OFFSET = 0 # Used to skip to later generations (e.g., 151 for Gen 2)
OUTPUT_FILE = "./pokedex/pokedex.json"

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
    """Fetches and parses the evolution chain recursively, handling ALL evolution conditions."""
    data = fetch_json(chain_url)
    if not data:
        return "Unknown"
    
    chain = data['chain']
    evo_list = []
    
    def parse_chain(node):
        species_name = clean_name(node['species']['name']).title()
        
        # Check if there are evolutions
        if node['evolves_to']:
            for next_node in node['evolves_to']:
                next_species_name = clean_name(next_node['species']['name']).title()
                
                # Some pokmeon have empty details (like babies/base forms in certain contexts), skip if empty
                if not next_node['evolution_details']:
                    continue
                    
                # We typically take the first evolution method listed (index 0)
                # In rare cases there are multiple ways to get to the SAME pokemon, 
                # but usually index 0 is the standard way.
                details = next_node['evolution_details'][0]
                
                # --- 1. DETERMINE THE BASE TRIGGER ---
                trigger = details.get('trigger', {}).get('name')
                conditions = [] # We will add requirements to this list
                
                base_action = "evolving" # Fallback
                
                if trigger == "level-up":
                    base_action = "leveling up"
                    if details.get('min_level'):
                        conditions.append(f"starting at level {details['min_level']}")
                
                elif trigger == "trade":
                    base_action = "trading"
                    if details.get('trade_species'):
                        tr_species = clean_name(details['trade_species']['name'])
                        conditions.append(f"with {tr_species}")
                        
                elif trigger == "use-item":
                    item_name = clean_name(details.get('item', {}).get('name', 'unknown item'))
                    base_action = f"using {item_name}"
                    
                elif trigger == "shed":
                    base_action = "shedding shell (needs space in party)"
                    
                elif trigger == "other":
                    base_action = "special condition"

                # --- 2. CHECK ALL ADDITIVE CONDITIONS ---
                
                # Time of Day (e.g., Umbreon)
                if details.get('time_of_day'):
                    conditions.append(f"during the {details['time_of_day']}")

                # Held Item (e.g., Sneasel, Trade evos)
                if details.get('held_item'):
                    item = clean_name(details['held_item']['name'])
                    conditions.append(f"while holding {item}")

                # Friendship/Happiness (e.g., Pichu)
                if details.get('min_happiness'):
                    conditions.append("with high friendship")

                # Affection (e.g., Sylveon)
                if details.get('min_affection'):
                    conditions.append("with high affection")

                # Beauty (e.g., Feebas)
                if details.get('min_beauty'):
                    conditions.append("with high beauty")

                # Location (e.g., Leafeon/Glaceon)
                if details.get('location'):
                    loc = clean_name(details['location']['name'])
                    conditions.append(f"at {loc}")

                # Known Move (e.g., Tangela, Yanma)
                if details.get('known_move'):
                    move = clean_name(details['known_move']['name'])
                    conditions.append(f"knowing the move {move}")

                # Known Move Type (e.g., Sylveon needs Fairy move)
                if details.get('known_move_type'):
                    m_type = clean_name(details['known_move_type']['name'])
                    conditions.append(f"knowing a {m_type} type move")

                # Gender (e.g., Gallade/Froslass)
                # 1 = Female, 2 = Male (per PokeAPI docs)
                gender = details.get('gender')
                if gender == 1:
                    conditions.append("(female only)")
                elif gender == 2:
                    conditions.append("(male only)")

                # Weather (e.g., Sliggoo)
                if details.get('needs_overworld_rain'):
                    conditions.append("while raining")

                # Upside Down (e.g., Inkay)
                if details.get('turn_upside_down'):
                    conditions.append("while holding the console upside down")

                # Party Species (e.g., Mantyke needs Remoraid)
                if details.get('party_species'):
                    p_species = clean_name(details['party_species']['name'])
                    conditions.append(f"with {p_species} in party")
                
                # Party Type (e.g., Pancham needs Dark type)
                if details.get('party_type'):
                    p_type = clean_name(details['party_type']['name'])
                    conditions.append(f"with a {p_type} type in party")

                # Relative Physical Stats (e.g., Tyrogue)
                # 1: Atk > Def, -1: Def > Atk, 0: Atk = Def
                stats_relation = details.get('relative_physical_stats')
                if stats_relation == 1:
                    conditions.append("if Attack > Defense")
                elif stats_relation == -1:
                    conditions.append("if Defense > Attack")
                elif stats_relation == 0:
                    conditions.append("if Attack = Defense")

                # --- 3. CONSTRUCT THE SENTENCE ---
                
                # Join all conditions with spaces
                condition_string = " ".join(conditions)
                
                # Make formatting clean
                if condition_string:
                    final_method = f"{base_action} {condition_string}"
                else:
                    final_method = base_action

                # Clean up double spaces if any
                final_method = " ".join(final_method.split())

                evo_string = f"{species_name} evolves into {next_species_name} via {final_method}"
                evo_list.append(evo_string)
                
                # Recursively parse the next link in the chain
                parse_chain(next_node)
        
    parse_chain(chain)
    
    # Return formatted string
    return ". ".join(evo_list) + "." if evo_list else "This Pokemon does not evolve."

def clean_name(name):
        """Helper to replace hyphens with spaces."""
        return name.replace('-', ' ') if name else "unknown"

def clean_text(text):
    """Removes newlines and form feeds from PokeAPI flavor text."""
    return text.replace('\n', ' ').replace('\f', ' ').strip()

def main():
    access = "w"
    # Check if pokedex was populated, if so, then we'll append to the file
    # CAN'T APPEND SINCE JSON WILL ADD IT AS ANOTHER LIST INSTEAD OF APPENDING TO THE EXISTING LIST
    # if os.path.exists(OUTPUT_FILE):
    #     access = "a"
    #     with open(OUTPUT_FILE, "r", encoding='utf-8') as f:
    #         OFFSET = len(json.load(f))
    #     print(f"📂 Existing Pokedex found with {OFFSET} entries. Appending")
    print(f"🚀 Starting Pokedex download (Limit: {POKEMON_LIMIT})...")

    # 1. Get the list of all Pokemon
    list_url = f"https://pokeapi.co/api/v2/pokemon?limit={POKEMON_LIMIT}&offset={OFFSET}"
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

        processed_variants = [clean_name(v['pokemon']['name']) for v in s_data['varieties'][1:]] # Skip first as it's the default form

        # 5. Format Data for the LLM
        # We flatten the structure so the LLM can read it easily.
        entry = {
            "name": name.capitalize(),
            "id": p_data['id'],
            "types": [t['type']['name'] for t in p_data['types']],
            "color": s_data['color']['name'],
            "shape": s_data['shape']['name'],
            "abilities": [a['ability']['name'] for a in p_data['abilities']],
            "stats": {s['stat']['name']: s['base_stat'] for s in p_data['stats']},
            "moves": [m['move']['name'] for m in p_data['moves']],
            "variants": processed_variants,
            "description": description,
            "evolution_info": evolution_text,
            # Create a "blob" of text for the Vector DB to index later
            "search_content": f"Name: {name.capitalize()}. Color: {s_data['color']['name']}. Shape: {s_data['shape']['name']}. Types: {'/'.join([t['type']['name'] for t in p_data['types']])}. Abilities: {', '.join([a['ability']['name'] for a in p_data['abilities']])}. Stats: {", ".join([f'{s['stat']['name'].capitalize()} {s['base_stat']}' for s in p_data['stats']])}. {"Variants: No Variants" if not processed_variants else "Variants: " }{', '.join(processed_variants)}. Description: {description} Evolution: {evolution_text}"
        }
        
        final_pokedex.append(entry)
        
        # Be nice to the API
        time.sleep(0.1)
    # access = "w"
    # # Check if pokedex was populated, if so, then we'll append to the file
    # if os.path.exists(OUTPUT_FILE):
    #     access = "a"
    with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
        json.dump(final_pokedex, f, indent=4)

    print(f"\n✅ Done! Saved {len(final_pokedex)} entries to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()