import requests
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# =========================================================
# 🎬 기본 설정
# =========================================================

st.set_page_config(
    page_title="Daily Box Office",
    page_icon="🎬",
    layout="wide"
)


# =========================================================
# 🎞️ 영화관 느낌의 배경
# 검은색 + 빨간색
# =========================================================

st.markdown(
    """
    <style>
    /* 전체 배경 */
    .stApp {
        background:
            radial-gradient(
                circle at top center,
                #4a0000 0%,
                #1a0000 25%,
                #0d0d0d 60%,
                #080808 100%
            );
        color: white;
    }

    /* 메인 화면 위쪽에 은은한 빨간 빛 */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 5px;
        background: #d00000;
        z-index: 999;
    }

    /* 제목 */
    h1, h2, h3 {
        color: white !important;
    }

    /* 일반 글씨 */
    p, label {
        color: #eeeeee;
    }

    /* 영화 카드 테두리 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: rgba(30, 30, 30, 0.92);
        border-color: #4a2020;
        border-radius: 14px;
    }

    /* Metric */
    div[data-testid="stMetric"] {
        background-color: #252020;
        border: 1px solid #4a3030;
        border-radius: 10px;
    }

    div[data-testid="stMetricLabel"] {
        color: #bbbbbb !important;
    }

    div[data-testid="stMetricValue"] {
        color: white !important;
    }

    /* 날짜 선택창 */
    div[data-testid="stDateInput"] {
        background-color: #1b1717;
        border-radius: 10px;
    }

    /* 구분선 */
    hr {
        border-color: #552020;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 🎬 제목
# =========================================================

st.title("🎬 DAILY BOX OFFICE")

st.caption(
    "원하는 날짜를 선택해서 그날의 박스오피스를 확인해보세요."
)


# =========================================================
# 🔐 KOBIS 인증키
# =========================================================

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]

except Exception:
    st.error(
        "🔐 KOBIS 인증키를 찾을 수 없습니다.\n\n"
        "Streamlit Cloud → Settings → Secrets에서 "
        "`KOBIS_KEY`가 등록되어 있는지 확인해주세요."
    )
    st.stop()


# =========================================================
# 🇰🇷 한국 시간
# =========================================================

KST = ZoneInfo("Asia/Seoul")

today = datetime.now(KST).date()

# 오늘은 아직 집계 전이므로 어제까지만 선택 가능
yesterday = today - timedelta(days=1)


# =========================================================
# 📅 날짜 선택
# =========================================================

st.subheader("📅 조회 날짜")

selected_date = st.date_input(
    "박스오피스를 확인할 날짜를 선택하세요.",
    value=yesterday,
    min_value=datetime(2004, 1, 1).date(),
    max_value=yesterday,
    format="YYYY-MM-DD"
)


# =========================================================
# 📅 KOBIS 날짜 형식
# =========================================================

target_date = selected_date.strftime("%Y%m%d")

display_date = selected_date.strftime(
    "%Y년 %m월 %d일"
)


# =========================================================
# 📡 KOBIS API
# =========================================================

API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)


# =========================================================
# 🎟️ 박스오피스 데이터 가져오기
# =========================================================

def get_boxoffice(target_dt):

    params = {
        "key": KOBIS_KEY,
        "targetDt": target_dt
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as e:

        st.error(
            "🚨 KOBIS API에 연결하지 못했습니다.\n\n"
            "다음 내용을 확인해주세요.\n"
            "• 인터넷 연결 상태\n"
            "• KOBIS API 주소\n"
            "• Streamlit Cloud의 네트워크 상태\n\n"
            f"오류 내용: {e}"
        )

        return None

    except ValueError:

        st.error(
            "🚨 KOBIS에서 정상적인 데이터를 받지 못했습니다.\n\n"
            "잠시 후 다시 실행해주세요."
        )

        return None


    # -----------------------------------------------------
    # 🔑 인증키 오류
    # -----------------------------------------------------

    if "faultInfo" in data:

        fault_info = data["faultInfo"]

        error_message = fault_info.get(
            "message",
            "KOBIS 인증키를 확인해주세요."
        )

        st.error(
            "🔑 KOBIS 인증키에 문제가 있습니다.\n\n"
            f"{error_message}\n\n"
            "Streamlit Cloud → Settings → Secrets에서 "
            "`KOBIS_KEY`가 정확하게 등록되어 있는지 확인해주세요."
        )

        return None


    # -----------------------------------------------------
    # 📦 결과 확인
    # -----------------------------------------------------

    if "boxOfficeResult" not in data:

        st.error(
            "⚠️ KOBIS에서 박스오피스 결과를 받지 못했습니다.\n\n"
            "KOBIS API의 응답을 확인해주세요."
        )

        return None


    movies = data["boxOfficeResult"].get(
        "dailyBoxOfficeList",
        []
    )


    # -----------------------------------------------------
    # 🎞️ 영화 목록이 없는 경우
    # -----------------------------------------------------

    if not movies:

        st.warning(
            "🎞️ 그날은 아직 집계 전입니다."
        )

        st.info(
            "선택한 날짜의 박스오피스 데이터가 아직 없거나 "
            "KOBIS에서 제공되지 않는 날짜일 수 있습니다."
        )

        return None


    return movies


# =========================================================
# 🚀 데이터 불러오기
# =========================================================

movies = get_boxoffice(target_date)

if movies is None:
    st.stop()


# =========================================================
# 📅 날짜 표시
# =========================================================

st.divider()

st.subheader(
    f"🎞️ {display_date} 박스오피스"
)

st.caption(
    f"총 {len(movies)}편의 영화"
)


# =========================================================
# 🎬 영화 목록
# =========================================================

for movie in movies:

    # -----------------------------------------------------
    # 기본 정보
    # -----------------------------------------------------

    rank = movie.get("rank", "-")

    movie_name = movie.get(
        "movieNm",
        "영화 제목 정보 없음"
    )

    open_date = movie.get(
        "openDt",
        ""
    )

    audi_cnt = movie.get(
        "audiCnt",
        "0"
    )

    audi_acc = movie.get(
        "audiAcc",
        "0"
    )

    screen_cnt = movie.get(
        "scrnCnt",
        "0"
    )

    rank_inten = movie.get(
        "rankInten",
        "0"
    )

    rank_old_new = movie.get(
        "rankOldAndNew",
        ""
    )


    # -----------------------------------------------------
    # 숫자 변환
    # -----------------------------------------------------

    try:
        audi_cnt_number = int(audi_cnt)
    except:
        audi_cnt_number = 0

    try:
        audi_acc_number = int(audi_acc)
    except:
        audi_acc_number = 0

    try:
        screen_cnt_number = int(screen_cnt)
    except:
        screen_cnt_number = 0

    try:
        rank_change_number = int(rank_inten)
    except:
        rank_change_number = 0


    audi_cnt_text = f"{audi_cnt_number:,}명"

    audi_acc_text = f"{audi_acc_number:,}명"

    screen_cnt_text = f"{screen_cnt_number:,}개"


    # -----------------------------------------------------
    # 📅 개봉일
    # -----------------------------------------------------

    if open_date:

        if "-" in open_date:

            open_date_text = open_date

        elif len(open_date) == 8:

            open_date_text = (
                f"{open_date[:4]}-"
                f"{open_date[4:6]}-"
                f"{open_date[6:]}"
            )

        else:

            open_date_text = open_date

    else:

        open_date_text = "정보 없음"


    # -----------------------------------------------------
    # 🏆 100만 관객
    # -----------------------------------------------------

    if audi_acc_number >= 1_000_000:

        movie_title = f"{movie_name} 🏆"

    else:

        movie_title = movie_name


    # -----------------------------------------------------
    # 📈 순위 변화
    # -----------------------------------------------------

    if rank_old_new == "NEW":

        rank_change = "🆕 NEW"

    elif rank_change_number > 0:

        # 양수 = 순위 상승
        rank_change = f"🔴 ▲ {rank_change_number}"

    elif rank_change_number < 0:

        # 음수 = 순위 하락
        rank_change = f"🔵 ▼ {abs(rank_change_number)}"

    else:

        rank_change = "━ 유지"


    # =====================================================
    # 🎬 영화 카드
    # =====================================================

    with st.container(border=True):

        col1, col2, col3 = st.columns(
            [1, 5, 2]
        )


        # -------------------------------------------------
        # 순위
        # -------------------------------------------------

        with col1:

            st.subheader(
                f"#{rank}"
            )

            st.write(
                rank_change
            )


        # -------------------------------------------------
        # 영화 정보
        # -------------------------------------------------

        with col2:

            st.subheader(
                movie_title
            )

            st.write(
                f"🎬 **개봉일:** {open_date_text}"
            )

            st.write(
                f"👥 **일일 관객:** {audi_cnt_text}"
            )

            st.write(
                f"🎟️ **누적 관객:** {audi_acc_text}"
            )

            st.write(
                f"🖥️ **스크린 수:** {screen_cnt_text}"
            )


        # -------------------------------------------------
        # 핵심 수치
        # -------------------------------------------------

        with col3:

            st.metric(
                "누적 관객",
                audi_acc_text
            )

            st.metric(
                "스크린",
                screen_cnt_text
            )


# =========================================================
# 📌 출처
# =========================================================

st.divider()

st.caption(
    "🎬 데이터 출처: 영화관입장권통합전산망(KOBIS) "
    "일별 박스오피스 API"
)

st.caption(
    "※ 오늘 날짜는 아직 박스오피스 집계 전이므로 선택할 수 없습니다."
)
