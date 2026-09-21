import requests
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# =========================================================
# 🎬 Streamlit 기본 설정
# =========================================================

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)


# =========================================================
# 🎞️ 영화관 분위기의 화면 디자인
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #080808 0%, #171717 100%);
        color: white;
    }

    .main-title {
        font-size: 45px;
        font-weight: 800;
        letter-spacing: -2px;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #aaaaaa;
        font-size: 16px;
        margin-bottom: 30px;
    }

    .movie-card {
        background: #202020;
        border: 1px solid #333333;
        border-radius: 15px;
        padding: 22px;
        margin-bottom: 14px;
    }

    .rank {
        font-size: 36px;
        font-weight: 800;
    }

    .movie-name {
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .info {
        color: #cccccc;
        line-height: 1.9;
        font-size: 15px;
    }

    .date-box {
        background: #111111;
        border: 1px solid #333333;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 25px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 🎬 제목
# =========================================================

st.markdown(
    '<div class="main-title">🎬 YESTERDAY BOX OFFICE</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    '어제 극장에서 가장 많은 관객이 선택한 영화들을 만나보세요.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# 🔐 KOBIS 인증키 가져오기
# =========================================================

# 실제 인증키는 코드에 작성하지 않고
# Streamlit Cloud의 Secrets에서 가져옵니다.
try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]

except Exception:
    st.error(
        "🔐 KOBIS 인증키를 찾을 수 없습니다.\n\n"
        "Streamlit Cloud의 Settings → Secrets에서 "
        "`KOBIS_KEY`가 등록되어 있는지 확인해 주세요."
    )

    st.stop()


# =========================================================
# 🇰🇷 한국 시간 기준으로 '어제' 계산
# =========================================================

# 배포 서버의 시간이 한국 시간이 아니어도
# 한국 시간을 기준으로 날짜를 계산합니다.
KST = ZoneInfo("Asia/Seoul")

today_kst = datetime.now(KST).date()

yesterday_kst = today_kst - timedelta(days=1)

# KOBIS API에서 사용하는 날짜 형식
# 예: 2026년 9월 21일 → 20260921
target_date = yesterday_kst.strftime("%Y%m%d")

# 화면에 보여줄 날짜
display_date = yesterday_kst.strftime("%Y년 %m월 %d일")


# =========================================================
# 📡 KOBIS API 주소
# =========================================================

API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)


# =========================================================
# 🎟️ 박스오피스 데이터 가져오기
# =========================================================

def get_boxoffice():
    """KOBIS에서 어제의 일별 박스오피스 데이터를 가져옵니다."""

    params = {
        "key": KOBIS_KEY,
        "targetDt": target_date
    }

    try:
        # KOBIS API에 요청합니다.
        response = requests.get(
            API_URL,
            params=params,
            timeout=15
        )

        # HTTP 오류가 있으면 예외를 발생시킵니다.
        response.raise_for_status()

        # JSON 형태의 응답을 가져옵니다.
        data = response.json()

    except requests.exceptions.RequestException as e:

        st.error(
            "🚨 KOBIS API에 연결하지 못했습니다.\n\n"
            "다음 내용을 확인해 주세요.\n"
            "• 인터넷 연결 상태\n"
            "• KOBIS API 주소\n"
            "• Streamlit Cloud의 네트워크 상태\n\n"
            f"오류 내용: {e}"
        )

        return None

    except ValueError:

        st.error(
            "🚨 KOBIS에서 정상적인 데이터를 받지 못했습니다.\n\n"
            "잠시 후 다시 실행하거나 KOBIS API 상태를 확인해 주세요."
        )

        return None


    # =====================================================
    # 🔑 인증키 오류 확인
    # =====================================================

    # KOBIS는 인증키가 잘못되어도 HTTP 상태코드가 200일 수 있습니다.
    # 대신 faultInfo가 응답에 들어옵니다.
    if "faultInfo" in data:

        fault_info = data["faultInfo"]

        error_message = fault_info.get(
            "message",
            "인증키 또는 요청 정보를 확인해 주세요."
        )

        st.error(
            "🔑 KOBIS API 인증에 문제가 있습니다.\n\n"
            f"{error_message}\n\n"
            "Streamlit Cloud → Settings → Secrets에서 "
            "`KOBIS_KEY`가 정확하게 등록되어 있는지 확인해 주세요."
        )

        return None


    # =====================================================
    # 📦 정상적인 박스오피스 결과 확인
    # =====================================================

    if "boxOfficeResult" not in data:

        st.error(
            "⚠️ KOBIS 응답에서 박스오피스 결과를 찾을 수 없습니다.\n\n"
            "KOBIS API의 응답 형식이나 서비스 상태를 확인해 주세요."
        )

        return None


    boxoffice_result = data["boxOfficeResult"]

    movies = boxoffice_result.get(
        "dailyBoxOfficeList",
        []
    )


    # =====================================================
    # 🎞️ 영화 목록이 비어 있는 경우
    # =====================================================

    if not movies:

        st.warning(
            f"🎞️ {display_date}의 박스오피스 데이터가 없습니다.\n\n"
            "다음 내용을 확인해 주세요.\n"
            "• 해당 날짜의 박스오피스가 집계되었는지\n"
            "• KOBIS API가 정상적으로 작동하는지\n"
            "• 인증키가 정상적으로 등록되어 있는지"
        )

        return None

    return movies


# =========================================================
# 🚀 데이터 불러오기
# =========================================================

movies = get_boxoffice()


# 데이터를 가져오지 못했다면 여기서 종료합니다.
if movies is None:
    st.stop()


# =========================================================
# 📅 조회 날짜 표시
# =========================================================

st.markdown(
    f"""
    <div class="date-box">
        <div style="color:#888888; font-size:13px;">
            BOX OFFICE DATE
        </div>

        <div style="
            font-size:28px;
            font-weight:700;
            margin-top:5px;
        ">
            {display_date}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 🎬 영화 순위 출력
# =========================================================

for movie in movies:

    # KOBIS에서 받아온 값들은 문자열입니다.
    rank = movie.get("rank", "-")
    movie_name = movie.get("movieNm", "영화 제목 없음")
    open_date = movie.get("openDt", "-")

    audi_cnt = movie.get("audiCnt", "0")
    audi_acc = movie.get("audiAcc", "0")
    screen_cnt = movie.get("scrnCnt", "0")

    rank_inten = movie.get("rankInten", "0")
    rank_old_new = movie.get("rankOldAndNew", "")


    # =====================================================
    # 🔢 숫자에 쉼표 넣기
    # =====================================================

    try:
        audi_cnt_text = f"{int(audi_cnt):,}명"
    except:
        audi_cnt_text = f"{audi_cnt}명"

    try:
        audi_acc_text = f"{int(audi_acc):,}명"
    except:
        audi_acc_text = f"{audi_acc}명"

    try:
        screen_cnt_text = f"{int(screen_cnt):,}개"
    except:
        screen_cnt_text = f"{screen_cnt}개"


    # =====================================================
    # 📅 개봉일 보기 좋게 변경
    # =====================================================

    if open_date and len(open_date) == 8:

        open_date_text = (
            f"{open_date[:4]}."
            f"{open_date[4:6]}."
            f"{open_date[6:]}"
        )

    else:
        open_date_text = "정보 없음"


    # =====================================================
    # 📈 전날 대비 순위 변화
    # =====================================================

    if rank_old_new == "NEW":

        rank_change = "🆕 NEW"

    elif rank_inten == "0":

        rank_change = "━ 유지"

    else:

        try:

            change = int(rank_inten)

            if change > 0:
                rank_change = f"▲ {change}"

            else:
                rank_change = f"▼ {abs(change)}"

        except:

            rank_change = "━"


    # =====================================================
    # 🎞️ 영화 카드
    # =====================================================

    st.markdown(
        '<div class="movie-card">',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 6])


    # -----------------------------------------------------
    # 순위
    # -----------------------------------------------------

    with col1:

        st.markdown(
            f"""
            <div class="rank">
                #{rank}
            </div>

            <div style="
                color:#aaaaaa;
                margin-top:5px;
            ">
                {rank_change}
            </div>
            """,
            unsafe_allow_html=True
        )


    # -----------------------------------------------------
    # 영화 정보
    # -----------------------------------------------------

    with col2:

        st.markdown(
            f"""
            <div class="movie-name">
                {movie_name}
            </div>

            <div class="info">
                🎬 개봉일　{open_date_text}<br>
                👥 일일 관객　{audi_cnt_text}<br>
                🎟️ 누적 관객　{audi_acc_text}<br>
                🖥️ 스크린 수　{screen_cnt_text}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# =========================================================
# 📌 하단 안내
# =========================================================

st.divider()

st.caption(
    "🎬 데이터 출처: 영화관입장권통합전산망(KOBIS) "
    "일별 박스오피스 API"
)

st.caption(
    "🇰🇷 조회 날짜는 한국 시간(Asia/Seoul)을 기준으로 "
    "자동으로 '어제'를 계산합니다."
)
