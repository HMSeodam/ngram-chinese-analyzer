import io
import re
import random
import colorsys
import html as html_module
import json
import os
from collections import Counter
from typing import List, Dict, Set
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

app = FastAPI(title="N-gram Chinese Text Analyzer", version="2.0")

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 다국어 UI용 언어 리소스 로딩
LOCALES = {}
for fname in os.listdir("static/locales"):
    lang = os.path.splitext(fname)[0]
    with open(f"static/locales/{fname}", encoding="utf-8") as f:
        LOCALES[lang] = json.load(f)

# 한자 패턴 (N-gram.py와 동일)
HANJA_PATTERN = re.compile(r'[\u4e00-\u9fff\u3400-\u4DBF\uF900-\uFAFF\U00020000-\U0002A6DF]')

def diverse_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    """워드클라우드용 다양한 색상 함수 (노란색 계열 제외)"""
    if random_state is None:
        random_state = random.Random()
    while True:
        hue = random_state.uniform(0, 360)
        if not (50 <= hue <= 70):  # 노란색 계열 제외
            break
    h = hue / 360.0
    s = random_state.uniform(0.7, 1.0)  # 채도: 70~100%
    l = random_state.uniform(0.3, 0.7)  # 밝기: 30~70%
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    r, g, b = int(r*255), int(g*255), int(b*255)
    return f"#{r:02x}{g:02x}{b:02x}"

