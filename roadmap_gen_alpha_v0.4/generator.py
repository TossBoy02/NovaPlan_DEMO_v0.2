import json
import random
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from embeddings_index import build_skill_index, query_skill
from data_ingest import DATA_DIR, load_esco_occupations_and_skills, load_onet_skills_and_tasks
from rapidfuzz import process, fuzz

CAREERS_JSON = Path('data') / 'careers.json'

if not CAREERS_JSON.exists():
    # This should ideally not happen if the setup is correct, but we keep a minimal fallback just in case
    CAREER_DATASET = [
        {"career":"Data Analyst","skills":["python","sql","data visualization","pandas"],"education":["bachelor's"],"description":"Analyze data."},
        {"career":"Frontend Developer","skills":["javascript","react","html","css"],"education":["bootcamp","self-taught"],"description":"Build web UI."}
    ]
else:
    try:
        text = open(CAREERS_JSON,'r',encoding='utf-8').read().strip()
        CAREER_DATASET = json.loads(text) if text else None
    except Exception:
        CAREER_DATASET = None
    
    if not CAREER_DATASET:
        CAREER_DATASET = [
            {"career":"Data Analyst","skills":["python","sql","data visualization","pandas"],"education":["bachelor's"],"description":"Analyze data."},
            {"career":"Frontend Developer","skills":["javascript","react","html","css"],"education":["bootcamp","self-taught"],"description":"Build web UI."}
        ]

if CAREER_DATASET:
    SKILL_VOCAB = sorted({s.lower() for c in CAREER_DATASET for s in c.get('skills', [])})
else:
    SKILL_VOCAB = []

# Build index lazily on first request to avoid blocking app startup
from embeddings_index import EMBED_DIR


def normalize_skills(raw_skills: List[str]) -> List[str]:
    # Use embedding nearest neighbor first, fallback to fuzzy matching
    normalized = []
    for s in raw_skills:
        s = s.strip()
        # query embeddings
        try:
            nn, d = query_skill(s, k=1)
            if d[0] > 0.6:
                normalized.append(nn[0])
                continue
        except Exception:
            pass
        # fallback fuzzy
        best = process.extractOne(s, SKILL_VOCAB, scorer=fuzz.token_sort_ratio)
        normalized.append(best[0] if best else s.lower())
    # dedupe
    seen = []
    for x in normalized:
        if x not in seen:
            seen.append(x)
    return seen


from generator_core import generate_distinct_roadmaps as core_generator


def _derive_skills_from_quiz(answers: List[Dict[str, Any]]) -> List[str]:
    """Map A-D choices to indicative skills clusters; lightweight heuristic."""
    type_to_skills = {
        'A': ['python', 'analysis', 'sql', 'data visualization'],
        'B': ['communication', 'teaching', 'empathy', 'presentation'],
        'C': ['design', 'creativity', 'ui/ux', 'writing'],
        'D': ['project management', 'organization', 'planning', 'leadership'],
    }
    tallied: Dict[str, int] = {}
    for ans in answers or []:
        t = (ans.get('type') or '').upper()
        for sk in type_to_skills.get(t, []):
            tallied[sk] = tallied.get(sk, 0) + 1
    # choose top skills
    ranked = sorted(tallied.items(), key=lambda x: x[1], reverse=True)
    return [s for s, _ in ranked[:8]] if ranked else []


def _serialize_nested_steps(step):
    """Helper to recursively serialize RoadmapStep objects including children."""
    serialized_step = step.__dict__
    if 'children' in serialized_step and serialized_step['children']:
        serialized_step['children'] = [_serialize_nested_steps(s) for s in serialized_step['children']]
    return serialized_step

