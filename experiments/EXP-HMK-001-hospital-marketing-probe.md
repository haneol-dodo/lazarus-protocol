# EXP-HMK-001: 병원마케팅 강사 자료 프로브 -- Tesseract-C/L/K 도출

> **Status**: in_progress (P1-P4 done, P5-P6 pending)
> **Created**: 2026-03-08
> **Protocol**: Lazarus v3.1.0
> **Upstream**: Tesseract (discovery layer)

---

## Objective

병원마케팅 강사(라이언/레비)의 전략 자료에서 고맥락 데이터를 비압축 추출하여,
도메인 비종속적인 3개의 Tesseract 좌표계를 도출한다.

### 3 Tesseract 구조

```
Tesseract-C (Client Decision Model)
  관찰 대상: 의사결정자(의사)의 멘탈모델
  facet 성격: position (관찰자 무관 -- 누가 봐도 같은 축)
  sextuple: (client, facet, value, t)
  일반화: "의사" → "전문직 의사결정자"

Tesseract-L (Lecturer Strategy)
  관찰 대상: 강사(라이언/레비)의 전략 좌표계
  facet 성격: distance (관찰자 종속 -- 강사의 자산/역량/맥락에 묶임)
  sextuple: (client, facet, value, t, 강사, 강사맥락)
  강사 맥락: 14년차, MSO 운영, 200-300병원, AI블로그툴, 팀 보유
  일반화: "병원마케팅 전문가" → "도메인 전문 자문가"

Tesseract-K (Kim Strategy)
  관찰 대상: 김한얼의 전략 좌표계
  facet 성격: distance (관찰자 종속 -- 나의 자산/역량/맥락에 묶임)
  sextuple: (client, facet, value, t, 김한얼, 김한얼맥락)
  김한얼 맥락: 1인, AI IDE 기반, Velvet Design Studio, 첫클라이언트,
               Lazarus/Tesseract 좌표계 보유, 컨설팅 경험 0
  일반화: "AI 네이티브 솔로 컨설턴트" → "도구 기반 자문가"
```

### 왜 L과 K가 분리되어야 하는가

```
같은 client(유제의원), 같은 facet(접근전략)이라도:

  강사 관점: (유제의원, approach, MSO체제, t, 강사, 14년차+팀+병원네트워크)
  김한얼 관점: (유제의원, approach, SI컨설팅, t, 김한얼, 1인+AI_IDE+Velvet)

  observer가 다르면 value가 다르다.
  강사의 전략을 그대로 복사하면 실패한다 -- 자산이 다르니까.

  L의 전략을 K의 맥락으로 번역하는 것 = bridge mapping.
  bridge 불가능한 영역 = gap (김한얼이 채워야 할 역량).
  bridge 불필요한 영역 = K만의 자산 (AI IDE, Lazarus 좌표계).
```

### C/L/K 관계

```
Tesseract-C (position)        -- 클라이언트가 "어떤 상태인지" 관찰
      ↓ 읽기
Tesseract-L (distance, 강사)  -- 강사가 "어떻게 접근하는지" 관찰
      ↓ bridge mapping
Tesseract-K (distance, 김한얼) -- 내가 "어떻게 번역하는지" 설계

C는 L과 K 모두가 읽는 공통 입력.
L은 원본 전략 (추출 대상).
K는 번역된 전략 (설계 대상).
L→K 변환 시 gap/surplus 분석 필수.
```

---

## Key Results (탐색 완료 측정)

| KR | 측정 | 목표 |
|----|------|------|
| KR1 | 6개 소스 프로브 완료 보고 | 6/6 reported |
| KR2 | raw record 추출 (발화/시나리오/행위 단위) | N records extracted |
| KR3 | Tesseract-C facet 후보 도출 | M candidates identified |
| KR4 | Tesseract-L facet 후보 도출 | M candidates identified |
| KR5 | Tesseract-K gap/surplus 분석 | L→K bridge map drafted |
| KR6 | 기존 Tesseract 10F 직교성 확인 | orthogonality assessed |

KR은 탐색 완료를 측정한다. "좋은 facet이 나왔다"는 KR이 아니다.

---

## Phase 1: PARTITION (소스 분할)

### 소스 인벤토리

```
BASE = ~/Documents/1. Work/.../Spotlight_Works/docs/8. 병원마케팅/1. 기획/
```

