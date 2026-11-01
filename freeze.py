"""Freeze tester inputs before evaluation; verify them without reading hidden bugs."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = 'db75ec7067df4c3d7bf0ad58abd5f3eed59851bf'
MANIFEST = ROOT/'results/freeze_manifest.json'


def digest(path):
    # Consistent across Git's LF/CRLF checkout settings on Linux and Windows.
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def frozen_paths():
    names = ['config.json', 'requirements-lock.txt', 'requirements.txt', 'serve.py', 'freeze.py',
             'docs/requirements.md', 'docs/tasks.json', 'docs/ai_instructions.txt',
             'docs/scoring.md', 'docs/evaluation_plan.md']
    for folder in ('tester', 'tests'):
        names.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py', '.cjs'))
    return sorted(set(names))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--allow-shop-changes', action='store_true',
                        help='Only after the trainer has provided the evaluation shop.')
    parser.add_argument('--replace', action='store_true', help='Replace an existing pre-evaluation manifest.')
    args = parser.parse_args()
    if args.verify:
        if not MANIFEST.is_file():
            parser.error('No freeze manifest; create it before evaluation.')
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        if manifest.get('schema_version') != 2:
            parser.error('Old manifest format. Keep it as historical evidence; create the new freeze before evaluation.')
        expected = manifest['frozen_files']
        current_names = set(frozen_paths())
        changed = sorted(current_names.symmetric_difference(expected))
        changed.extend(name for name, value in expected.items()
                       if not (ROOT/name).is_file() or digest(ROOT/name) != value)
        changed = sorted(set(changed))
        shop_changed = digest(ROOT/'shop/index.html') != manifest['healthy_shop_sha256']
        for name in changed:
            print('CHANGED OR MISSING:', name)
        print('Shop differs from healthy baseline:', shop_changed)
        if changed or (shop_changed and not args.allow_shop_changes):
            print('FAIL: do not run the scored experiment until unexpected changes are resolved.')
            return 1
        print('PASS: frozen tester, instructions, configuration and scoring rules match.')
        return 0
    if MANIFEST.exists() and not args.replace:
        parser.error('Manifest exists. Preserve it; use --replace only before evaluation, never after viewing blind results.')
    manifest = dict(schema_version=2, source_baseline_commit=BASELINE,
                    hash_normalization='SHA-256 with CRLF normalized to LF',
                    frozen_files={name: digest(ROOT/name) for name in frozen_paths()},
                    healthy_shop_sha256=digest(ROOT/'shop/index.html'))
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print('Freeze manifest saved. Commit it and retain the commit ID before trainer bug planting.')
    print('Do not regenerate it after seeing blind evaluation results.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
