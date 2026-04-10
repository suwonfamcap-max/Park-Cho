import streamlit as st
import fitz  # PyMuPDF
from google import genai
import requests
import time
import io

# 1. AI 설정
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

st.set_page_config(page_title="주식 리포트 AI 분석기", layout="centered")
st.title("📈 주식 리포트 AI 비서")
st.write("PDF 파일을 올리거나 리포트 링크(URL)를 입력해 주세요.")

@st.cache_resource
def get_working_model():
    try:
        models = client.models.list()
        for m in models:
            if 'flash' in m.name: return m.name
    except:
        return "gemini-2.0-flash"
    return "gemini-1.5-flash"

target_model = get_working_model()

# 입력 방식 선택
option = st.radio("분석 방식 선택", ["파일 업로드", "링크(URL) 입력"])
text = ""
file_name = "report"

if option == "파일 업로드":
    uploaded_file = st.file_uploader("증권사 리포트(PDF) 선택", type="pdf")
    if uploaded_file:
        file_bytes = uploaded_file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "".join([page.get_text() for page in doc])
        file_name = uploaded_file.name

else:
    url = st.text_input("리포트 PDF 주소를 입력하세요 (예: http://...pdf)")
    if url:
        try:
            with st.spinner('링크에서 리포트를 가져오고 있습니다...'):
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    # PDF인지 일반 웹페이지인지 확인 후 텍스트 추출
                    if "application/pdf" in response.headers.get('Content-Type', ''):
                        doc = fitz.open(stream=response.content, filetype="pdf")
                        text = "".join([page.get_text() for page in doc])
                    else:
                        text = response.text # 일반 웹페이지일 경우
                    file_name = "link_report"
                else:
                    st.error("링크에 접속할 수 없습니다. 주소를 다시 확인해 주세요.")
        except Exception as e:
            st.error(f"링크를 읽는 중 오류가 발생했습니다: {e}")

# 분석 실행
if text:
    if st.button("분석 시작"):
        with st.spinner('AI가 내용을 정독하고 있습니다...'):
            prompt = f"""
            당신은 초보 투자자를 돕는 전문 분석가입니다. 
            다음 내용을 [리포트 성격, 1.핵심요약, 2.상세풀이, 3.투자제언, 4.주요지표] 순서로 분석해 주세요.
            어려운 용어는 반드시 ( ) 안에 쉬운 우리말 뜻을 달아주세요.
            내용: {text[:20000]}
            """
            
            try:
                max_retries = 3
                ai_response = None
                for attempt in range(max_retries):
                    try:
                        ai_response = client.models.generate_content(model=target_model, contents=prompt)
                        break
                    except Exception as e:
                        if "503" in str(e) and attempt < max_retries - 1:
                            time.sleep(3)
                        else:
                            raise e
                
                st.markdown("---")
                st.subheader("📋 분석 결과")
                st.markdown(ai_response.text)
                
                st.download_button(
                    label="분석 결과 저장하기",
                    data=ai_response.text,
                    file_name=f"분석결과_{file_name}.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}")

st.sidebar.caption(f"작동 모델: {target_model}")
