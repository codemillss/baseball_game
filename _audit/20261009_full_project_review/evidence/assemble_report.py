from pathlib import Path
import json
import re
from collections import Counter

OUT = Path(__file__).resolve().parent.parent
VOLUMES = [
    ('01_목적_문제정의_설계판단_시간순_복원.md', '목적·문제 정의·기대효과·27개 커밋과 단계별 설계 판단'),
    ('04_초기설계_레거시_월드모델_코드해설.md', '초기 기구학·게임·영상 인지·RSSM·Dreamer·PPO·UI 전수 해설'),
    ('05_패치44개_실패_수정_설계사고_해설.md', '44개 패치의 수정 의도·실제 적용·남은 문제'),
    ('02_물리_환경_관측_보상_코드해설.md', '환경·규칙 코드13개·XML8개·진단21개와 모든 함수·요소·주소'),
    ('03_학습_평가_모델_실험증거_코드해설.md', '훈련·평가 전수 해설과 모델·정규화·학습 로그·성공 판정'),
    ('06_문서주장_실제구현_검증수준_대조.md', '문서·영상·데모의 주장과 실제 연결·작은 계약 실행 결과'),
    ('09_이족후속_연구일지_설계판단_시간순_복원.md', '후속 연구일지 모든 Entry·17개 커밋·사용자 피드백과 수정'),
    ('07_이족후속_전신제어_물리환경_코드해설.md', '후속 환경10개·XML10개·PD/IK/보행·직접 지정과 정책의 경계'),
    ('08_이족후속_학습_평가_모델_실험증거.md', '후속 스크립트·모델·CSV 재계산·지표 대상·분모·재현성'),
]

def owner(project, path):
    if project == 'baseball':
        if path.startswith('archive/'):
            return VOLUMES[1][0]
        if path.startswith(('cognitive_ai/envs/', 'shared_assets/', 'cognitive_ai/scripts/')) or path == 'scripts/test_pitcher_action.py':
            return VOLUMES[3][0]
        if path.startswith(('cognitive_ai/training/', 'cognitive_ai/evaluation/')) or path in {'run_demo.sh', 'run_dashboard.sh', 'requirements.txt'}:
            return VOLUMES[4][0]
        if path.startswith('scripts/patches/'):
            return VOLUMES[2][0]
        if path in {'README.md', '.agents/AGENTS.md', '.gitignore'} or path.startswith('docs/'):
            return VOLUMES[0][0] if path == '.agents/AGENTS.md' else VOLUMES[5][0]
    elif project == 'bipedal':
        if path in {'README.md', 'RESEARCH_LOG.md', 'walkthrough.md'}:
            return VOLUMES[6][0]
        if path in {'__init__.py', 'envs/__init__.py', 'test_sim.py'} or path.startswith('scripts/'):
            return VOLUMES[8][0]
        if path.startswith(('envs/', 'models/')):
            return VOLUMES[7][0]
        if path == '.gitignore':
            return VOLUMES[5][0]
    raise ValueError(f'Unassigned source: {project}/{path}')