| ID | 파일 | 크기 | 유형 | Observer | 관찰 대상 |
|----|------|------|------|----------|----------|
| S1 | 260113 병원마케팅 특강.md | 305KB | 녹취록 (라이브) | 라이언(A) + PD(B) | 영업 프로세스 + 시장 구조 |
| S2 | 업태분석.md | 622줄 | 분석 보고서 | 김한얼 (Velvet) | 경쟁 환경 + 가격 구조 |
| S3 | 레이저제모 리서치.md | 1552줄 | 케이스 분석 | 김한얼 + ChatGPT | 전략 전환 패턴 |
| S4 | 원장님 첫 미팅 시나리오.pdf | 2MB | 시나리오 30선 | 강사(미상) | **의사 반론 패턴** (RPD cue library) |
| S5 | AI 병원마케팅_무자본 시작.pdf | 3MB | 전자책 (입문) | 강사(미상) | AI 블로그 + 수익 구조 |
| S6 | 병원마케팅 영업 가이드.pdf | 4MB | 전자책 (영업) | 강사(미상) | **7단계 영업 시스템** + 심리 구조 |
| S7 | PPT Slide/ (51장) | 이미지 | 슬라이드 캡처 | 라이언/레비 | S1 시각 보충 |

### Observer 분류

| Observer | 역할 | 출처 |
|----------|------|------|
| 라이언 (A) | 병원마케팅 실무자, MSO 운영 | S1 |
| 레비 대표 | 14년차, 연매출 100억+, 라이언의 멘토 | S1 (후반부) |
| 김한얼 | Velvet Design Studio, 분석자 | S2, S3 |
| 강사(미상) | 전자책 저자 (라이언/레비 중 하나 추정) | S4, S5, S6 |
| PD (B) | 인터뷰어 | S1 |

### C/L/K 매핑 예상

| 소스 | Tesseract-C (Client) | Tesseract-L (Lecturer) | Tesseract-K (Kim) |
|------|----------------------|------------------------|-------------------|
| S1 특강 | 원장 심리 (까다로운 이유) | 분석→제안→MSO 접근법 | 김한얼이 못 쓰는 자산 식별 |
| S2 업태분석 | -- | -- | **김한얼 산출물** -- K의 시장 좌표 |
| S3 레이저제모 | 의사결정자의 전략 전환 패턴 | 엔트리→업셀 퍼널 구조 | 유제의원에 적용 가능성 |
| S4 시나리오 | **핵심**: 30가지 반론 = 멘탈모델 | 30가지 대응 = L의 레퍼토리 | L→K 번역 (내 자산으로 대응 가능?) |
| S5 AI 블로그 | 병원의 4대 고민 | L의 도구 (AI블로그툴) | K의 도구 (AI IDE, Lazarus) |
| S6 영업 가이드 | **핵심**: 감정vs논리, 4핵심요소 | **핵심**: 7단계 프로세스 | K의 파이프라인과 대조 |
| S7 슬라이드 | -- | S1 시각 보충 | -- |

### L→K Bridge 예상 gap/surplus

```
강사(L)가 가진 것 → 김한얼(K)에게 없는 것 (GAP):
  - 14년 도메인 경험 → 0년
  - 200-300병원 네트워크 → 지인 1명 (오해솔)
  - MSO 운영 역량 → 없음
  - AI 블로그 전용 툴 → 없음
  - 팀 (개발자, 마케터) → 1인

김한얼(K)이 가진 것 → 강사(L)에게 없는 것 (SURPLUS):
  - Lazarus/Tesseract 좌표계 → 체계적 분석 프레임워크
  - AI IDE (Claude Code) → 범용 자동화 (블로그 전용보다 넓음)
  - Spotlight Works 엔진 → 255d 벡터, 24 서비스 모듈, 슬라이드 시스템
  - 디자인 역량 → 웹/브랜딩 직접 제작
  - 30곳 경쟁분석 데이터 → 이미 보유 (강사 접근법을 이미 실행한 셈)

번역 전략:
  GAP 영역 → 회피 또는 대체 전략 설계
  SURPLUS 영역 → 차별화 무기로 전환
  공통 영역 → L의 패턴을 K의 도구로 실행
```

### 프로브 우선순위

```
Priority 1 (핵심 -- C/L 양면 + K 번역):
  S4 시나리오 30선  → C: 의사 반론 / L: 마케터 대응 / K: 내 대응 가능?
  S6 영업 가이드     → C: 의사결정 심리 / L: 영업 시스템 / K: Velvet 파이프라인 대조

Priority 2 (L의 암묵지 추출):
  S1 특강           → L의 실전 맥락, 사례, 원칙
  S3 레이저제모      → 전략 전환 케이스

Priority 3 (K의 기존 자산 대조):
  S2 업태분석        → K가 이미 만든 시장 좌표
  S5 AI 블로그      → L의 도구 vs K의 도구 비교

Priority 4 (보충):
  S7 슬라이드        → S1 프로브 시 필요하면 참조
```

---

## Phase 2: SCAN (프로브 파견)

### 추출 규칙

각 소스에서 다음 단위로 raw record를 추출한다:

