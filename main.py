import requests
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# =========================================================
# 🎬 기본 설정
# =========================================================

st.set_page_config(
    page_title="박스오피스",
    page_icon="🎬",
    layout="wide"
)


# =========================================================
# 🎞️ 영화관 느낌의 화면 디자인
# 검정 + 빨강 + 흰색 테마
# =========================================================

st.markdown(
    """
    <style>

    /* 전체 배경 */
    .stApp {
        background-color: #0f0f0f;
        color: #ffffff;
    }

    /* 상단 제목 */
    h1 {
        color: #ffffff !important;
        font-weight: 800 !important;
        letter-spacing: -2px;
    }

    /* 소제목 */
    h2, h3 {
        color: #ffffff !important;
    }

    /* 일반 글씨 */
    p, label {
        color: #eeeeee;
    }

    /* 날짜 선택 영역 */
    div[data-testid="stDateInput"] {
        background-color: #1c1c1c;
        border-radius: 12px;
        padding: 8px;
        border: 1px solid #3a3a3a;
    }

    /* 영화 카드 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1c1c1c;
        border: 1px solid #3d3d3d;
        border-radius: 14px;
    }

    /* 카드 안쪽 글씨 */
    div[data-testid="stVerticalBlockBorderWrapper"] p {
        color: #eeeeee;
    }

    /* Streamlit metric */
    div[data-testid="stMetric"] {
        background-color: #262626;
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #3d3d3d;
    }

    div[data-testid="stMetricLabel"] {
        color: #bbbbbb !important;
    }

    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
    }

    /* 버튼 */
    .stButton > button {
        background-color: #b00020;
        color: white;
        border: none;
        border-radius: 8px;
    }

    /* 선택된 날짜 */
    input {
        color: #ffffff !important;
    }

    /* 구분선 */
    hr {
        border-color: #3a3a3a;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 🎬 제목
# =========================================================

st.title("🎬 DAILY BOX OFFICE")

st.markdown(
    """
    <div style="
        color:#bbbbbb;
        font-size:16px;
        margin-top:-10px;
        margin-bottom:25px;
    ">
        원하는 날짜를 선택해서 그날의 박스오피스를 확인해보세요.
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 🔐 KOBIS 인증키 가져오기
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
# 🇰🇷 한국 시간 계산
# =========================================================

# 서버 시간이 한국 시간이 아니어도
# 항상 한국 시간을 기준으로 계산합니다.
KST = ZoneInfo("Asia/Seoul")

today = datetime.now(KST).date()

# 오늘은 아직 집계 전이므로 선택할 수 없습니다.
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
# 📅 KOBIS 날짜 형식으로 변경
# =========================================================

target_date = selected_date.strftime("%Y%m%d")

display_date = selected_date.strftime(
    "%Y년 %m월 %d일"
)


# =========================================================
# 📡 KOBIS API 주소
# =========================================================

API_URL = (
    "https://www.kobis.or.kr/"
    "kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)


# =========================================================
# 🎟️ 박스오피스 가져오기
# =========================================================

def get_boxoffice(target_dt):
    """선택한 날짜의 KOBIS 박스오피스를 가져옵니다."""

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


    # =====================================================
    # 🔑 인증키 오류 확인
    # =====================================================

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


    # =====================================================
    # 📦 박스오피스 결과 확인
    # =====================================================

    if "boxOfficeResult" not in data:

        st.error(
            "⚠️ KOBIS에서 박스오피스 결과를 받지 못했습니다.\n\n"
            "KOBIS API의 응답을 확인해주세요."
        )

        return None


    result = data["boxOfficeResult"]

    movies = result.get(
        "dailyBoxOfficeList",
        []
    )


    # =====================================================
    # 🎞️ 영화 목록이 없는 경우
    # =====================================================

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
# 📅 날짜 제목
# =========================================================

st.divider()

st.markdown(
    f"""
    <div style="
        background:linear-gradient(
            90deg,
            #4a0000 0%,
            #260000 45%,
            #1c1c1c 100%
        );
        border-left:5px solid #e50914;
        border-radius:10px;
        padding:18px 22px;
        margin:15px 0 20px 0;
    ">

        <div style="
            color:#ff7777;
            font-size:13px;
            font-weight:700;
            letter-spacing:1px;
        ">
            BOX OFFICE
        </div>

        <div style="
            color:#ffffff;
            font-size:28px;
            font-weight:800;
            margin-top:4px;
        ">
            {display_date}
        </div>

        <div style="
            color:#bbbbbb;
            font-size:14px;
            margin-top:5px;
        ">
            총 {len(movies)}편의 영화
        </div>

    </div>
    """,
    unsafe_allow_html=True
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


    # =====================================================
    # 🔢 숫자 변환
    # =====================================================

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


    # =====================================================
    # 📅 개봉일 처리
    # =====================================================

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


    # =====================================================
    # 🏆 100만 관객
    # =====================================================

    if audi_acc_number >= 1_000_000:

        trophy = " 🏆"

    else:

        trophy = ""


    # =====================================================
    # 📈 순위 변화
    # =====================================================

    if rank_old_new == "NEW":

        rank_change_html = (
            '<span style="'
            'color:#ff5252;'
            'font-weight:700;'
            '">🆕 NEW</span>'
        )

    elif rank_change_number > 0:

        # 양수 = 순위 상승
        rank_change_html = (
            '<span style="'
            'color:#ff4d4d;'
            'font-weight:800;'
            'font-size:17px;'
            '">▲ '
            f'{rank_change_number}'
            '</span>'
        )

    elif rank_change_number < 0:

        # 음수 = 순위 하락
        rank_change_html = (
            '<span style="'
            'color:#70a7ff;'
            'font-weight:800;'
            'font-size:17px;'
            '">▼ '
            f'{abs(rank_change_number)}'
            '</span>'
        )

    else:

        rank_change_html = (
            '<span style="'
            'color:#999999;'
            '">━ 유지</span>'
        )


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

            st.markdown(
                f"""
                <div style="
                    text-align:center;
                    padding-top:5px;
                ">

                    <div style="
                        color:#e50914;
                        font-size:32px;
                        font-weight:900;
                    ">
                        #{rank}
                    </div>

                    <div style="
                        margin-top:8px;
                    ">
                        {rank_change_html}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )


        # -------------------------------------------------
        # 영화 정보
        # -------------------------------------------------

        with col2:

            st.markdown(
                f"""
                <div style="
                    color:#ffffff;
                    font-size:23px;
                    font-weight:800;
                    margin-bottom:12px;
                ">
                    {movie_name}{trophy}
                </div>

                <div style="
                    color:#dddddd;
                    line-height:2;
                    font-size:15px;
                ">

                    🎬 <b>개봉일</b>　
                    {open_date_text}
                    <br>

                    👥 <b>일일 관객</b>　
                    {audi_cnt_text}
                    <br>

                    🎟️ <b>누적 관객</b>　
                    {audi_acc_text}
                    <br>

                    🖥️ <b>스크린 수</b>　
                    {screen_cnt_text}

                </div>
                """,
                unsafe_allow_html=True
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
# 📌 하단 출처
# =========================================================

st.divider()

st.caption(
    "🎬 데이터 출처: 영화관입장권통합전산망(KOBIS) "
    "일별 박스오피스 API"
)

st.caption(
    "※ 오늘 날짜는 아직 박스오피스 집계 전이므로 선택할 수 없습니다."
)
