import os
import zipfile
import requests
import shutil
from pathlib import Path
import pandas as pd
from typing import Dict, Any, List

ONET_KAGGLE_ZIP = 'https://www.kaggle.com/datasets/emarkhauser/onet-29-0-database/download?datasetVersionNumber=1'

ESCO_DOWNLOAD_PAGE = 'https://esco.ec.europa.eu/en/use-esco/download'

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)


def download_onet_manual(local_zip_path: Path) -> Path:
    if not local_zip_path.exists():
        raise FileNotFoundError(f"Put the O*NET zip at: {local_zip_path}")
    with zipfile.ZipFile(local_zip_path, 'r') as z:
        z.extractall(DATA_DIR / 'onet')
    return DATA_DIR / 'onet'


def parse_onet_core_skills(onet_dir: Path) -> pd.DataFrame:
    # Example filenames vary by release; try common names
    candidates = ['Skills.csv', 'skills.csv', 'Skills.xlsx']
    for fname in candidates:
        p = onet_dir / fname
        if p.exists():
            if p.suffix.lower() == '.csv':
                return pd.read_csv(p)
            else:
                return pd.read_excel(p)
    raise FileNotFoundError('O*NET skills file not found. Inspect the onet_dir folder.')


def download_esco_csv(output_dir: Path = DATA_DIR / 'esco') -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    # ESCO site offers CSV/ODS/ttl packages; here we assume the user downloaded a CSV package and placed it in output_dir.
    return output_dir


def load_esco_occupations_and_skills(esco_dir: Path = DATA_DIR / 'esco') -> Dict[str, Any]:
    esco_dir = Path(esco_dir)
    occ_path = esco_dir / 'occupations_en.csv'
    rel_path = esco_dir / 'occupationSkillRelations_en.csv'
    sk_path = esco_dir / 'skills_en.csv'
    if not (occ_path.exists() and rel_path.exists() and sk_path.exists()):
        return {}
    occ_df = pd.read_csv(occ_path)
    rel_df = pd.read_csv(rel_path)
    sk_df = pd.read_csv(sk_path)
    # Normalize columns by common names
    occ_id_col = 'conceptUri' if 'conceptUri' in occ_df.columns else occ_df.columns[0]
    occ_label_col = 'preferredLabel' if 'preferredLabel' in occ_df.columns else 'label'
    alt_label_col = 'altLabels' if 'altLabels' in occ_df.columns else None
    sk_id_col = 'conceptUri' if 'conceptUri' in sk_df.columns else sk_df.columns[0]
    sk_label_col = 'preferredLabel' if 'preferredLabel' in sk_df.columns else 'label'
    rel_occ_col = 'occupationUri' if 'occupationUri' in rel_df.columns else 'occupation'
    rel_skill_col = 'skillUri' if 'skillUri' in rel_df.columns else 'skill'

    occ = occ_df[[occ_id_col, occ_label_col] + ([alt_label_col] if alt_label_col else [])].copy()
    sk = sk_df[[sk_id_col, sk_label_col]].copy()
    occ_map = {row[occ_id_col]: {
        'label': str(row[occ_label_col]),
        'alt_labels': [x.strip() for x in str(row[alt_label_col]).split('|')] if alt_label_col and pd.notna(row.get(alt_label_col)) else []
    } for _, row in occ.iterrows()}
    sk_map = {row[sk_id_col]: str(row[sk_label_col]) for _, row in sk.iterrows()}
    out: Dict[str, Any] = {}
    for _, row in rel_df[[rel_occ_col, rel_skill_col]].iterrows():
        o_uri = row[rel_occ_col]; s_uri = row[rel_skill_col]
        if o_uri in occ_map and s_uri in sk_map:
            o_label = occ_map[o_uri]['label']
            entry = out.setdefault(o_label, {'skills': set(), 'alt_labels': occ_map[o_uri]['alt_labels']})
            entry['skills'].add(sk_map[s_uri])
    # finalize
    for k in list(out.keys()):
        out[k]['skills'] = sorted({s.lower() for s in out[k]['skills']})
    return out


def load_onet_skills_and_tasks(data_dir: Path = DATA_DIR) -> Dict[str, Any]:
    skills_txt = data_dir / 'Skills.txt'
    tasks_txt = data_dir / 'Task Statements.txt'
    related_occ_txt = data_dir / 'Related Occupations.txt'
    out: Dict[str, Any] = {}
    if skills_txt.exists():
        try:
            df = pd.read_csv(skills_txt, sep='\t', engine='python')
            # Try common columns
            occ_col = next((c for c in df.columns if 'Occupation' in c or 'Title' in c), df.columns[0])
            skill_col = next((c for c in df.columns if 'Element Name' in c or 'Skill' in c), df.columns[-1])
            for _, row in df[[occ_col, skill_col]].iterrows():
                occ = str(row[occ_col])
                sk = str(row[skill_col]).lower()
                if not occ or not sk: continue
                ent = out.setdefault(occ, {'skills': set(), 'tasks': []})
                ent['skills'].add(sk)
        except Exception:
            pass
    if tasks_txt.exists():
        try:
            df = pd.read_csv(tasks_txt, sep='\t', engine='python')
            occ_col = next((c for c in df.columns if 'Occupation' in c or 'Title' in c), df.columns[0])
            task_col = next((c for c in df.columns if 'Task' in c), df.columns[-1])
            for _, row in df[[occ_col, task_col]].iterrows():
                occ = str(row[occ_col])
                task = str(row[task_col])
                if not occ or not task: continue
                ent = out.setdefault(occ, {'skills': set(), 'tasks': []})
                ent['tasks'].append(task)
        except Exception:
            pass
    # finalize sets to lists
    for k in list(out.keys()):
        out[k]['skills'] = sorted({s for s in out[k]['skills']})
    return out
