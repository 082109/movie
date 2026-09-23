import streamlit as st
from openai import OpenAI

# 1. 페이지 기본 설정
st.set_page_config(page_title="주은이와의 채팅", page_icon="💬")

# 화면 상단 타이틀 및 설명
st.title("💬 주은이와의 채팅")
st.write("주은이를 만나보세요!")

# 2. API 키 세팅 및 OpenAI 클라이언트 준비
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API 키를 찾을 수 없습니다. .streamlit/secrets.toml 파일에 GEMINI_API_KEY를 설정해 주세요.")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 3. 아이돌 '주은이'의 말투 및 페르소나 정의
PRESET_PROMPTS = {
    "백구 주은이": (
        "너는 인기 최정상 아이돌 그룹의 멤버 '주은이'야! 장난기 많고 멍뭉미 넘치는 밝은 성격이야. "
        "팬과 대화하듯이 친근하고 스윗하게 대화해줘. "
        "정답이나 결론을 바로 딱 알려주기보다는 퀴즈를 내듯 살짝 힌트를 주고 '맞혀봐~!' 하고 다정하게 되물어봐줘. "
        "팬이 정답을 맞히면 진심으로 신나하며 칭찬해주고, 과도하게 억지로 귀여운 척하기보다는 유쾌하고 자연스러운 댕댕이 같은 매력을 보여줘."
    ),
    "멋있는 주은이": (
        "너는 팬들에게 무대 위에서도, 밖에서도 든든하고 다정한 최고의 아이돌 '주은이'야. "
        "무슨 질문이든 친절하고 명확하게 알려주고, 따뜻하게 응원과 격려를 건네며 훈훈한 분위기를 만들어줘."
    ),
    "단호한 주은이": (
        "너는 프로페셔널하고 차도녀 매력이 있는 시크한 아이돌 '주은이'야. "
        "쓸데없는 사족 없이 핵심만 딱 깔끔하고 쿨하게 말해주지만, 은근히 팬을 챙겨주는 장난기 섞인 시크함을 유지해줘."
    )
}

# 4. 사이드바 구성
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 4-1. 말투 고르기
    selected_style = st.selectbox(
        "말투 고르기",
        options=list(PRESET_PROMPTS.keys()),
        index=0
    )
    
    # 선택한 말투 프롬프트를 기본값으로 설정하되, 사용자가 수정을 원할 경우 세션 상태 활용
    if "custom_prompt" not in st.session_state or st.session_state.get("last_selected_style") != selected_style:
        st.session_state.custom_prompt = PRESET_PROMPTS[selected_style]
        st.session_state.last_selected_style = selected_style

    # 4-2. 성격 문장 직접 수정하기
    system_instruction = st.text_area(
        "성격 문장 직접 수정",
        value=st.session_state.custom_prompt,
        height=140,
        help="주은이의 성격(시스템 프롬프트)을 원하는 대로 자유롭게 수정할 수 있습니다."
    )

    st.markdown("---")
    
    # 4-3. 대화 지우기 버튼
    if st.button("🗑️ 대화 지우기", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 5. 세션 상태에 대화 기록 저장소 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 6. 이전 대화 목록 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. 사용자 채팅 입력 처리
if user_input := st.chat_input("주은이에게 말을 걸어보세요!"):
    # 사용자 입력 화면 출력 및 저장
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # AI(아이돌 주은이) 응답 스트리밍
    with st.chat_message("assistant"):
        try:
            # 설정된 system_instruction을 항상 맨 위에 포함하여 말투 변경이 즉시 반영되도록 함
            api_messages = [{"role": "system", "content": system_instruction}] + [
                {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
            ]

            stream = client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=api_messages,
                stream=True,
            )

            # 실시간 텍스트 스트리밍 출력
            answer = st.write_stream(stream)
            
            # 주은이의 답변 대화 기록에 저장
            st.session_state.messages.append({"role": "assistant", "content": answer})

        except Exception:
            st.error("응답을 받지 못했습니다. 잠시 후 다시 보내 주세요.")
