# EXP-UNI-001: Lazarus 통일장 전환

> Status: draft
> Created: 2026-03-08
> Objective: 6개 독립 프로젝트를 Lazarus 단일 메타 프로토콜로 통일

## Objective

모든 하류 프로젝트가 Lazarus를 import하고, 시행착오가 좌표로 누적되어
새 프로젝트의 탐색 비용이 감소하는 시스템을 만든다.

## Key Results (탐색 완료 측정)

- KR1: 6개 프로젝트의 20 facet 스키마 비교 완료 (같은지/다른지 판별)
- KR2: 255d 구조 비교 완료 (Spotlight Works vs DT_Cartography)
- KR3: exploration_map.json 스키마 v0.1 설계 완료
- KR4: Decision Commit Protocol CLAUDE.md 반영 완료
- KR5: 1개 프로젝트에서 exploration_map 파일럿 실행

## 대상 프로젝트

| # | 프로젝트 | 현재 연동 | 통일 난이도 |
|---|----------|----------|------------|
| 1 | Parallax | lazarus import (깊음) | 낮음 -- 이미 통합 |
| 2 | Spotlight Works | lazarus import (중간) | 중간 -- convergence 연결, 4-tuple 숫자 제거 |
| 3 | AI MVP 5th | lazarus import (깊음) | 낮음 -- DomainRegistry 이미 있음 |
| 4 | DT_Cartography | 독립구현 | 높음 -- KK 0-100 categorical 전환, import 전환 |
| 5 | DT_Genome | 독립구현 | 중간 -- 스키마 호환성 확인 후 import 전환 |
| 7 | Tesseract | GitHub repo (submodule) | - | 10 facet + T1-T4 | RPD+Satisficing 핵심 |
| 6 | 260205 Bootcamp | submodule | 낮음 -- pip -e 전환 |

## 가설

- H1: 3개 프로젝트의 20 facet은 동일한 NSM prime 매핑이다
- H2: exploration_map은 프로젝트 횡단으로 운영 가능하다
- H3: Workspace Complexity는 exploration_map의 부산물이다 (별도 모듈 불필요)
- H4: DT_Cartography의 KK score는 enum 구간으로 전환 가능하다
- H5: Tesseract의 10 facet은 기존 20 facet과 직교(orthogonal)하다
- H6: Tesseract(discovery) -> Lazarus(collection) -> Parallax(triangulation) cosmology가 통일장의 파이프라인이다

## 제약조건 (C9 사전 검토)

- 모든 단계에서 C1-C11 준수
- 스키마 통일 시 C2 (enum 불변) -- 기존 스키마를 변경하는 게 아니라 canonical을 확정
- exploration_map 데이터는 전부 source_type 태깅 (C6)
- KK score categorical 전환 시 기존 데이터 소급 적용 여부는 별도 결정

## 우선순위

1. facet 스키마 비교 (H1 검증) -- 통일의 전제조건
2. exploration_map 스키마 설계 -- 오늘 논의의 핵심 산출물
3. Decision Commit Protocol CLAUDE.md 반영 -- Section 9 교체
4. Spotlight Works convergence 연결 -- 실전 검증
5. DT_Cartography categorical 전환 -- 가장 큰 작업
6. Tesseract 10 facet과 기존 20 facet 관계 조사
7. 파일 시스템 정리 -- 중복 제거 + ~/Projects/ 분리 + iCloud 정리
