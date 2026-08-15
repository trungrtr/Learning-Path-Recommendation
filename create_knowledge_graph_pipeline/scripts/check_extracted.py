import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / 'data' / '01_extracted'
files = sorted(DATA_DIR.glob('*.json'))
summary = {
    'files_total': 0,
    'files_with_unwanted_fields': [],
    'files_missing_course_code': [],
    'files_missing_internal_course_code': [],
    'lessons_without_chapter_ref': 0,
    'total_lessons': 0,
}
UNWANTED = {'content_hash', 'allocated_hours', 'related_chapter_refs_temp_id'}
for fp in files:
    summary['files_total'] += 1
    data = json.loads(fp.read_text(encoding='utf-8'))
    # check unwanted
    has_unwanted_flag = {'v': False}
    def walk(obj, path=''):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in UNWANTED:
                    has_unwanted_flag['v'] = True
                walk(v, path + '/' + k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, path + f'[{i}]')
    walk(data)
    if has_unwanted_flag['v']:
        summary['files_with_unwanted_fields'].append(str(fp.name))
    course = data.get('course', {})
    if not course.get('course_code'):
        summary['files_missing_course_code'].append(str(fp.name))
    if not course.get('internal_course_code'):
        summary['files_missing_internal_course_code'].append(str(fp.name))
    lessons = data.get('lessons', [])
    summary['total_lessons'] += len(lessons)
    for l in lessons:
        if not l.get('chapter_ref_temp_id'):
            summary['lessons_without_chapter_ref'] += 1

print(json.dumps(summary, indent=2, ensure_ascii=False))