def _plot_roadmaps(roadmaps: List[Dict[str, Any]], output_dir: Path) -> List[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    image_urls: List[str] = []

    def enumerate_nodes(steps: List[Dict[str, Any]]):
        nodes = []  # (id, title, duration, depth, parent_id, milestones_count, tasks_count)
        edges = []  # (parent_id, child_id)
        counter = {'i': 0}

        def walk(lst, depth, parent):
            for s in lst:
                node_id = counter['i']; counter['i'] += 1
                milestones_count = len(getattr(s, 'milestones', []))
                tasks_count = len(getattr(s, 'tasks', []))
                nodes.append((node_id, getattr(s, 'title', ''), int(getattr(s, 'duration_months', 1)), 
                             depth, parent, milestones_count, tasks_count))
                
                children = getattr(s, 'children', [])
                if children:
                    for ch in children:
                        child_id = counter['i']
                        edges.append((node_id, child_id))
                        walk([ch], depth + 1, node_id)
                
        walk(steps, 0, None)
        return nodes, edges

    def layout_topdown(nodes):
        # Assign x by preorder index, y by depth (top to bottom)
        positions = {}
        x = 0
        for node_id, title, dur, depth, parent, milestones_count, tasks_count in nodes:
            positions[node_id] = (x, -depth)
            x += 1
        return positions

    def draw_tree(ax, nodes, edges, positions, title):
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlim(-1, max(pos[0] for pos in positions.values()) + 1)
        ax.set_ylim(min(pos[1] for pos in positions.values()) - 1, 1)
        
        # draw edges
        for p, c in edges:
            if p in positions and c in positions:
                x1, y1 = positions[p]
                x2, y2 = positions[c]
                ax.plot([x1, x2], [y1, y2], color="#94a3b8", linewidth=2, zorder=1, alpha=0.7)
        
        # draw nodes as boxes with enhanced information
        for node_id, label, dur, depth, parent, milestones_count, tasks_count in nodes:
            x, y = positions[node_id]
            w, h = 1.4, 1.0
            
            # Color based on depth
            colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
            color = colors[min(depth, len(colors)-1)]
            
            # Main node rectangle
            rect = plt.Rectangle((x - w/2, y - h/2), w, h, 
                               facecolor=color, alpha=0.9, 
                               edgecolor='#1e40af', linewidth=2, zorder=2)
            ax.add_patch(rect)
            
            # Node title (truncate if too long)
            display_label = label[:20] + "..." if len(label) > 20 else label
            ax.text(x, y + 0.25, display_label, color="white", fontsize=9, 
                   ha="center", va="center", zorder=3, fontweight='bold')
            
            # Duration
            ax.text(x, y + 0.05, f"{dur} mo", color="#e0e7ff", fontsize=8, 
                   ha="center", va="center", zorder=3, fontweight='bold')
            
            # Milestones count
            if milestones_count > 0:
                ax.text(x - 0.4, y - 0.2, f"🎯{milestones_count}", color="#10b981", 
                       fontsize=8, ha="center", va="center", zorder=3, fontweight='bold')
            
            # Tasks count
            if tasks_count > 0:
                ax.text(x + 0.4, y - 0.2, f"📝{tasks_count}", color="#f59e0b", 
                       fontsize=8, ha="center", va="center", zorder=3, fontweight='bold')
            
            # Add depth indicator
            depth_icons = ["📋", "🎯", "✅", "🔧", "🚀"]
            icon = depth_icons[min(depth, len(depth_icons)-1)]
            ax.text(x, y - 0.35, icon, fontsize=10, ha="center", va="center", zorder=3)
        
        # Add comprehensive legend
        legend_elements = [
            plt.Rectangle((0,0),1,1, facecolor='#3b82f6', alpha=0.9, label='Foundations'),
            plt.Rectangle((0,0),1,1, facecolor='#10b981', alpha=0.9, label='Core Skills'),
            plt.Rectangle((0,0),1,1, facecolor='#f59e0b', alpha=0.9, label='Projects'),
            plt.Rectangle((0,0),1,1, facecolor='#ef4444', alpha=0.9, label='Specializations'),
            plt.Rectangle((0,0),1,1, facecolor='#8b5cf6', alpha=0.9, label='Job Search')
        ]
        
        # Add info legend
        info_legend = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#10b981', 
                      markersize=8, label='🎯 Milestones'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#f59e0b', 
                      markersize=8, label='📝 Tasks'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#6b7280', 
                      markersize=8, label='📋 Main Steps'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#6b7280', 
                      markersize=8, label='🎯 Sub-steps'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#6b7280', 
                      markersize=8, label='✅ Tasks')
        ]
        
        # Create two legends
        legend1 = ax.legend(handles=legend_elements, loc='upper left', fontsize=7, title='Phase Colors')
        ax.add_artist(legend1)
        ax.legend(handles=info_legend, loc='upper right', fontsize=7, title='Information')
        
        ax.axis('off')

    for idx, r in enumerate(roadmaps):
        nodes, edges = enumerate_nodes(r['steps'])
        positions = layout_topdown(nodes)
        width = max(12, len(nodes) * 1.0)
        height = max(8, (max((d for _,_,_,d,_,_,_ in nodes), default=0) + 1) * 2.0)
        fig, ax = plt.subplots(figsize=(width, height))
        draw_tree(ax, nodes, edges, positions, f"{r['path_title']} — {r['focus']}")
        plt.tight_layout()
        fname = output_dir / f"roadmap_{idx+1}.png"
        fig.savefig(fname, dpi=150)
        plt.close(fig)
        image_urls.append(f"/static/roadmaps/{fname.name}")
    return image_urls


def generate_roadmaps_for_user(user_input: Dict[str,Any]) -> Dict[str,Any]:
    # Accept either explicit skills or derive from quiz answers
    provided_skills = user_input.get('skills', [])
    answers = user_input.get('answers', [])
    derived_skills = _derive_skills_from_quiz(answers)
    skills = normalize_skills(provided_skills + derived_skills)
    education = user_input.get('education','')
    summary = user_input.get('summary','')
    # ensure embedding index exists
    try:
        if not (EMBED_DIR / 'skill_index.faiss').exists():
            build_skill_index(SKILL_VOCAB)
    except Exception:
        # continue without embeddings if building fails; fuzzy fallback will still work
        pass
    # retrieve top career using embedding-aware scoring
    scored = []
    for c in CAREER_DATASET:
        cskills = [s.lower() for s in c.get('skills', [])]
        overlap = len(set(skills) & set(cskills))
        # Basic keyword nudge from summary
        kw_bonus = 0.2 if any(k in (summary or '').lower() for k in cskills[:5]) else 0
        score = overlap / max(1, len(cskills) or 1) + kw_bonus
        scored.append((c,score))
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[0][0] if scored else CAREER_DATASET[0]
    roadmaps = core_generator({**user_input, 'skills': skills}, top)
    out = {
        'input': user_input,
        'derived_skills': skills,
        'chosen_career': top['career'],
        'roadmaps': [r.__dict__ for r in roadmaps]
    }
    # serialize RoadmapStep dataclasses inner lists
    for r in out['roadmaps']:
        r['steps'] = [_serialize_nested_steps(s) for s in r['steps']]
    # save visualizations to static folder
    static_dir = Path('static') / 'roadmaps'
    image_urls = _plot_roadmaps(out['roadmaps'], static_dir)
    out['images'] = image_urls
    # save files
    with open('generated_roadmaps_output.json','w',encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    outputs_dir = Path('outputs')
    outputs_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    with open(outputs_dir / f'roadmaps_{ts}.json','w',encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    return out