class NgramAnalyzer:
    """N-gram 분석 클래스 (원본 N-gram.py의 핵심 로직)"""
    
    def __init__(self):
        self.files_data = {}           # 파일명 -> 한자만 남긴 텍스트
        self.index_map = {}            # 파일명 -> 원본 텍스트에서 한자 위치(인덱스) 리스트
        self.original_text_data = {}   # 파일명 -> 원본 전체 텍스트
        self.ngram_results = {}        # 파일명 -> n-gram 카운터
        self.all_ngrams = set()        # 전체 n-gram 집합
    
    def process_files(self, files: List[UploadFile], min_n: int, max_n: int):
        """파일들을 처리하여 N-gram 분석 수행"""
        self.files_data.clear()
        self.index_map.clear()
        self.original_text_data.clear()
        self.ngram_results.clear()
        self.all_ngrams.clear()
        
        for file in files:
            try:
                content = file.file.read().decode("utf-8", errors="ignore")
                file.file.seek(0)  # 파일 포인터 리셋
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"파일 {file.filename} 읽기 오류: {str(e)}")
            
            file_name = os.path.splitext(file.filename)[0]
            self.original_text_data[file_name] = content
            
            # 한자만 추출
            processed_text = ""
            index_mapping = []
            for i, ch in enumerate(content):
                if HANJA_PATTERN.match(ch):
                    processed_text += ch
                    index_mapping.append(i)
            
            self.files_data[file_name] = processed_text
            self.index_map[file_name] = index_mapping
            
            # N-gram 카운팅
            counter = Counter()
            text_len = len(processed_text)
            for n in range(min_n, max_n + 1):
                for i in range(text_len - n + 1):
                    ngram = processed_text[i:i+n]
                    counter[ngram] += 1
            
            self.ngram_results[file_name] = counter
            self.all_ngrams.update(counter.keys())
    
    def get_analysis_results(self, sort_option: str = "빈도수 오름차순"):
        """분석 결과 반환"""
        file_keys = list(self.ngram_results.keys())
        sorted_ngrams = self.sort_ngrams(self.all_ngrams, file_keys, sort_option)
        
        lines = []
        for ngram in sorted_ngrams:
            parts = []
            for fname, counter in self.ngram_results.items():
                count = counter.get(ngram, 0)
                parts.append(f"{fname}: {count}")
            lines.append(f"{ngram}: " + ", ".join(parts))
        
        return lines
    
    def get_common_ngrams(self, selected_files: List[str], include_all_common: bool = False):
        """공통 N-gram 필터링"""
        if not selected_files:
            return []
        
        filtered_ngrams = []
        for ngram in self.all_ngrams:
            if include_all_common:
                # 모든 선택된 파일에 나타나는 N-gram
                if all(self.ngram_results[fname].get(ngram, 0) > 0 for fname in selected_files):
                    parts = [f"{fname}: {self.ngram_results[fname].get(ngram, 0)}" for fname in selected_files]
                    filtered_ngrams.append(f"{ngram}: " + ", ".join(parts))
            else:
                # 정확히 선택된 파일들에만 나타나는 N-gram
                selected_set = set(selected_files)
                appearance_set = {fname for fname, counter in self.ngram_results.items() if counter.get(ngram, 0) > 0}
                if appearance_set == selected_set and appearance_set:
                    parts = [f"{fname}: {self.ngram_results[fname].get(ngram, 0)}" for fname in selected_files]
                    filtered_ngrams.append(f"{ngram}: " + ", ".join(parts))
        
        return filtered_ngrams
    
    def sort_ngrams(self, ngrams, file_set, sort_option: str):
        """N-gram 정렬"""
        def freq_key(ngram):
            return sum(self.ngram_results[fname].get(ngram, 0) for fname in file_set)
        
        reverse = (sort_option == "빈도수 내림차순")
        return sorted(ngrams, key=freq_key, reverse=reverse)
    
    def apply_to_original_text(self, file_name: str, selected_ngrams: Set[str]):
        """원본 텍스트에 선택된 N-gram 하이라이트 적용"""
        if file_name not in self.original_text_data:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        orig_text = self.original_text_data[file_name]
        processed_text = self.files_data[file_name]
        index_mapping = self.index_map[file_name]
        
        # 하이라이트할 위치 찾기
        red_positions = set()
        for ngram in selected_ngrams:
            start_idx = 0
            while True:
                pos = processed_text.find(ngram, start_idx)
                if pos == -1:
                    break
                for offset in range(len(ngram)):
                    if pos + offset < len(index_mapping):
                        red_positions.add(index_mapping[pos + offset])
                start_idx = pos + 1
        
        # HTML 생성
        result_html = (
            "<html><head><meta charset='utf-8'>"
            "<style>"
            "body { margin: 20px; font-family: '맑은 고딕', 'Malgun Gothic', sans-serif; font-size: 14px; line-height: 1.6; }"
            ".highlight { color: red; font-weight: bold; }"
            ".stats { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }"
            "</style></head><body>"
        )
        
        # 통계 정보
        total_count = len(index_mapping)
        red_count = len(red_positions)
        ratio = (red_count / total_count * 100) if total_count > 0 else 0
        
        result_html += f"""
        <div class="stats">
            <h3>분석 결과</h3>
            <p><strong>전체 한자수:</strong> {total_count}자</p>
            <p><strong>해당 글자수:</strong> {red_count}자</p>
            <p><strong>비율:</strong> {ratio:.2f}%</p>
        </div>
        <div class="content">
        """
        
        # 텍스트 하이라이트
        for i, ch in enumerate(orig_text):
            if i in red_positions:
                result_html += f'<span class="highlight">{html_module.escape(ch)}</span>'
            else:
                result_html += html_module.escape(ch)
        
        result_html += "</div></body></html>"
        return result_html

# 전역 분석기 인스턴스
analyzer = NgramAnalyzer()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, lang: str = "ko"):
    """메인 페이지"""
    if lang not in LOCALES:
        lang = "ko"
    return templates.TemplateResponse("index.html", {
        "request": request,
        "locale": LOCALES[lang],
        "current_lang": lang
    })

