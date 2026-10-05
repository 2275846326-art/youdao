"""Read-only checks for a primary shot timeline; no media decoding or network."""
import argparse
import json
import math
from pathlib import Path


def number(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def text(value):
    return isinstance(value, str) and bool(value.strip())


def check(data, base, files=True, tolerance=0.04):
    errors, warnings = [], []
    checked = 0

    def asset(path, label, required):
        nonlocal checked
        if not text(path):
            errors.append(f'{label}: path must be a nonempty string')
            return
        if '://' in path:
            errors.append(f'{label}: local file required; remote results need separate verification')
            return
        if not files:
            return
        p = Path(path)
        if not p.is_absolute():
            p = base / p
        checked += 1
        try:
            valid = p.is_file() and p.stat().st_size > 0
        except OSError:
            valid = False
        if not valid:
            (errors if required else warnings).append(f'{label}: missing, empty or unreadable file: {path}')

    if not isinstance(data, dict):
        return {'errors': ['manifest must be an object'], 'warnings': [], 'file_checks': files, 'files_checked': 0}
    if type(data.get('schema_version')) is not int or data.get('schema_version') != 1:
        errors.append('schema_version must be integer 1')
    shots = data.get('shots')
    if not isinstance(shots, list) or not shots:
        errors.append('shots must be a nonempty array')
        shots = []
    duration = data.get('duration_sec')
    if 'duration_sec' in data and (not number(duration) or duration <= 0):
        errors.append('duration_sec must be finite and positive')
    seen, previous = set(), 0.0
    for index, shot in enumerate(shots):
        label = f'shots[{index}]'
        if not isinstance(shot, dict):
            errors.append(f'{label}: must be an object')
            continue
        sid = shot.get('id')
        if not text(sid):
            errors.append(f'{label}: id required')
        elif sid in seen:
            errors.append(f'{label}: duplicate id {sid}')
        else:
            seen.add(sid)
        if not text(shot.get('purpose')):
            errors.append(f'{label}: purpose required')
        start, end = shot.get('start_sec'), shot.get('end_sec')
        if not number(start) or not number(end) or start < 0 or end <= start:
            errors.append(f'{label}: invalid start/end time')
        else:
            if abs(start - previous) > tolerance:
                errors.append(f'{label}: timeline gap, overlap or ordering error (expected {previous}, got {start})')
            previous = end
        status = shot.get('status')
        if status not in ('planned', 'ready', 'rendered', 'accepted'):
            errors.append(f'{label}: invalid status')
        assets = shot.get('assets')
        if not isinstance(assets, list):
            errors.append(f'{label}: assets must be an array')
            assets = []
        for ai, item in enumerate(assets):
            alabel = f'{label}.assets[{ai}]'
            if not isinstance(item, dict):
                errors.append(f'{alabel}: must be an object')
                continue
            if not text(item.get('role')):
                errors.append(f'{alabel}: role required')
            asset(item.get('path'), alabel, status != 'planned')
        if status in ('rendered', 'accepted'):
            asset(shot.get('output_path'), f'{label}.output_path', True)
        if status == 'accepted':
            review = shot.get('review')
            if not isinstance(review, list) or not review:
                errors.append(f'{label}: accepted requires review evidence')
                review = []
            passed = False
            for ri, item in enumerate(review):
                rlabel = f'{label}.review[{ri}]'
                if not isinstance(item, dict):
                    errors.append(f'{rlabel}: must be an object')
                    continue
                if not text(item.get('aspect')) or not text(item.get('evidence')):
                    errors.append(f'{rlabel}: aspect and evidence required')
                result = item.get('result')
                if result not in ('passed', 'not_applicable'):
                    errors.append(f'{rlabel}: accepted review has unresolved or invalid result')
                passed = passed or result == 'passed'
            if not passed:
                errors.append(f'{label}: accepted requires at least one passed review')
    if shots and number(duration) and abs(previous - duration) > tolerance:
        errors.append(f'timeline ends at {previous}, expected duration_sec {duration}')
    return {'errors': errors, 'warnings': warnings, 'file_checks': files,
            'files_checked': checked, 'shots': len(shots), 'media_decoded': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--structure-only', action='store_true')
    parser.add_argument('--tolerance', type=float, default=0.04)
    args = parser.parse_args()
    if not math.isfinite(args.tolerance) or args.tolerance < 0:
        parser.error('--tolerance must be finite and nonnegative')
    try:
        data = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        print(json.dumps({'errors': [str(exc)], 'file_checks': False}, ensure_ascii=False))
        return 2
    result = check(data, args.manifest.resolve().parent, not args.structure_only, args.tolerance)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
