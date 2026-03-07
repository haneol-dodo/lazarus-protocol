# 2026-03-08: Lazarus 통일장 설계 -- numeric 제거에서 메타 프로토콜까지

## 경로 (어떻게 여기에 도달했는가)

1. "lazarus를 가져다 쓰는 프로젝트들에 원칙을 추가하고 싶다" -- numeric 값 금지, 원본 표현 유지
2. 분석: "numeric 금지"가 아니라 **"스칼라 축소 금지"**가 정확한 표현
   - 빈도수, 음절수 등 computed 숫자는 허용
   - 금지 대상: 고차원 데이터를 스칼라 점수로 환원하는 것
3. Section 8 Numeric Convergence를 왜 넣었는지 추적 -- `numeric.py` 라인 6:
   "Extracted from Parallax convergence_workflow.py (EXP-005)"
   - 도메인 코드가 인프라로 잘못 올라온 케이스
4. Numeric Convergence의 고객이 없다는 결론:
   - computed 숫자 -- convergence 불필요 (결정론적)
   - observed 숫자 -- LLM convergence 영역 아님
   - estimated 숫자 -- 프로토콜이 금지하는 것
5. **제거 실행**: CLAUDE.md Section 8, numeric.py, test_numeric.py, display.py, types.py, domain.py, README.md
6. context window 관리 논의 -- 70%/80% 안전망
7. 기각된 가설의 context window 점유 문제 제기
   - 사용자 원문: "아직 결정이 안났는데 기각된 가설들이 누적되면서 context window를 차지하는 경우"
8. **아젠다 전환 감지** -- % 기반은 안전망, 주 메커니즘은 논리적 decision commit
   - git commit 패턴: 디스크가 차서가 아니라 논리적 단위가 완결될 때 commit
9. 외부화 포맷 논의 -- prose면 실패 (O(n) 해석), 좌표면 성공 (O(1) 조회)
   - 사용자 원문: "저렇게 해도 전부다 비정형 텍스트들인거 아냐?"
10. **RPD 연결** -- NDM의 Recognition-Primed Decision
    - 사용자 원문: "lazarus를 만든 이유였어. NDM의 RPD가 이 원리라고 생각했어. working memory를 최적화하는 pattern matching이라고 말이야"
    - exploration_map = 전문가의 경험 베이스
    - 좌표 조회 = pattern matching (O(1))
    - 로그가 쌓일수록 빨라지는 시스템 = RPD
11. **하류 프로젝트 전수 탐색**:
    - Parallax (깊은 통합)
    - Spotlight Works (중간 통합, 255d, Gabriel 실패 이력)
    - 260205 Bootcamp (submodule)
    - AI MVP 5th (DomainRegistry, 20 facet + 17 dim)
    - DT_Cartography (255d 독립구현, Phase 5 완료)
    - DT_Genome (761 atom, 20 NSM prime, 독립구현)
    - 2. English (Target_Spotlighting 원조, Workspace_Complexity)
12. **Gabriel 실패 = numeric convergence = 스칼라 축소** -- 같은 교훈의 반복 확인
    - Gabriel: LLM에게 0-100 점수 매기게 함 -> C7 위반 -> drift
    - Numeric convergence: running mean delta -> 거짓 정밀도
    - 오늘 제거한 것과 2026-02에 Gabriel 폐기한 것이 동일한 패턴
13. **통일장 비전**: 모든 프로젝트의 시행착오를 좌표로 누적
    - 사용자 원문: "각자의 시행착오를 다 한군데 모으는데 그것도 complexity안에서 다 기계코드화 할 수 있잖아"

## 결론 (채택된 결정)

### D1: 스칼라 축소 금지
- LLM에게 0-100 점수를 매기게 하는 모든 패턴을 금지
- categorical (enum) 분류만 허용
- computed 숫자 (빈도, 음절수 등)는 예외 -- 이건 원래 스칼라

### D2: Numeric Convergence 제거
- CLAUDE.md Section 8에서 삭제 완료
- lazarus/convergence/numeric.py 삭제 완료
- 모든 참조 정리 완료 (domain.py, types.py, display.py, README.md)
- 테스트 110 passed

### D3: Decision Commit Protocol 방향
- 가설 채택/기각 시 좌표로 기록 (prose 아님)
- 채택 -> logbook, experiment, memory
- 기각 -> exploration_map (좌표 기반)
- 탐색 지도: (facet, value, status, evidence_type, t)
- % 안전망 (70% warning, 80% stop)은 보조 메커니즘

### D4: Lazarus = 통일장
- 현재 6개 프로젝트가 같은 사상을 독립 구현
- Lazarus를 통일장으로 만들어 모든 프로젝트가 같은 라이브러리를 import
- 시행착오를 좌표로 누적 -> 새 프로젝트가 RPD로 빨라짐

## 기각된 경로

