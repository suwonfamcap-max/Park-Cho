import streamlit as st
import fitz  # PyMuPDF
from google import genai
import time
import io

# 1. AI 설정
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

st.set_page_config(page_title="주식 리포트 수치 분석기", layout="wide")
st.title("📊 리포트 핵심 수치 정밀 분석")
st.write("PDF 파일을 업로드하면 종목 정보와 재무 추정치를 표로 정리해 드립니다.")

@st.cache_resource
def get_working_model():
    try:
        models = client.models.list()
        for m in models:
            if 'flash' in m.name: return m.name
    except: return "gemini-2.0-flash"
    return "gemini-1.5-flash"

target_model = get_working_model()

# 파일 업로더
uploaded_file = st.file_uploader("증권사 리포트(PDF) 선택", type="pdf")

if uploaded_file is not None:
    with st.spinner('리포트에서 숫자를 추출하고 있습니다...'):
        try:
            # PDF 텍스트 추출
            file_bytes = uploaded_file.read()
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = "".join([page.get_text() for page in doc])
            
            # AI에게 숫자 위주의 분석 지시 (프롬프트 강화)
            prompt = f"""
            당신은 기업 분석 전문가입니다. 다음 리포트에서 아래 정보를 반드시 '표(Table)' 형식으로 추출해 주세요.
            만약 리포트에 해당 정보가 없다면 '정보 없음'이라고 표기해 주세요.

            1. 기본 정보: 종목이름, 현재가(리포트 시점), 목표가, 투자의견
            2. 연도별 실적 추정 (최근 3~4개년 정보 위주):
               - 연도 / 매출액 / 영업이익 / 영업이익률(OPM) / 순이익 / PER
            3. 성장성 지표:
               - 매출액 성장률(YoY), 영업이익 성장률(YoY)
            4. 리포트 핵심 요약 (3줄 이내)

            답변은 Markdown 형식을 사용하여 표가 깨지지 않게 해주고, 
            중요한 수치(목표가 등)는 굵게(bold) 표시해 주세요.

            리포트 내용: {text[:20000]}
            """
            
            # 유료 계정이라도 발생할 수 있는 503 에러 대응
            max_retries = 3
            response = None
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(model=target_model, contents=prompt)
                    break
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    raise e
            
            # 결과 출력
            st.divider()
            st.markdown(f"### 🎯 {uploaded_file.name} 분석 결과")
            st.markdown(response.text)
            
            # 다운로드 버튼
            st.download_button(
                label="분석 데이터 다운로드 (텍스트)",
                data=response.text,
                file_name=f"수치분석_{uploaded_file.name}.txt",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")

st.sidebar.caption(f"분석 엔진: {target_model}")
