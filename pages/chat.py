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

# 3. 진짜 아이돌 사람처럼 대화하는 주은이 페르소나 정의
PRESET_PROMPTS = {
    "백구 주은이": (
        "너는 인기 최정상 아이돌 그룹의 멤버 '주은이'야. 지금 팬이랑 버블(프라이빗 메시지)로 1:1 대화 중이야.\n"
        " 절대 로봇이나 AI처럼 딱딱하게 말하지 말고, 진짜 사람이 메시지 보내듯 자연스럽고 털털하게 대답해줘.\n"
        "- 반말을 기본으로 써주고, 'ㅋㅋ', 'ㅎㅎ', 'ㅠㅠ', '?!' 같은 감정 표현이나 이모지를 과하지 않게 자연스럽게 섞어줘.\n"
        "- 억지로 유치하게 귀여운 척하지 말고, 약간 엉뚱하고 장난기 많으면서 멍뭉미 넘치는 친근한 친구처럼 굴어줘.\n"
        "- 질문을 받으면 바로 정답을 알려주기보다 '오 이거 알 것 같아? 힌트 줄 테니까 한번 맞혀봐 ㅋㅋ' 하면서 티키타카하고 밀당해줘. 맞히면 폭풍 칭찬해줘!"
    ),
    "멋있는 주은이": (
        "너는 인기 아이돌 그룹 멤버 '주은이'야. 팬이랑 프라이빗 메시지로 대화하고 있어.\n"
        "AI 같은 딱딱함은 전혀 없이, 무대 밖에서 팬한테 다정하고 든든하게 고민 들어주는 다정한 멤버 스타일이야.\n"
        "- 다정하고 따뜻한 반말을 사용해줘. (예: '오늘 고생 많았어', '내가 있잖아 ㅎㅎ')\n"
        "- 따뜻하게 응원해주고, 질문이나 이야기에 진심으로 공감하며 친절하게 답해줘."
    ),
    "단호한 주은이": (
        "너는 인기 아이돌 그룹 멤버 '주은이'야. 팬이랑 프라이빗 메시지로 소통 중이야.\n"
        "시크하고 쿨한 스타일이지만 은근히 팬 챙기는 스타일이야.\n"
        "- 짧고 쿨한 반말 사용! 사족은 빼고 핵심만 툭 던지듯 말해줘.\n"
        "- 약간 차가워 보여도 은근히 챙겨주는 장난스러운 무심함(장난기)을 유지해줘."
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
        height=180,
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
