import streamlit as st
import fitz  # PyMuPDF
from google import genai
import time
import io

# 1. AI 설정
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# 웹 화면 구성
st.set_page_config(page_title="주식 리포트 AI 분석기", layout="centered")
st.title("📈 주식 리포트 AI 비서")
st.info("모바일에서도 PDF 파일을 업로드하여 바로 분석 결과를 확인하세요.")

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

# 파일 업로더
uploaded_file = st.file_uploader("증권사 리포트(PDF) 선택", type="pdf")

if uploaded_file is not None:
    with st.spinner('리포트를 정독하고 있습니다. 잠시만 기다려 주세요...'):
        try:
            # PDF 텍스트 추출 (메모리 직접 읽기)
            file_bytes = uploaded_file.read()
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = "".join([page.get_text() for page in doc])
            
            prompt = f"""
            당신은 초보 투자자를 돕는 전문 분석가입니다. 
            다음 리포트를 [리포트 성격, 1.핵심요약, 2.상세풀이, 3.투자제언, 4.주요지표] 순서로 분석해 주세요.
            어려운 용어는 반드시 ( ) 안에 쉬운 우리말 뜻을 달아주세요.
            리포트 내용: {text[:15000]}
            """
            
            # 구글 서버 과부하(503 에러) 대응: 최대 3회 자동 재시도
            max_retries = 3
            response = None
            
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(model=target_model, contents=prompt)
                    break  # 성공 시 반복문 탈출
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        st.warning(f"구글 서버 과부하로 대기 중입니다. ({attempt+1}/3차 자동 재시도)")
                        time.sleep(3)  # 3초 대기 후 다시 시도
                    else:
                        raise e  # 다른 에러거나 최대 횟수를 넘기면 에러 출력
            
            # 결과 출력
            st.markdown("---")
            st.subheader("📋 분석 결과")
            st.markdown(response.text)
            
            # 다운로드 버튼
            st.download_button(
                label="분석 결과 저장하기",
                data=response.text,
                file_name=f"분석결과_{uploaded_file.name}.txt",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")

st.sidebar.caption(f"작동 모델: {target_model}")
