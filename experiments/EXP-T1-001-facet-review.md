# EXP-T1-001: Tesseract Facet Candidate HITL Review

> Status: in_progress (T1 done, T2 pending)
> Created: 2026-03-08
> Paused: 2026-03-08 (yuje clinic 전환)
> Objective: 23 facet + 16 theory + 2 module 후보를 HITL 심사하여 Tesseract spec 확장 여부 결정

## Objective

source_log_synthesis.md에서 발굴된 후보들을 심사하여:
- Tesseract에 올릴 것 (domain-agnostic)
- Parallax에 남길 것 (domain-specific)
- 기존 facet과 겹치는 것 (X)
- 추가 evidence 필요한 것 (H)
을 분류한다.

## Key Results (탐색 완료 측정)

- KR1: ~~T1 Priority 8개 구조적 판단~~ **DONE** (8/8)
- KR2: T2 facet 20개 position/distance 분류 -- **문서 작성 완료, 판단 대기** (0/20)
- KR3: 16 theory domain 분류 -- **미착수** (0/16)
- KR4: 2 module 후보 판단 -- **미착수** (0/2)
- KR5: 확정된 신규 facet의 enum/temporal_type 정의 -- **미착수**

## T1 Results (confirmed)

### 신규 facet 확정 (3개)

**F11 ethics_orient** (T1-3)
- enum: citizen / supplier / business
- temporal_type: state
- sextuple: position (observer/viewpoint 불필요)
- domain: agnostic
- note: F07(orient_dominant)과 독립 축. cognitive orient vs value orient.

**switching_cost** (T1-4)
- enum: TBD (gradient이므로 categorical 정의 필요)
- temporal_type: gradient
- sextuple: distance (observer 판단 필요)
- domain: agnostic
- note: 3 layers -- cognitive(Context↔Blitz OODA), pedagogical(AS_conceptual↔AS_procedural), ethical(supplier↔business)
- observed: LIVE 이율희 (cognitive), AI MVP logbook 028 (pedagogical), andragogy Michael Corleone (ethical)

**as_delta** (T1-4)
- source_type: computed
- formula: AS 6요소 변화량의 평균
- threshold: <= 1.0 (safe), > 2.67 (crash observed)
- domain: agnostic
- note: switching_cost의 정량적 측정. Activity System 전환 크기.

### 구조적 판단 (facet 아닌 것)

- T1-2 Croquis vs Atlas: 독립 구조 (module-internal vs observation framework)
- T1-6 T*Q*O: operational protocol (facet 아님)
- T1-7 Periodization: temporal protocol 확장 후보 (facet 아님, T1-6과 통합)

### 보류 (3개)

- T1-1 Loop Currency Economics: 조직/개인 entity 수준 문제
- T1-5 Phase-aware Convergence: phase stratification 추가 조사
- T1-8 11-Loop Menu: F03→intervention mapping 관계

## T2 Status (pending)

문서: `~/Documents/Tesseract/docs/t2_facet_candidate_review.md`

20개 후보 × 6가지 판단 항목 = telescope 판단 대기.
Calculator 추정은 문서에 포함되어 있으나 전부 estimated (C6).

## Resume Instructions

1. `t2_facet_candidate_review.md` 읽기
2. 20개 후보에 대해 P/D/X/H 판단 받기
3. 16개 theory 심사 문서 작성 + 판단
4. 확정된 facet의 enum/temporal_type 정의
5. Tesseract spec 반영
