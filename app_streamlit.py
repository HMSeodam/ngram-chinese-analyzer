import streamlit as st
import requests
import json

st.title("N-gram Chinese Text Analyzer (Streamlit)")

# 파일 업로드
uploaded_files = st.file_uploader("한자 텍스트 파일 업로드 (2개 이상)", type=["txt"], accept_multiple_files=True)
min_n = st.number_input("N-gram 최소값", min_value=2, max_value=10, value=2)
max_n = st.number_input("N-gram 최대값", min_value=2, max_value=10, value=4)

if st.button("분석 시작") and uploaded_files and len(uploaded_files) >= 2:
    files = [("files", (f.name, f, "text/plain")) for f in uploaded_files]
    data = {"min_n": min_n, "max_n": max_n}
    response = requests.post("http://localhost:8000/api/analyze", files=files, data=data)
    if response.ok:
        result = response.json()
        st.success("분석 완료!")
        st.write(result["results"])
        st.session_state["ngram_results"] = result["results"]
    else:
        st.error(response.text)

if st.button("워드클라우드 생성"):
    ngram_results = st.session_state.get("ngram_results", None)
    if ngram_results:
        wc_response = requests.post(
            "http://localhost:8000/api/wordcloud",
            data={"ngrams_data": json.dumps(ngram_results)}
        )
        if wc_response.ok:
            st.image(wc_response.content)
        else:
            st.error(wc_response.text)
    else:
        st.warning("먼저 분석을 진행하세요.")