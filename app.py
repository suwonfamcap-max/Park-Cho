import streamlit as st
import fitz  # PyMuPDF
from google import genai
import time

# 1. AI 설정 (클라우드 비밀변수에서 안전하게 호출)
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# 웹 화면 구성
st.set_page_config(page_title="주식 리포트 정밀 분석기", layout="wide")
st.title("📊 주식 리포트 수치 정밀 분석기")
st.info("스마트폰에 다운로드한 증권사 리포트(PDF)를 업로드해 주세요.")

# 정밀한 수치(표) 추출을 위해 똑똑한 Pro 모델로 고정
target_model = "gemini-1.5-pro"

# 오직 '파일 업로드'만 남김
uploaded_file = st.file_uploader("리포트 PDF 파일 선택", type="pdf")

if uploaded_file is not None:
    with st.spinner('리포트에서 핵심 수치를 추출하고 있습니다. 잠시만 기다려주세요...'):
        try:
            # 스마트폰 환경에서도 안전하게 PDF 읽기
            file_bytes = uploaded_file.read()
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = "".join([page.get_text() for page in doc])
            
            # AI에게 표 형태와 필수 항목을 강제로 지시하는 강력한 프롬프트
            prompt = f"""
            당신은 기업 재무 분석 전문가입니다. 다음 리포트에서 아래 정보를 반드시 '표(Table)' 형식으로 깔끔하게 추출해 주세요.
            리포트에 없는 정보는 억지로 지어내지 말고 '정보 없음'이라고 표기하세요.

            [필수 추출 항목]
            1. 기본 정보 (표 1): 종목이름, 현재가(리포트 시점), 목표가, 투자의견
            2. 연도별 실적 추정 (표 2 - 최근 3~4개년): 연도, 매출액, 영업이익, 영업이익률(OPM), 순이익, PER
            3. 성장성 지표 (표 3): 연도, 매출액 성장률(YoY), 영업이익 성장률(YoY)
            4. 리포트 핵심 요약 (텍스트): 3줄 이내로 명확하게 요약

            답변은 반드시 Markdown 문법을 사용하여 표가 깨지지 않게 출력하고, 핵심 수치(목표가, 높은 성장률 등)는 굵게(bold) 강조해 주세요.

            리포트 내용: {text[:20000]}
            """
            
            # 구글 서버 503 과부하 에러 대응 (최대 3회 자동 재시도)
            max_retries = 3
            response = None
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(model=target_model, contents=prompt)
                    break
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        st.warning(f"구글 서버 대기열 지연... ({attempt+1}/3차 재시도 중)")
                        time.sleep(3) # 3초 쉬고 다시 요청
                        continue
                    raise e
            
            # 결과 화면 출력
            st.markdown("---")
            st.markdown(f"### 🎯 [{uploaded_file.name}] 분석 결과")
            st.markdown(response.text)
            
            # 결과 저장 버튼
            st.download_button(
                label="이 분석 결과 저장하기 (텍스트 파일)",
                data=response.text,
                file_name=f"수치분석결과_{uploaded_file.name}.txt",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
            st.info("구글 서버 트래픽 문제일 수 있으니 잠시 후 파일을 닫았다가 다시 올려주세요.")

st.sidebar.caption(f"현재 작동 엔진: {target_model}")
