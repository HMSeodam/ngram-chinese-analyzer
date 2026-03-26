# N-gram Chinese Text Analyzer (한문 N-gram 분석기)

[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)

한문(漢文) 텍스트 여러 판본을 업로드하여 **N-gram 빈도 분석**, **공통 구절 추출**, **원문 하이라이트**, **워드클라우드 시각화**를 제공하는 디지털 인문학 도구입니다.

> 서버 불필요 — GitHub Pages에서 브라우저만으로 바로 실행됩니다.

---

## 👉 바로 사용하기

**[https://hmseodam.github.io/ngram-chinese-analyzer/](https://hmseodam.github.io/ngram-chinese-analyzer/)**

---

## 최신 버전 소식 (Changelog)

### ver1.1 (2026-03-26)

#### ⚡ 성능 개선

- **Web Worker** 적용 — N-gram 연산을 백그라운드 스레드로 분리하여 대용량 파일 분석 중에도 UI가 멈추지 않습니다.
- **가상 스크롤** 도입 — 수십만 건의 결과를 화면에 보이는 행만 렌더링하여 표시 속도를 대폭 개선했습니다.
- **진행률 표시** — 분석 중 퍼센트 프로그레스 바를 표시합니다.

#### 🔤 한자 인식 범위 전면 확장

- 한국·일본·대만·중국의 모든 한자를 빠짐없이 카운트하도록 유니코드 범위를 확장했습니다.
  - CJK Extension C~H (U+2A700–U+323AF)
  - Kangxi Radicals / CJK Radicals Supplement
  - Enclosed CJK, Kanbun, CJK Strokes 등
- **서로게이트 페어(고대역 한자) 처리 수정** — `𠿒`(U+20FD2), `𦍞`(U+2635E) 등 Extension B 이상 한자가 JS에서 2개로 쪼개져 누락되던 버그를 수정했습니다. (`content[i]` → `for...of` 순회 방식 변경)

#### 📊 다운로드 기능 강화

- **엑셀(.xlsx) 다운로드** 추가 — SheetJS 기반, 헤더 색상·열 너비 자동 설정, 정보 시트 포함
- 다운로드 기본 선택을 xlsx로 변경

#### 🖊️ N-gram 하이라이트 창 전면 개선

- **창 제목** — `about:blank` 대신 `파일명 × 분석모드 — N-gram 하이라이트` 형식으로 표시
- **저장 버튼** — HTML / Word(.doc) / JSON 3종 지원 (HWP·TXT 제거, JSON 신규 추가)
  - JSON 저장 시 파일명·모드·날짜·통계·N-gram 목록·하이라이트 위치 인덱스 포함
- **전체 폭 활용** — PC에서 최대 1,400px로 화면 폭 충분히 활용
- **글자 크기 조절** — 툴바 A− / A+ 버튼으로 12~32px 범위 조절 가능 (기본 17px)
- **모바일 pinch-zoom 허용** — `maximum-scale=5` 설정
- **줄 간격 최적화** — `line-height: 1.7`, `white-space: pre-wrap` 제거로 엔터 부분 이중 줄바꿈 버그 수정
- **기본 글자 크기** — PC 17px / 모바일 16px로 가독성 향상

#### 🎨 디자인 통일

- 메인 화면과 하이라이트 창의 CSS 토큰(`--brand`, `--font`, `--bg` 등) 통일
- Noto Serif KR 폰트, 네이비 색상, 카드 스타일, 스크롤바 전체 일관 적용
- 테이블 헤더 색상 메인 브랜드 컬러(네이비)로 변경

#### 🔧 기타

- **초기화 버튼** 추가 — 파일·분석 결과·설정 전체 리셋
- **워드클라우드** 개선 — Noto Serif KR 폰트 적용, 표시 항목 80개 → 300개 확장, 파스텔 팔레트 적용
- 저작권 연도 2025 수정

---

## 주요 기능

- **파일 업로드**: TXT, HTML 파일 2개 이상 지원
- **N-gram 분석**: 2~4자(기본) 한자 조합 빈도 분석, Web Worker 백그라운드 처리
- **필터링**: 전체 분석 / 공통 부분 교집합 추출
- **정렬**: 빈도수 오름차순 / 내림차순
- **하이라이트**: 분석 N-gram을 원문에 빨간색으로 표시, HTML·Word·JSON 저장
- **워드클라우드**: 캔버스 기반 시각화(최대 300항목) 및 PNG 저장
- **다운로드**: XLSX / HTML / TXT 형식
- **다국어**: 한국어 · English · 中文 · 日本語

---

## 기술 스택

- **순수 프론트엔드**: Vanilla JS + Web Worker (서버·백엔드 없음)
- **UI**: Bootstrap 5 + Font Awesome + Noto Serif KR
- **엑셀**: SheetJS (xlsx)
- **호스팅**: GitHub Pages

---

## 라이선스

Copyright (c) 2025 **서담 한민수 (Han Minsu), 동명대학교 (Tongmyong University)**

이 프로젝트는 [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ko) 라이선스를 따릅니다.

- ✅ 저작자 표시 조건 하에 공유·복제 허용
- ❌ 상업적 이용 금지
- ❌ 변형·2차 저작물 배포 금지

상업적 이용 또는 변경 배포를 원하시는 경우 저작자에게 별도 문의하시기 바랍니다.

---

## 인용 (Citation)

이 도구를 연구에 사용하셨다면 다음과 같이 인용해 주세요:

> 한민수 (2025). N-gram Chinese Text Analyzer. GitHub. https://github.com/HMSeodam/ngram-chinese-analyzer

또는 `CITATION.cff` 참고.