```
record:
  id: "{source_id}-{seq}"
  type: utterance | scenario | action | claim | framework | case
  raw_text: "원문 그대로" (C1: 압축 금지)
  speaker: observer 이름
  target: client | advisor | market | system
  domain_terms: ["원장", "마케팅", ...]  # 나중에 일반화할 도메인 용어
  general_terms: ["의사결정자", "자문", ...]  # 도메인 비종속 대응어
  tesseract_hint: C | L | K | CL | CK | LK | CLK | none
  source_type: observed  # 강사 발화 = observed (C4)
```

### 프로브 실행 계획

| 프로브 | 소스 | 방법 | 세션 수 (예상) |
|--------|------|------|-------------|
| P1 | S4 시나리오 30선 | PDF 전체 읽기 → 30쌍 추출 | 2-3 |
| P2 | S6 영업 가이드 | PDF 전체 읽기 → 챕터별 추출 | 3-4 |
| P3 | S1 특강 | 부분 읽기 (100줄 단위) → 구간별 추출 | 5-8 |
| P4 | S3 레이저제모 | 전체 읽기 → 케이스 추출 | 1-2 |
| P5 | S2 업태분석 | 전체 읽기 → 구조 추출 | 1-2 |
| P6 | S5 AI 블로그 | PDF 읽기 → 핵심 프레임워크 추출 | 1-2 |

총 예상: 13-21 세션 (소스 크기와 밀도에 따라)

---

## Phase 3: SYNTHESIZE (패턴 집계)

Phase 2의 raw records를 세 관찰 대상으로 분리:

### Tesseract-C (Client Decision Model) -- position facets

S6에서 이미 발견된 프레임워크:

```
강사가 명시한 의사결정 구조 (4 핵심 요소):
  1. 관심 (Interest) -- "첫 3초가 승부를 결정"
  2. 문제 인식 -- "고객이 스스로 현재 상황의 문제점을 깨닫게"
  3. 해결 확신 -- "우리가 제시하는 솔루션이 실제로 해결할 수 있다는 믿음"
  4. 긴급성 (Urgency) -- "지금 당장 결정해야 하는 명확한 이유"

  메타 원칙:
  "사람은 논리로 결정하지 않는다. 감정으로 결정하고, 논리는 설명하기 위해 존재"
  실제 구매 결정: 감정적 충동(3초) → 논리적 정당화 → 행동 실행
```

S4에서 이미 발견된 반론 패턴 (처음 8/30개):

```
1. "이미 마케팅 업체가 있습니다" -- 현상유지 편향
2. "병원 마케팅 안 믿습니다" -- 불신/과거 경험
3. "비용이 너무 비싸네요" -- 가격 민감성
4. "지금은 시기상 어려워요" -- 시점 회피
5. "환불되나요?" -- 리스크 회피
6. "우리는 입소문으로 충분해요" -- 자족/관성
7. "저희 지역은 경쟁이 너무 치열합니다" -- 외부 귀인
8. "직원들이 반대합니다" -- 내부 저항
```

→ 이것들은 facet의 값(enum) 후보이지 facet 자체가 아니다.
→ facet은 "저항 유형", "의사결정 단계", "신뢰 수준" 같은 상위 축.
→ position이므로: 강사가 관찰하든 김한얼이 관찰하든 같은 값이어야 함.

### Tesseract-L (Lecturer Strategy) -- distance facets (강사 관점)

S6에서 발견된 프레임워크:

```
7단계 영업 프로세스:
  DB 구축 → 접촉 → 통화 → 1st 미팅 → 진단 리포트 → 제안 미팅 → 계약 확정

전환율 모델:
  DB 50 → DM 50 → 통화 10 → 미팅 3 → 계약 1

필요 자산: 블로그 AI툴, 팀, 병원 네트워크, MSO 역량
```

S1에서 발견된 전략 원칙:

```
- "분석 먼저, 영업 나중에" (= SI 컨설팅형)
- 지역별 분기 (서울/지방, 외국인/국내)
- 병원 먼저 분석 → 맞춤 제안서 → 미팅
- "합리적이게 왜, 어떤 근거에서" → 프로세스 명확 설명
- "원장님들은 까다로운 게 아니라 합리적인 것" → 존중 기반 접근
```

→ 이 전략들은 강사의 자산/역량에 묶여 있다 (distance).
→ facet 후보: "접근 방식", "가치 전달 방법", "퍼널 단계", "자산 활용 패턴"

### Tesseract-K (Kim Strategy) -- distance facets (김한얼 관점)

Phase 3에서 L의 facet이 확정된 후, L→K bridge mapping 수행:

```
각 L facet에 대해:
  (1) K가 동일 value를 쓸 수 있는가? → 공통 (직접 적용)
  (2) K가 다른 value를 써야 하는가? → 번역 (자산 대체)
  (3) K가 해당 facet 자체를 쓸 수 없는가? → gap (역량 부재)
  (4) K만 가진 facet이 있는가? → surplus (차별화)

이미 파악된 K surplus:
  - Lazarus/Tesseract 좌표계 (체계적 분석)
  - AI IDE 범용 자동화 (블로그 전용보다 넓음)
  - 255d 벡터 + 24 서비스 모듈
  - 디자인 직접 제작 역량
  - 30곳 경쟁분석 이미 보유 (강사 접근법의 "진단 리포트"를 이미 실행)
```

---

## Phase 4: SPEC (설계) -- Phase 3 완료 후

### Tesseract-C 설계
- 후보 facet → position으로 확인 (관찰자 무관성 검증)
- 기존 Tesseract 10F (F01-F10) 과 직교성 확인
- 일반화 검증: "의사" → "변호사", "회계사" 등으로 치환해도 축이 유효한지

### Tesseract-L 설계
- 후보 facet → distance로 확인 (강사 맥락 종속성 검증)
- C와의 관계 정의 (C의 어떤 값을 읽고 L의 어떤 전략을 선택하는지)
- 일반화 검증: "병원마케팅 전문가" → "법률마케팅 전문가" 등으로 치환

### Tesseract-K 설계
- L→K bridge map 기반으로 K facet 도출
- gap 목록 → 단기 회피 vs 장기 역량 구축 분류
- surplus 목록 → 차별화 전략 설계
- Telescope (사용자) HITL 판단

## Phase 5: VALIDATE -- Phase 4 완료 후

- 설계된 3개 좌표계로 원본 데이터 재코딩
- coverage 확인 (빠진 데이터 없는지)
- 도메인 비종속성 확인 (병원→법률, 병원→회계 등 치환)
- 실전 검증: 유제의원 케이스에 C/K 적용하여 meeting_prep.md와 대조

---

## Probe Execution Log

| Probe | Source | Records | Status | Date | Notes |
|-------|--------|---------|--------|------|-------|
| P1 | S4 시나리오 30선 | 30 | done | 2026-03-08 | 30/30 시나리오, C/L 양면 |
| P2 | S6 영업 가이드 | 13 | done | 2026-03-08 | P1 교차검증 완료 |
| P3 | S1 특강 녹취록 | 127 | done | 2026-03-08 | S7 슬라이드 교차참조, 5 parallel agents |
| P4 | S3 레이저제모 리서치 | 124 | done | 2026-03-08 | 사용자-AI 대화, 5 parallel agents |
| P5 | S2 업태분석 | - | pending | - | K의 시장 좌표 |
| P6 | S5 AI 블로그 | - | pending | - | L의 도구 vs K의 도구 |
| **합계** | | **294** | **4/6** | | |

### 중간 발견 요약 (P1-P4)

**Tesseract-C facet 후보** (position):
1. resistance_type: status_quo / distrust / trauma / cost / risk / timing / external / internal / competition_fear / uncertainty / none
2. awareness_level: unaware / problem_aware / cause_aware / solution_aware
3. decision_stage: interest / recognition / conviction / urgency
4. pain_point, prior_attempt, desired_state
5. value_orientation: cost_driven / data_driven / relationship_driven / brand_driven

**Tesseract-L facet 후보** (distance, 강사):
1. pipeline_stage: 7단계
2. response_strategy: 8+ 패턴
3. stage_objective: 단계별 목표 한정
4. commitment_unit: 점진적 확대
5. conversion_rate
6. market_phase: 5단계 (개척→황금→과열→붕괴전조→구조조정) [P4 신규]
7. dead-end funnel 판별 [P4 신규]
8. 4단계 성공 공식, 매출 공식, 맞춤전략 4변수 [P3 신규]

**Tesseract-K**:
- SURPLUS: DB 30곳, AI IDE+디자인 진단, Lazarus/Tesseract 좌표계
- GAP: ⑥제안(실적0), ⑦계약(구조미설계)
- P4 신규: 3단 서비스(진단/설계/운영), "구조 판단" 포지셔닝, 구조조정기 진입 타이밍

---

## 복원 포인터

- 실험 파일: `~/Documents/Lazarus/experiments/EXP-HMK-001-hospital-marketing-probe.md`
- 소스 위치: `~/Documents/.../Spotlight_Works/docs/8. 병원마케팅/1. 기획/`
- 프로브 산출물: `~/Documents/Tesseract/probes/hmk/` (P1-P4 완료)
- 트리거: "HMK 프로브 계속" → P5(업태분석)부터 실행
- 관련 문서:
  - Tesseract spec: `~/Documents/Tesseract/spec/`
  - Tesseract T1 review: `~/Documents/Tesseract/docs/t1_hitl_review_results.md`
  - SW strategy course: `~/Documents/.../Spotlight_Works/spotlighting/intelligence/strategy_course_yuje.json`
