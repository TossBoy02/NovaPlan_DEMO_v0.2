import random
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class RoadmapStep:
    title: str
    objective: str
    duration_months: int
    prerequisites: List[str]
    milestones: List[str]
    resources: List[str]
    tasks: List[str] = field(default_factory=list)
    children: List['RoadmapStep'] = field(default_factory=list)

@dataclass
class Roadmap:
    path_title: str
    focus: str
    confidence_score: float
    steps: List[RoadmapStep]


def generate_steps_for_career(career: Dict[str,Any], profile_skills: List[str], focus: str, beginner: bool = True):
    known = [s for s in [sk.lower() for sk in career.get('skills', [])] if s in profile_skills]
    missing = [s for s in [sk.lower() for sk in career.get('skills', [])] if s not in profile_skills]

    def make_step(title, objective, months, prereq, milestones, resources, tasks=None, children=None):
        return RoadmapStep(
            title=title,
            objective=objective,
            duration_months=months,
            prerequisites=prereq,
            milestones=milestones,
            resources=resources,
            tasks=tasks or [],
            children=children or []
        )

    # Dynamic Step Generation Logic
    career_tasks = career.get('tasks', [])
    career_name = career.get('career', 'Career')
    
    # helper to get random subset or fallback
    def get_tasks(count, fallback_prefix):
        if career_tasks:
            # try to find relevant tasks first if possible, else random
            return random.sample(career_tasks, min(len(career_tasks), count))
        return [f"{fallback_prefix} {i+1}" for i in range(count)]

    # helper to generate milestones
    def get_milestones(context, count=3):
        return [f"Complete {context} module {i+1}", f"Pass {context} assessment", f"Build {context} demo"]

    # 1. Foundations
    foundations_children = []
    if beginner:
        foundations_children.append(make_step(
            'Industry Fundamentals',
            f'Understand the core concepts of {career_name}',
            1,
            [],
            ['Complete introductory course', 'Learn industry terminology', 'Understand role responsibilities'],
            ['Online Courses', 'Industry Glossaries', 'Career Guides'],
            get_tasks(5, 'Study fundamental concept')
        ))
        foundations_children.append(make_step(
            'Tools & Environment',
            'Set up your professional workspace',
            1,
            [],
            ['Install necessary software', 'Configure development/work environment', 'Join professional communities'],
            ['Official Documentation', 'Community Forums'],
            ['Research standard tools for ' + career_name, 'Install primary software tools', 'Create account on professional networks']
        ))

    foundations = make_step(
        'Foundations', 
        'Build essential groundwork for your career', 
        1 if beginner else 0, 
        [], 
        ['Complete foundation modules', 'Set up workspace'],
        ['Standard Industry Tools'],
        ['Set up your learning workspace', 'Create a study schedule', 'Join relevant online communities'],
        children=foundations_children
    )

    # 2. Core Skills
    core_children = []
    skills_to_learn = (missing[:4] if missing else career.get('skills', [])[:4])
    
    for i, sk in enumerate(skills_to_learn):
        # Try to find tasks related to this skill
        related_tasks = [t for t in career_tasks if sk.lower() in t.lower()]
        step_tasks = related_tasks[:3] if related_tasks else [f'Practice {sk} fundamentals', f'Apply {sk} in small scenarios']
        
        core_children.append(make_step(
            f'{sk.title()} Proficiency', 
            f'Develop proficiency in {sk}', 
            2, 
            known[:2] if i == 0 else [], 
            [f'Complete {sk} course', f'Demonstrate {sk} usage', f'Pass {sk} quiz'],
            [f'{sk.title()} Resources'],
            step_tasks
        ))
    
    core = make_step(
        'Core Skills Development', 
        f'Master essential skills for {career_name}', 
        max(2, len(core_children)), 
        known, 
        ['Complete all core skill modules', 'Pass skill assessments'],
        ['Online Learning Platforms'],
        ['Create a skills tracking spreadsheet', 'Set up practice projects', 'Find a mentor'],
        children=core_children
    )

    # 3. Practical Application (Projects/Experience)
    project_children = []
    
    # Project 1: Basic Application
    proj1_tasks = get_tasks(4, 'Implement basic feature')
    project_children.append(make_step(
        'Applied Practice Project', 
        'Apply core skills in a realistic scenario', 
        2, 
        known + missing[:2], 
        ['Design project scope', 'Implement core features', 'Document results'],
        ['Project Management Tools', 'Documentation Tools'],
        ['Select a real-world problem to solve', 'Plan the solution'] + proj1_tasks
    ))

    # Project 2: Advanced Application
    proj2_tasks = get_tasks(5, 'Implement advanced feature')
    project_children.append(make_step(
        'Advanced Capstone', 
        'Demonstrate comprehensive mastery', 
        2, 
        known + missing[:3], 
        ['Complete complex project', 'Peer review', 'Final presentation'],
        ['Advanced Tools'],
        ['Define advanced project requirements'] + proj2_tasks
    ))

    project = make_step(
        'Practical Application', 
        'Gain hands-on experience through projects or simulations', 
        len(project_children), 
        known, 
        ['Complete 2 major projects', 'Build portfolio'],
        ['Portfolio Platform'],
        ['Research industry standard projects', 'Document process and outcomes'],
        children=project_children
    )

    # 4. Specialization
    spec_children = [
        make_step(
            'Specialization Track', 
            'Deep dive into a specific area', 
            2, 
            known + missing[:2], 
            ['Complete specialization course', 'Advanced certification', 'Master advanced concepts'],
            ['Specialized Training'],
            get_tasks(4, 'Study advanced topic')
        )
    ]
    spec = make_step(
        'Specialization', 
        'Develop expertise in specific areas', 
        2, 
        [], 
        ['Choose specialization', 'Achieve advanced competency'],
        ['Industry Certifications'],
        ['Research trending specializations in ' + career_name, 'Select a niche'],
        children=spec_children
    )

    # 5. Career Launch
    job_children = [
        make_step(
            'Professional Branding', 
            'Create compelling professional presence', 
            1, 
            [], 
            ['Update resume', 'Optimize professional profile', 'Build portfolio'],
            ['LinkedIn', 'Resume Builder'],
            ['Tailor resume for ' + career_name, 'Highlight key skills: ' + ', '.join(skills_to_learn[:3])]
        ),
        make_step(
            'Job Search Strategy', 
            'Execute systematic job search', 
            1, 
            [], 
            ['Apply to positions', 'Network', 'Interview prep'],
            ['Job Boards', 'Networking Events'],
            ['Identify top companies for ' + career_name, 'Prepare for interviews']
        )
    ]
    job = make_step(
        'Career Launch', 
        'Land your first role in the field', 
        len(job_children), 
        [], 
        ['Complete branding', 'Secure job offer'],
        ['Job Search Platforms'],
        ['Develop job search strategy', 'Practice interview questions'],
        children=job_children
    )

    # Tailor for focus
    if focus == 'Depth':
        core.duration_months += 1
    elif focus == 'Fast-Entry':
        project.duration_months += 1
    elif focus == 'Transition':
        job.duration_months += 1

    return [foundations, core, project, spec, job]


def generate_distinct_roadmaps(profile: Dict[str,Any], top_career: Dict[str,Any]):
    focuses = ['Depth','Fast-Entry','Transition']
    roadmaps = []
    for f in focuses:
        steps = generate_steps_for_career(top_career, profile.get('skills',[]), f, beginner=True)
        rm = Roadmap(path_title=top_career.get('career') or top_career.get('label', 'Career'), focus=f, confidence_score=0.8, steps=steps)
        roadmaps.append(rm)
    return roadmaps
