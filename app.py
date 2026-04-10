import streamlit as st
import fitz  # PyMuPDF
from google import genai
import io

# 1. AI 설정 (클라우드 Secrets에서 안전하게 가져옴)
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# 웹 화면 구성 (모바일 최적화)
st.set_page_config(page_title="주식 리포트 AI 분석기", layout="centered")
st.title("📈 주식 리포트 AI 비서")
st.info("모바일에서도 PDF 파일을 업로드하여 바로 분석 결과를 확인하세요.")

# 2. 사용할 수 있는 모델 자동 탐색
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

# 파일 업로더 (모바일 대응 강화)
uploaded_file = st.file_uploader("증권사 리포트(PDF) 선택", type="pdf")

if uploaded_file is not None:
    with st.spinner('리포트를 정독하고 있습니다. 잠시만 기다려 주세요...'):
        try:
            # [개선] 임시 파일 대신 메모리 스트림으로 직접 읽기 (모바일 오류 방지)
            file_bytes = uploaded_file.read()
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = "".join([page.get_text() for page in doc])
            
            # AI 분석 요청
            prompt = f"""
            당신은 초보 투자자를 돕는 전문 분석가입니다. 
            다음 리포트를 [리포트 성격, 1.핵심요약, 2.상세풀이, 3.투자제언, 4.주요지표] 순서로 분석해 주세요.
            어려운 용어는 반드시 ( ) 안에 쉬운 우리말 뜻을 달아주세요.
            리포트 내용: {text[:15000]}
            """
            
            response = client.models.generate_content(model=target_model, contents=prompt)
            
            # 결과 출력
            st.markdown("---")
            st.subheader("📋 분석 결과")
            st.markdown(response.text)
            st.success("분석이 완료되었습니다!")
            
            # [추가 기능] 분석 결과 텍스트 다운로드 버튼
            st.download_button(
                label="분석 결과 저장하기",
                data=response.text,
                file_name=f"분석결과_{uploaded_file.name}.txt",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")

st.sidebar.caption(f"작동 모델: {target_model}")