def main():
    for name, _ in VOLUMES:
        assert (OUT / name).is_file(), name
    sources = json.loads((OUT / 'evidence/source_index.json').read_text())
    coverage = []
    bodies = {name: (OUT / name).read_text() for name, _ in VOLUMES}
    for entry in sources:
        chapter = owner(entry['project'], entry['path'])
        sourcebook = OUT / entry['sourcebook']
        assert sourcebook.is_file(), sourcebook
        basename = Path(entry['path']).name
        named = basename in bodies[chapter] or entry['path'] == '.gitignore'
        coverage.append({'project': entry['project'], 'path': entry['path'], 'lines': entry['lines'], 'sha256': entry['sha256'], 'chapter': chapter, 'named_in_chapter': named, 'full_sourcebook': entry['sourcebook']})
    missing = [r for r in coverage if not r['named_in_chapter']]
    assert not missing, missing
    counts = Counter(r['project'] for r in sources)
    header = '# 야구 강화학습 프로젝트 전체 해설 보고서\n\n'
    header += '작성일: 2026-10-09. 이 파일은 9개 상세 장을 내용 생략 없이 이어 붙인 통합본이다. 코드·설계 문서 251개, 41,271행의 원문은 별도 파일별 sourcebook에도 생략 없이 보존했다. 두 저장소의 first-parent 커밋 44개와 별도 stash 3개를 추적했고, 모델·정규화·TensorBoard·평가 배열·CSV를 대조했다.\n\n'
    header += '읽기의 중심은 목적과 문제, 당시 기록한 생각, 실제 구현, 발생한 문제, 수정 결과와 남은 한계다. 초기 게임→영상/월드모델→상태 벡터 PPO→후속 이족 제어라는 흐름을 따라간다. 원본은 바꾸지 않았으며 이번 재학습·전체 영상 재검수는 수행하지 않았다. 순수 게임 카운트와 심판의 작은 계약 사례만 새로 실행했다.\n\n'
    header += '각 장의 독립 파일도 그대로 제공한다. 큰 통합본에서 이동하기 어려우면 아래 장별 링크를 이용한다.\n\n| 읽기 순서 | 상세 장 | 다루는 내용 |\n|---:|---|---|\n'
    header += '\n'.join(f'| {i} | [{name[:-3]}]({name}) | {label} |' for i, (name, label) in enumerate(VOLUMES, 1))
    header += '\n\n[251개 전체 코드·설계 문서 원문 색인](98_전체코드_원문색인.md) · [파일별 해설 누락 검사](97_파일별해설_전체범위_검사.md) · [원본 보존 검증](evidence/final_integrity.json)\n\n'
    combined = header
    for i, (name, _) in enumerate(VOLUMES, 1):
        combined += f'\n\n---\n\n# 상세 장 {i}: {name[:-3]}\n\n' + bodies[name] + '\n'
    (OUT / '00_전체해설보고서.md').write_text(combined)
    (OUT / 'evidence/manual_review_coverage.json').write_text(json.dumps({'source_count': len(sources), 'source_lines': sum(r['lines'] for r in sources), 'project_counts': dict(counts), 'missing': missing, 'note': 'Every source is assigned to a fully read detailed chapter and a complete line-numbered sourcebook. Semantic assertions still require source review; this mechanical check alone does not prove correctness.', 'files': coverage}, ensure_ascii=False, indent=2))
    table = '# 전체 대상의 파일별 해설 범위 검사\n\n코드·설계 문서 251개 모두 담당 장과 원문 전문에 연결돼 있다. 루트는 목적/기록/Git/44패치/문서 및 두 gitignore를 읽었고, 나머지 영역은 각 담당자의 전수 읽기 목록과 대조했다. 이 표는 누락 검사이며 의미·성능 검증의 대체물이 아니다.\n\n| 프로젝트 | 파일 | 행수 | 상세 해설 | 전체 원문 |\n|---|---|---:|---|---|\n'
    table += '\n'.join(f'| {r["project"]} | `{r["path"]}` | {r["lines"]} | [장 열기]({r["chapter"]}) | [원문]({r["full_sourcebook"]}) |' for r in coverage) + '\n'
    (OUT / '97_파일별해설_전체범위_검사.md').write_text(table)
    index = header.replace('# 야구 강화학습 프로젝트 전체 해설 보고서', '# 야구 프로젝트 상세 보고서 읽기 안내', 1)
    index += '\n[내용을 모두 이어 붙인 통합본 열기](00_전체해설보고서.md)\n'
    (OUT / '00_읽기안내.md').write_text(index)
    print(json.dumps({'volumes': len(VOLUMES), 'sources': len(sources), 'source_lines': sum(r['lines'] for r in sources), 'missing': len(missing), 'combined_lines': len(combined.splitlines()), 'combined_bytes': len(combined.encode())}, ensure_ascii=False))

if __name__ == '__main__':
    main()