### R1: dead_ends.md (prose 기반 기각 로그)
- 제안됨 -> 기각
- 이유: 비정형 텍스트는 O(n) 해석 필요, 중복 탐색 방지 불가
- 대체: exploration_map.json (좌표 기반)

### R2: lazarus.workspace 별도 모듈
- 제안됨 -> 보류
- 이유: exploration_map이 제대로 작동하면 workspace complexity가 부산물로 해결됨
- 70%/80% 안전망만 추가하면 될 수 있음 -- 검증 필요

### R3: 가설 전환의 프로그래밍적 자동 감지
- 논의됨 -> 한계 확인
- LLM이 자기 context를 정확히 측정 불가
- 행동 규칙(discipline)으로 작동 -- C 규칙과 동일한 메커니즘
- 자동화 가능한 부분: probe 결과, convergence 결과 (이미 구조화)
- 자동화 불가: 대화 중 즉흥 가설

## 다음 작업: 통일 방법 연구

### 조사 대상
1. 20 facet 스키마 비교 -- Spotlight Works vs AI MVP 5th vs DT_Genome
   - 같은 건가? canonical 버전은?
   - NSM prime과의 1:1 매핑 검증
2. 255d 구조 비교 -- Spotlight Works vs DT_Cartography
   - 축 이름, 레벨 정의, plateau 구조가 동일한지
3. DT_Cartography의 KK 0-100 점수 -- categorical 전환 방안
4. exploration_map.json 스키마 설계
5. pip install -e 통일 (Bootcamp submodule 전환 포함)

### 열린 질문
- exploration_map이 프로젝트별인가, 프로젝트 횡단인가?
- 20 facet이 Lazarus 코어에 들어가야 하나, 도메인 레벨에 남아야 하나?
- DT_Genome의 761 atom이 exploration_map의 seed가 될 수 있나?
- Workspace Complexity를 별도 모듈로 둘지, exploration_map의 부산물로 볼지

## Tesseract 발견 (추가)

- GitHub: haneol-dodo/tesseract (v0.1.0, spec-only)
- Bootcamp submodule로 등록되어 있었으나 로컬에서 init 안 됨 -- 복구 완료
- **핵심**: RPD + Satisficing이 Tesseract의 중심 원리
  - "Expert decision-making is recognition-primed + satisficing, not analytical optimization"
- **Cosmology**: Tesseract(discovery) -> Lazarus(collection) -> Parallax(triangulation)
- 10 observation facets, 28 theories with provenance, 6-Module training loop
- 제약조건 T1-T4 (domain-agnostic, facet immutable, theory provenance, module abstract)
- Lazarus C1-C11 상속
- 통일장에 포함 대상 -- 10 facet과 기존 20 facet의 관계 조사 필요

## 파일 정리 계획 (추가)

### 현황
- 총 68G (Documents 56G + Projects 12G)
- Boilerplate 5개 모듈이 3-4곳에 중복 (15+ 복사본)
- 2. English는 02-07 일괄 스냅샷 -- 이후 수정 없음
- Bootcamp 2곳 존재 (AI IDE 03-07 활발 / DT IDEO 02-27 방치)
- facet_schema가 JSON/MD 혼재, 3+ 곳에 산재
- iCloud 동기화가 .git, .venv, .omc를 불필요하게 동기화 중

### 안전하게 정리 가능
- 2. English 내 Boilerplate 사본들 (02-07 스냅샷, 이후 미수정)
- AI IDE/00. Boilerplate (MVP에 더 최신 버전 있음)
- Bootcamp (DT IDEO) -- AI IDE 쪽이 활발
- DT_Cartography, DT_Genome -- 완성 후 방치, 이동만

### 주의 필요
- Spotlight Works (03-08 활발)
- 3_AI_MVP_5th (양쪽 활발, submodule 관계 정리)
- MVP/AI_SaaS_Agent_Config (기술스택 분기)

### 목표 구조
```
~/Projects/              로컬 전용 (코드 + git)
  Lazarus, Parallax, Spotlight_Works, DT_Cartography,
  DT_Genome, 3_AI_MVP_5th, Bootcamp, Tesseract

~/Documents/             iCloud (문서만)
  1. Work/ (강의자료, 계약서, PDF)
  2. Resources/ (디자인, 폰트)
```

### 실행 순서
1. git remote 전수 확인 (모든 프로젝트 push 상태 점검)
2. 안전한 사본 삭제 (2. English 스냅샷, AI IDE Boilerplate)
3. 코드 프로젝트 ~/Projects/로 이동
4. iCloud에서 ~/Projects/ 제외 설정
5. 깨진 참조 (하드코딩 절대경로) 수정

## 관련 파일
- CLAUDE.md (수정됨 -- Section 8 numeric 제거)
- lazarus/registry/domain.py (수정됨 -- numeric 참조 제거)
- lazarus/convergence/display.py (수정됨 -- numeric display 제거)
- lazarus/convergence/types.py (수정됨 -- NumericWordResult 제거)
- README.md (수정됨 -- numeric 참조 제거)