@app.post("/api/analyze")
async def analyze_files(
    min_n: int = Form(...),
    max_n: int = Form(...),
    files: List[UploadFile] = File(...)
):
    """파일 분석 API"""
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="최소 2개 이상의 파일을 선택해야 합니다.")
    
    try:
        analyzer.process_files(files, min_n, max_n)
        results = analyzer.get_analysis_results()
        
        return JSONResponse({
            "success": True,
            "filenames": list(analyzer.files_data.keys()),
            "results": results,
            "data_count": len(results)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")

@app.post("/api/filter")
async def filter_ngrams(
    mode: str = Form(...),
    selected_files: str = Form(...),  # JSON string
    include_all_common: bool = Form(False),
    sort_option: str = Form("빈도수 오름차순")
):
    """N-gram 필터링 API"""
    try:
        if mode == "common":
            selected_files_list = json.loads(selected_files)
            results = analyzer.get_common_ngrams(selected_files_list, include_all_common)
            # 정렬 적용
            file_keys = selected_files_list
            sorted_ngrams = analyzer.sort_ngrams([line.split(":")[0].strip() for line in results], file_keys, sort_option)
            # 정렬된 결과 재구성
            sorted_results = []
            for ngram in sorted_ngrams:
                for line in results:
                    if line.startswith(ngram + ":"):
                        sorted_results.append(line)
                        break
            results = sorted_results
        else:
            results = analyzer.get_analysis_results(sort_option)
        
        return JSONResponse({
            "success": True,
            "results": results,
            "data_count": len(results)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"필터링 중 오류 발생: {str(e)}")

@app.post("/api/wordcloud")
async def generate_wordcloud(
    ngrams_data: str = Form(...)  # JSON string of ngram results
):
    """워드클라우드 생성 API"""
    try:
        # N-gram 데이터에서 빈도수 추출
        freq_dict = {}
        ngrams_list = json.loads(ngrams_data)
        
        for line in ngrams_list:
            if line.strip():
                parts = line.split(":")
                if len(parts) < 2:
                    continue
                ngram = parts[0].strip()
                counts = re.findall(r'\d+', line)
                total = sum(int(x) for x in counts) if counts else 0
                freq_dict[ngram] = total
        
        if not freq_dict:
            raise HTTPException(status_code=400, detail="워드클라우드 생성을 위한 유효한 데이터가 없습니다.")
        
        # 워드클라우드 생성
        try:
            # Linux 환경용 폰트 경로
            font_path = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
            if not os.path.exists(font_path):
                # Windows 환경용 폰트 경로
                font_path = "C:\\Windows\\Fonts\\msyh.ttc"
                if not os.path.exists(font_path):
                    # 기본 폰트 사용
                    font_path = None
        except:
            font_path = None
        
        wc = WordCloud(
            font_path=font_path,
            width=800,
            height=600,
            background_color="white",
            color_func=diverse_color_func,
            max_words=200
        )
        wc.generate_from_frequencies(freq_dict)
        
        # 이미지를 바이트로 변환
        img_buffer = io.BytesIO()
        wc.to_image().save(img_buffer, format="PNG")
        img_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(img_buffer.getvalue()),
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=wordcloud.png"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"워드클라우드 생성 중 오류 발생: {str(e)}")

@app.post("/api/apply-highlight")
async def apply_highlight(
    file_name: str = Form(...),
    selected_ngrams: str = Form(...)  # JSON string
):
    """원본 텍스트에 하이라이트 적용 API"""
    try:
        ngrams_set = set(json.loads(selected_ngrams))
        html_result = analyzer.apply_to_original_text(file_name, ngrams_set)
        
        return HTMLResponse(html_result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"하이라이트 적용 중 오류 발생: {str(e)}")

@app.post("/api/download")
async def download_results(
    results_data: str = Form(...),  # JSON string
    format_type: str = Form("txt")
):
    """분석 결과 다운로드 API"""
    try:
        results = json.loads(results_data)
        
        if format_type == "txt":
            content = "\n".join(results)
            return StreamingResponse(
                io.BytesIO(content.encode('utf-8')),
                media_type="text/plain",
                headers={"Content-Disposition": "attachment; filename=ngram_analysis.txt"}
            )
        elif format_type == "html":
            html_content = f"""
            <html><head><meta charset='utf-8'>
            <style>
            body {{ font-family: '맑은 고딕', 'Malgun Gothic', sans-serif; margin: 20px; }}
            .result {{ margin: 10px 0; padding: 5px; border-bottom: 1px solid #eee; }}
            </style></head><body>
            <h1>N-gram 분석 결과</h1>
            """
            for result in results:
                html_content += f'<div class="result">{html_module.escape(result)}</div>'
            html_content += "</body></html>"
            
            return StreamingResponse(
                io.BytesIO(html_content.encode('utf-8')),
                media_type="text/html",
                headers={"Content-Disposition": "attachment; filename=ngram_analysis.html"}
            )
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 형식입니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다운로드 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
