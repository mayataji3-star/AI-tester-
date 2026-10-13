"""Produce a hash manifest before sending the healthy shop to the trainer."""
import hashlib,json
from pathlib import Path
root=Path(__file__).parent
paths=[root/'config.json',root/'requirements-lock.txt']
for folder in ['tester','docs']:
    paths.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='effort_log.csv')
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
(root/'results/freeze_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Manifest written. Preserve it with your final tester commit before blind evaluation.')
