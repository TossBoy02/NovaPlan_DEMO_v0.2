import json
from pathlib import Path
from data_ingest import DATA_DIR, load_esco_occupations_and_skills, load_onet_skills_and_tasks

def generate_careers_json():
    print("Loading ESCO data...")
    ESCO = load_esco_occupations_and_skills(DATA_DIR / 'esco')
    print(f"Loaded {len(ESCO)} ESCO occupations.")
    
    print("Loading O*NET data...")
    ONET = load_onet_skills_and_tasks(DATA_DIR)
    print(f"Loaded {len(ONET)} O*NET occupations.")

    combined = []
    print("Combining datasets...")
    
    # Start with ESCO as base
    for occ, val in ESCO.items():
        combined.append({ 
            'career': occ, 
            'skills': val.get('skills', []), 
            'tasks': [], # ESCO loader doesn't currently return tasks, so init empty
            'education': [], 
            'description': '' 
        })
    
    # Enrich with O*NET
    enriched_count = 0
    added_count = 0
    
    for occ, val in ONET.items():
        # find nearest existing by simple name containment
        match = next((c for c in combined if occ.lower() in c['career'].lower() or c['career'].lower() in occ.lower()), None)
        if match:
            merged_skills = sorted({*match['skills'], *val.get('skills', [])})
            match['skills'] = [s.lower() for s in merged_skills]
            # Merge tasks - append new ones
            existing_tasks = set(match.get('tasks', []))
            new_tasks = [t for t in val.get('tasks', []) if t not in existing_tasks]
            match['tasks'] = match.get('tasks', []) + new_tasks
            enriched_count += 1
        else:
            combined.append({ 
                'career': occ, 
                'skills': [s.lower() for s in val.get('skills', [])], 
                'tasks': val.get('tasks', []),
                'education': [], 
                'description': '' 
            })
            added_count += 1
            
    print(f"Enriched {enriched_count} careers, added {added_count} new careers from O*NET.")
    print(f"Total careers: {len(combined)}")

    output_path = DATA_DIR / 'careers.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2)
    
    print(f"Successfully saved to {output_path}")

if __name__ == "__main__":
    generate_careers_json()
