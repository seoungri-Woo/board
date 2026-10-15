import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인 (따뜻한 톤 연출)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# 따뜻하고 편안한 분위기의 배경 및 글꼴 스타일 적용
st.markdown("""
    <style>
    .stApp {
        background-color: #FAF7F2;
    }
    .main-title {
        color: #4A3E3D;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
    }
    .sub-title {
        color: #7D6B68;
        text-align: center;
        font-size: 1.05rem;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 (캐싱을 이용해 데이터 로딩 속도 최적화)
# -----------------------------------------------------------------------------
@st.cache_data
def load_population_data():
    # pandas는 zip 압축 파일의 URL도 바로 읽을 수 있습니다.
    url = "https://raw.githubusercontent.com/seoungri-Woo/board/main/population_ts_yearly_gender.zip"
    df = pd.read_csv(url)
    return df

# 로딩 중 메시지
with st.spinner("지역별 인구 데이터를 불러오는 중입니다... ☕"):
    data = load_population_data()

# 데이터셋에서 가장 최신 연도 자동 추출 및 필터링
latest_year = data['연도'].max()
df_latest = data[data['연도'] == latest_year].copy()

# -----------------------------------------------------------------------------
# 3. 앱 타이틀 및 헤더 영역
# -----------------------------------------------------------------------------
st.markdown(f"<h1 class='main-title'>🏘️ 우리 동네 인구 피라미드 ({latest_year}년)</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>원하시는 시·도, 시·군·구, 읍·면·동을 선택하여 연령별 인구 분포를 확인해보세요.</p>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. 단계별 지역 선택 드롭다운 (시도 ➡️ 시군구 ➡️ 동)
# -----------------------------------------------------------------------------
st.subheader("📍 지역 선택")
col1, col2, col3 = st.columns(3)

with col1:
    sido_list = sorted(df_latest['시도'].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

# 선택한 시·도에 속한 시·군·구목록 추출
sigungu_filtered = df_latest[df_latest['시도'] == selected_sido]
with col2:
    sigungu_list = sorted(sigungu_filtered['시군구'].dropna().unique())
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

# 선택한 시·군·구에 속한 읍·면·동 목록 추출
dong_filtered = sigungu_filtered[sigungu_filtered['시군구'] == selected_sigungu]
with col3:
    dong_list = sorted(dong_filtered['동'].dropna().unique())
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)

# 최종 선택된 읍·면·동 데이터 1행 추출
target_df = dong_filtered[dong_filtered['동'] == selected_dong]

# -----------------------------------------------------------------------------
# 5. 인구 피라미드 그래프 그리기
# -----------------------------------------------------------------------------
if not target_df.empty:
    target_row = target_df.iloc[0]

    # 0세부터 100세 이상까지의 연령 라벨 배열 생성 (아래에서 위로 올라가는 순서)
    age_list = [f"{i}세" for i in range(100)] + ["100세 이상"]

    # 데이터 프레임 컬럼 이름에 맞게 리스트 생성
    male_cols = [f"남_{age}" for age in age_list]
    female_cols = [f"여_{age}" for age in age_list]

    # 각 나이별 남성/여성 인구수 추출
    male_pop_abs = [int(target_row[col]) if col in target_row and pd.notna(target_row[col]) else 0 for col in male_cols]
    female_pop = [int(target_row[col]) if col in target_row and pd.notna(target_row[col]) else 0 for col in female_cols]

    # 남성 인구수는 피라미드 왼쪽에 배치해야 하므로 음수로 변환
    male_pop_neg = [-val for val in male_pop_abs]

    # 상단 요약지표 (총 인구, 남성, 여성)
    total_male = sum(male_pop_abs)
    total_female = sum(female_pop)
    total_pop = total_male + total_female

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("총 인구수", f"{total_pop:,} 명")
    m2.metric("남성 인구수", f"{total_male:,} 명")
    m3.metric("여성 인구수", f"{total_female:,} 명")

    # Plotly 시각화 객체 생성
    fig = go.Figure()

    # 남성 인구 막대 (왼쪽: 음수 값, 따뜻한 올리브/그린 톤)
    fig.add_trace(go.Bar(
        y=age_list,
        x=male_pop_neg,
        name='남성',
        orientation='h',
        marker=dict(color='#3D5A80'), # 따뜻한 딥 블루 톤
        customdata=male_pop_abs,       # 마우스 호버 시 양수로 보여주기 위한 데이터
        hovertemplate='<b>%{y} 남성</b>: %{customdata:,}명<extra></extra>'
    ))

    # 여성 인구 막대 (오른쪽: 양수 값, 따뜻한 코랄/테라코타 톤)
    fig.add_trace(go.Bar(
        y=age_list,
        x=female_pop,
        name='여성',
        orientation='h',
        marker=dict(color='#E07A5F'), # 따뜻한 테라코타 코랄 톤
        customdata=female_pop,
        hovertemplate='<b>%{y} 여성</b>: %{customdata:,}명<extra></extra>'
    ))

    # X축 범위를 대칭으로 만들기 위해 최대 인구값 계산
    max_val = max(max(male_pop_abs, default=0), max(female_pop, default=0))
    x_limit = int(max_val * 1.1) if max_val > 0 else 10

    # X축 왼쪽 음수 눈금을 양수로 표기하기 위한 설정
    step = max(1, x_limit // 4)
    tick_vals = list(range(-step * 4, step * 5, step))
    tick_texts = [f"{abs(v):,}" for v in tick_vals]

    # Layout 및 축 설정
    fig.update_layout(
        title=dict(
            text=f"<b>{selected_sido} {selected_sigungu} {selected_dong} 인구 피라미드</b>",
            font=dict(size=18, color='#4A3E3D'),
            x=0.5,
            xanchor='center'
        ),
        barmode='relative',
        bargap=0.05,
        paper_bgcolor='#FAF7F2',
        plot_bgcolor='#FFFFFF',
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif", color='#4A3E3D'),
        xaxis=dict(
            title="인구수 (명)",
            range=[-x_limit, x_limit],
            tickmode='array',
            tickvals=tick_vals,
            ticktext=tick_texts,
            gridcolor='#F0EAE1',
            zerolinecolor='#8D7B68',
            zerolinewidth=1.5
        ),
        # y축 순서 엄격 고정: 0세가 맨 아래, 100세 이상이 맨 위 (자동 정렬 및 축 반전 미사용)
        yaxis=dict(
            title="연령",
            type='category',
            categoryorder='array',
            categoryarray=age_list,
            gridcolor='#F0EAE1'
        ),
        legend=dict(
            x=0.82,
            y=1.03,
            orientation='h',
            bgcolor='rgba(255, 255, 255, 0.7)'
        ),
        height=850,
        margin=dict(l=60, r=60, t=80, b=60)
    )

    # 스트림릿 화면에 그래프 출력
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("선택하신 지역의 데이터가 존재하지 않습니다.")
