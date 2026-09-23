import streamlit as st
from openai import OpenAI

# 페이지 기본 설정 (타이틀 및 아이콘)
st.set_page_config(page_title="AI 정보 선생님", page_icon="💬")

st.title("💬 친절한 AI 정보 선생님")
st.write("궁금한 점이 있다면 무엇이든 편하게 물어보세요!")

# 1. Secrets에서 Gemini API 키 불러오기
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API 키를 찾을 수 없습니다. .streamlit/secrets.toml 파일에 GEMINI_API_KEY를 설정해 주세요.")
    st.stop()

# 2. OpenAI 클라이언트를 Gemini 호환 엔드포인트로 설정
client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# 3. AI 페르소나(시스템 프롬프트) 설정
SYSTEM_PROMPT = (
    "너는 중고등학생에게 설명하는 친절한 정보 선생님이야. "
    "어려운 말은 쉬운 말로 바꿔 주고, 반드시 순수 한국어로만 답해"
)

# 4. 세션 상태(Session State)를 활용해 대화 기록 초기화 및 유지
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. 기존 대화 기록을 화면에 말풍선 형태로 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. 사용자 입력창 처리
if user_input := st.chat_input("선생님에게 질문을 입력하세요..."):
    # 사용자 메시지를 화면에 즉시 표시
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # 대화 기록에 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 7. AI 응답 생성 및 실시간 스트리밍 출력
    with st.chat_message("assistant"):
        try:
            # 전달할 전체 대화 목록 구성 (시스템 프롬프트 + 이전 대화 기록)
            api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
                {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
            ]

            # OpenAI SDK를 통한 스트리밍 요청 (gemini-3.5-flash-lite 모델 지정)
            stream = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=api_messages,
                stream=True
            )

            # 실시간으로 글자가 흘러나오도록 st.write_stream 활용
            response_text = st.write_stream(stream)

            # 답변 완료 후 대화 기록에 AI 응답 저장
            st.session_state.messages.append({"role": "assistant", "content": response_text})

        except Exception:
            # 오류 발생 시 빨간색 시스템 예외 대신 친절한 한국어 안내 출력
            st.warning("선생님이 잠시 응답하기 어려워해요. 잠시 후 다시 시도해 주세요.")
