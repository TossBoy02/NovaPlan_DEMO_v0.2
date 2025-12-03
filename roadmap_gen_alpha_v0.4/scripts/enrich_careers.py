"""
Enrich careers.json with description, education recommendations, and tasks.
- Backups the original file to careers.json.bak
- Adds/updates keys on each career entry:
  - description: brief role description
  - education: list of recommended education levels (strings)
  - tasks: list of 4-7 concrete tasks tailored to the career

This script is conservative and preserves other fields.
"""
import json
from pathlib import Path
import hashlib

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
DATA_FILE = DATA_DIR / 'careers.json'
BACKUP_FILE = DATA_DIR / 'careers.json.bak'

EDU_LEVELS = ['high_school', 'certificate', 'associate', 'bachelor', 'master', 'phd']

# Generic task templates per education level, with placeholders {career} and {skill}
TASK_TEMPLATES = {
    'high_school': [
        'Learn basic {skill} concepts using short online courses and tutorials',
        'Build 1-2 small, demonstrative projects relevant to {career}',
        'Document your learning in a simple portfolio or blog',
        'Apply for internships or assistant roles to gain hands-on experience'
    ],
    'certificate': [
        'Complete a vocational certificate focused on {skill} or tools used in {career}',
        'Create a practical project that demonstrates applied {skill}',
        'Join local/online communities for practical advice and networking',
        'Prepare a clear CV and start applying to entry-level professional roles'
    ],
    'associate': [
        'Finish an associate program with practical labs or apprenticeships',
        'Complete an internship and collect employer references',
        'Deliver a project showing applied {skill} in a real context',
        'Apply to technician or junior specialist roles directly related to {career}'
    ],
    'bachelor': [
        'Graduate a bachelor’s degree or equivalent in a relevant discipline',
        'Lead a capstone or team project solving a realistic problem in {career}',
        'Intern or co-op with industry partners to build professional experience',
        'Publish or present your project work on a portfolio or site'
    ],
    'master': [
        'Undertake advanced coursework or a master’s specialization relevant to {career}',
        'Lead complex applied projects or supervised research using {skill}',
        'Mentor junior peers and document advanced workflows',
        'Target specialist or leadership roles and craft a research/experience summary'
    ],
    'phd': [
        'Conduct original research that advances knowledge related to {career}',
        'Publish findings and present at conferences or professional events',
        'Teach or supervise to develop academic leadership skills',
        'Lead multi-year projects or labs and pursue high-level roles in research or industry'
    ]
}


def deterministic_choice(items, key):
    """Pick an item from items deterministically based on key string."""
    if not items:
        return None
    h = hashlib.sha256(key.encode('utf-8')).digest()
    idx = int.from_bytes(h[:4], 'little') % len(items)
    return items[idx]


def pick_primary_skill(skills, career):
    if not skills:
        # try to get a short meaningful token from career name
        tokens = [t.strip() for t in career.split() if len(t) > 2]
        return tokens[0].lower() if tokens else 'core skills'
    # choose shortest skill name or deterministic first
    for s in skills:
        if len(s.split()) <= 3:
            return s
    return skills[0]


def recommend_education(skills, career):
    s = ' '.join([str(x).lower() for x in (skills or [])])
    # heuristic rules
    if any(k in s for k in ['research', 'analysis', 'algorithm', 'machine', 'scientific', 'statistics']):
        return ['bachelor', 'master']
    if any(k in s for k in ['teacher', 'education', 'instruct', 'training']):
        return ['bachelor', 'certificate']
    if any(k in s for k in ['weld', 'machin', 'operator', 'repair', 'maintenance', 'assembly']):
        return ['certificate', 'associate']
    # default
    return ['certificate', 'bachelor']


def make_description(career, skills, existing):
    if existing and str(existing).strip():
        return existing
    primary = pick_primary_skill(skills, career)
    if skills:
        top = ', '.join(skills[:4])
        return f"{career.capitalize()} typically involves working with {top} and applying {primary} to deliver job outcomes."
    return f"{career.capitalize()} focuses on {primary} and related skills to achieve role objectives."


def make_tasks(career, skills, educations):
    primary = pick_primary_skill(skills, career)
    tasks = []
    # choose templates for recommended education levels and also include a general set
    for lvl in educations:
        templates = TASK_TEMPLATES.get(lvl, [])
        # pick up to 2 templates per level deterministically
        for i in range(min(2, len(templates))):
            t = deterministic_choice(templates, career + lvl + str(i))
            if t:
                tasks.append(t.format(career=career, skill=primary))
    # Add a few general tasks
    general = [
        f"Build a public portfolio showcasing projects related to {career}",
        f"Connect with professionals in the field and request informational interviews",
        f"Set short-term learning goals and review progress every month"
    ]
    # ensure uniqueness and limit to 7-9 tasks
    seen = set()
    out = []
    for t in tasks + general:
        if t not in seen:
            out.append(t)
            seen.add(t)
        if len(out) >= 8:
            break
    return out


def load_data(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_data(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    if not DATA_FILE.exists():
        print('ERROR: careers.json not found at', DATA_FILE)
        return

    # Backup existing file
    if BACKUP_FILE.exists():
        print('Backup already exists at', BACKUP_FILE)
    else:
        DATA_FILE.replace(BACKUP_FILE)
        print('Backed up original to', BACKUP_FILE)

    data = load_data(BACKUP_FILE)

    # Determine structure
    if isinstance(data, dict) and 'careers' in data and isinstance(data['careers'], list):
        careers = data['careers']
        top_dict = True
    elif isinstance(data, list):
        careers = data
        top_dict = False
    else:
        # if dict but not with key 'careers', try to wrap
        if isinstance(data, dict):
            careers = [data]
            top_dict = False
        else:
            print('Unexpected data format in careers.json')
            return

    updated = 0
    examples = []
    for entry in careers:
        career = entry.get('career') or entry.get('title') or 'unknown'
        skills = entry.get('skills') or []
        # normalize skills to list of strings
        skills = [str(s).strip() for s in skills if s]

        # description
        desc = make_description(career, skills, entry.get('description', ''))
        entry['description'] = desc

        # education recommendation
        if not entry.get('education'):
            entry['education'] = recommend_education(skills, career)

        # tasks
        entry['tasks'] = make_tasks(career, skills, entry['education'])

        updated += 1
        if len(examples) < 3:
            examples.append({
                'career': career,
                'education': entry['education'],
                'description': entry['description'],
                'tasks': entry['tasks'][:4]
            })

    # write back
    if top_dict:
        with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
            orig = json.load(f)
        orig['careers'] = careers
        out = orig
    else:
        out = careers

    write_data(DATA_FILE, out)
    print(f'Updated {updated} careers and wrote to {DATA_FILE}')
    print('Examples:')
    print(json.dumps(examples, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
