import json
import os

# CONFIGURATION
INPUT_FILE = "./pokedex/pokedex.json"
OUTPUT_FILE = "./pokedex/pokedex_cleaned.json" # We save to a new file first for safety

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    print(f"📂 Loading {INPUT_FILE}...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        pokedex_data = json.load(f)

    print(f"🧹 Cleaning move names for {len(pokedex_data)} Pokemon...")
    
    count_moves_fixed = 0

    for p in pokedex_data:
        # 1. Get the list of moves
        raw_moves = p.get('moves', [])
        
        # 2. Replace hyphens with spaces
        clean_moves = [move.replace('-', ' ') for move in raw_moves]
        
        # 3. Save it back
        p['moves'] = clean_moves
        count_moves_fixed += len(clean_moves)

    # 4. Save the new file
    print(f"💾 Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(pokedex_data, f, indent=4)

    print(f"✅ Done! Processed {count_moves_fixed} moves.")
    print(f"👉 Please rename '{OUTPUT_FILE}' to '{INPUT_FILE}' to use it with your app.")

if __name__ == "__main__":
    main()