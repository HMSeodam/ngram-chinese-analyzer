# N-gram Chinese Text Analyzer

한자 텍스트의 N-gram 분석을 위한 웹 애플리케이션입니다. FastAPI와 Bootstrap을 사용하여 구축되었으며, 다국어 지원(한국어, 영어, 중국어, 일본어)을 제공합니다.

## 🌟 주요 기능

- **파일 업로드**: TXT, HTML, HWP 파일 지원
- **N-gram 분석**: 2-4자 한자 조합 분석
- **필터링**: 전체 분석 및 공통 부분 분석
- **정렬**: 빈도수 오름차순/내림차순
- **하이라이트**: 원본 텍스트에 분석 결과 하이라이트 적용
- **워드클라우드**: 분석 결과 시각화
- **다운로드**: HTML, Word(.docx), 한글(.hwp) 형식 지원
- **다국어 지원**: 한국어, 영어, 중국어, 일본어

## 🚀 배포된 서비스

**Live Demo**: [https://ngram-chinese-analyzer.onrender.com](https://ngram-chinese-analyzer.onrender.com)

## 🛠️ 기술 스택

- **Backend**: FastAPI, Python 3.11
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **분석**: N-gram 알고리즘, WordCloud
- **배포**: Render.com

## 📦 설치 및 실행

### 로컬 개발 환경

1. **저장소 클론**
   ```bash
   git clone https://github.com/your-username/ngram-chinese-analyzer.git
   cd ngram-chinese-analyzer
   ```

2. **가상환경 생성 및 활성화**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

4. **서버 실행**
   ```bash
   python ngsm.py
   ```

5. **브라우저에서 접속**
   ```
   http://localhost:8000
   ```

### Render.com 배포

1. **GitHub에 코드 푸시**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Render.com에서 새 Web Service 생성**
   - GitHub 저장소 연결
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn ngsm:app --host 0.0.0.0 --port $PORT`

## 📁 프로젝트 구조

```
ngram-chinese-analyzer/
├── ngsm.py                  # 메인 서버 파일
├── requirements.txt          # Python 의존성
├── runtime.txt              # Python 버전
├── render.yaml              # Render.com 설정
├── README.md               # 프로젝트 문서
├── static/                 # 정적 파일
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── templates/              # HTML 템플릿
    └── index.html
```

## 🔧 사용 방법

1. **파일 업로드**: 2개 이상의 텍스트 파일 선택
2. **N-gram 설정**: 최소/최대 N-gram 값 설정 (기본: 2-4)
3. **분석 실행**: "분석 시작" 버튼 클릭
4. **필터링**: 전체 분석 또는 공통 부분 분석 선택
5. **하이라이트**: "하이라이트 적용" 버튼으로 원본 텍스트에 결과 적용
6. **다운로드**: 다양한 형식으로 결과 다운로드

## 🌐 다국어 지원

- 한국어 (ko)
- 영어 (en)
- 중국어 (zh)
- 일본어 (ja)

언어는 우측 상단 드롭다운에서 변경할 수 있습니다.

## 📝 API 엔드포인트

- `GET /`: 메인 페이지
- `POST /api/analyze`: 파일 분석
- `POST /api/filter`: N-gram 필터링
- `POST /api/apply-highlight`: 하이라이트 적용
- `GET /api/download-highlight`: 하이라이트 결과 다운로드
- `POST /api/download`: 분석 결과 다운로드
- `POST /api/wordcloud`: 워드클라우드 생성

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 GitHub Issues를 통해 연락해 주세요.

---

**Made with ❤️ for Chinese text analysis** 