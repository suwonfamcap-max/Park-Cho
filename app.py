import streamlit as st
import fitz
from google import genai
import tempfile
import os

# 1. 설정 (클라우드 비밀변수에서 API 키 불러오기)
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

st.set_page_config(page_title="주식 리포트 AI 분석기", layout="wide")
st.title("📈 주식 리포트 초보자용 분석기")
st.write("PDF 파일을 아래에 끌어다 놓으세요. AI가 이름을 자동으로 찾아 분석합니다.")

# 2. 사용할 수 있는 모델 이름을 자동으로 찾는 함수
def get_working_model():
    try:
        models = client.models.list()
        for m in models:
            if 'flash' in m.name:
                return m.name
    except:
        return "gemini-1.5-flash"
    return "gemini-1.5-flash"

target_model = get_working_model()

# 파일 업로더
uploaded_file = st.file_uploader("PDF 리포트를 선택하세요", type="pdf")

if uploaded_file is not None:
    with st.spinner(f'AI({target_model})가 리포트를 정독하고 있습니다...'):
        # PDF에서 텍스트 추출
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            doc = fitz.open(tmp_file.name)
            text = "".join([page.get_text() for page in doc])
        
        # AI 분석 요청
        prompt = f"""
        당신은 초보 투자자를 돕는 전문 분석가입니다. 
        다음 리포트를 [리포트 성격, 1.핵심요약, 2.상세풀이, 3.투자제언, 4.주요지표] 순서로 분석해 주세요.
        어려운 용어는 반드시 ( ) 안에 쉬운 우리말 뜻을 달아주세요.
        
        리포트 내용: {text[:15000]}
        """
        
        try:
            # 자동으로 찾은 모델명으로 실행
            response = client.models.generate_content(
                model=target_model, 
                contents=prompt
            )
            
            # 결과 출력
            st.divider()
            st.markdown(response.text)
            st.success("분석이 완료되었습니다!")
            
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")

st.sidebar.info(f"연결된 모델: {target_model}")