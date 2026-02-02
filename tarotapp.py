import streamlit as st
import random
import base64
import time
import io
import os
import uuid
from PIL import Image
import google.generativeai as genai

# --- 데이터 로드 ---
try:
    from tarot_images import tarot_images
    HAS_IMAGES = True
except ImportError:
    HAS_IMAGES = False
    tarot_images = {}

# --- 페이지 설정 ---
st.set_page_config(
    page_title="Cyberpunk Tarot Web",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS 커스텀 ---
st.markdown("""
    <style>
    /* 1. 기본 레이아웃 */
    .block-container { padding-top: 3rem !important; padding-bottom: 2rem !important; max-width: 95% !important; }
    header { visibility: visible !important; background-color: transparent !important; }
    footer { visibility: hidden; }
    .stApp { background-color: #0e0e0e; color: #E0F7FA; }
    
    /* 2. 로그 및 텍스트 */
    .system-msg { color: #39FF14; font-size: 0.8em; margin-bottom: 5px; text-align: left; text-shadow: 0 0 5px rgba(57, 255, 20, 0.6); }
    .ai-msg { color: #E0F7FA; border-left: 3px solid #D500F9; padding-left: 10px; margin: 10px 0; background-color: #1a1a1a; padding: 10px; border-radius: 5px; text-align: left; }
    .user-msg { color: #00E5FF; font-weight: bold; margin-top: 5px; text-align: left; }
    div[data-testid="stMarkdownContainer"] p { text-align: left; }
    
    /* 3. 입력창 & 버튼 */
    .stTextInput > div > div > input { background-color: #1a1a1a; color: #00E5FF; border: 1px solid #D500F9; font-family: 'Consolas'; }
    div.stButton > button { background-color: #333; color: #00E5FF; border: 1px solid #00E5FF; transition: 0.1s; }
    div.stButton > button:hover { background-color: #00E5FF; color: #000; }
    
    /* 사이드바 */
    [data-testid="stSidebar"] { background-color: #111; border-right: 1px solid #333; }
    [data-testid="stSidebar"] button[kind="header"] svg { fill: #00E5FF !important; }
    [data-testid="collapsedControl"] svg { fill: #00E5FF !important; }
    
    /* 4. 카드 래퍼 */
    .card-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
    }
    
    /* 라벨 */
    .pos-label { 
        text-align: center !important; 
        color: #D500F9; font-family: 'Impact', sans-serif; 
        font-size: 0.9em; margin-bottom: 5px; 
        text-shadow: 0 0 5px #D500F9; 
        width: 100%; display: block;
        height: 20px;
    }
    
    /* 하단 컨트롤 영역 (높이 고정 -> 점프 방지) */
    .control-area {
        height: 65px; 
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center; 
        margin-top: 5px;
    }
    
    /* 카드 이름 박스 */
    .card-name-box {
        font-family: 'NanumGothic'; 
        font-size: 11px; 
        color: #00E5FF; 
        text-align: center;
        line-height: 1.2;
        margin-bottom: 2px;
    }

    /* 상태 배지 */
    .status-badge {
        display: inline-block;
        padding: 1px 6px;
        border: 1px solid #00E5FF;
        background-color: rgba(0, 229, 255, 0.05);
        color: #00E5FF;
        font-size: 10px;
        font-weight: bold;
        border-radius: 3px;
    }
    .status-badge.rev {
        border-color: #FF5252;
        background-color: rgba(255, 82, 82, 0.05);
        color: #FF5252;
    }
    
    /* 카드 이미지 */
    img.card-img {
        display: block !important;
        margin-left: auto !important;
        margin-right: auto !important;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
    }
    
    div.stButton > button p { font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 타로 데이터 ---
TAROT_DATA = [
    {"name": "The Fool (바보)", "image_key": "Fool", "keywords_up": ["새로운 시작", "순수함", "자유"], "keywords_rev": ["무모함", "어리석음", "위험"], "meaning_up": "두려움 없는 새로운 여정의 시작.", "meaning_rev": "준비되지 않은 시작은 위험할 수 있습니다."},
    {"name": "The Magician (마법사)", "image_key": "Magician", "keywords_up": ["창조", "숙련됨", "의지"], "keywords_rev": ["속임수", "재능 낭비"], "meaning_up": "당신은 필요한 모든 도구를 가지고 있습니다.", "meaning_rev": "능력을 잘못된 곳에 쓰고 있습니다."},
    {"name": "The High Priestess (여사제)", "image_key": "High Priestess", "keywords_up": ["직관", "무의식", "신비"], "keywords_rev": ["비밀", "내면 무시"], "meaning_up": "직관을 따르세요. 답은 안에 있습니다.", "meaning_rev": "내면의 소리를 무시하지 마세요."},
    {"name": "The Empress (여황제)", "image_key": "Empress", "keywords_up": ["풍요", "모성", "창조성"], "keywords_rev": ["의존", "창조력 고갈"], "meaning_up": "풍요로움과 창조성이 넘치는 시기입니다.", "meaning_rev": "자신을 돌보는 데 소홀하지 마세요."},
    {"name": "The Emperor (황제)", "image_key": "Emperor", "keywords_up": ["권위", "구조", "통제"], "keywords_rev": ["지배", "고집", "규율 부족"], "meaning_up": "질서와 리더십이 필요한 때입니다.", "meaning_rev": "너무 강압적이거나 통제력을 잃지 마세요."},
    {"name": "The Hierophant (교황)", "image_key": "Hierophant", "keywords_up": ["전통", "신념", "가르침"], "keywords_rev": ["반항", "부적응"], "meaning_up": "전통적인 방식이나 조언을 따르세요.", "meaning_rev": "자신만의 신념을 찾아야 할 때입니다."},
    {"name": "The Lovers (연인)", "image_key": "Lovers", "keywords_up": ["사랑", "조화", "선택"], "keywords_rev": ["불화", "불균형"], "meaning_up": "중요한 선택의 기로에 서 있습니다.", "meaning_rev": "관계의 갈등이나 후회가 있을 수 있습니다."},
    {"name": "The Chariot (전차)", "image_key": "Chariot", "keywords_up": ["승리", "의지", "행동"], "keywords_rev": ["패배", "통제 상실"], "meaning_up": "목표를 향해 거침없이 나아가세요.", "meaning_rev": "방향을 잃거나 너무 서두르지 마세요."},
    {"name": "Strength (힘)", "image_key": "Strength", "keywords_up": ["용기", "인내", "내면의 힘"], "keywords_rev": ["나약함", "폭발"], "meaning_up": "부드러움이 강함을 이깁니다.", "meaning_rev": "자신감을 잃지 마세요."},
    {"name": "The Hermit (은둔자)", "image_key": "Hermit", "keywords_up": ["성찰", "고독", "탐구"], "keywords_rev": ["고립", "외로움"], "meaning_up": "잠시 멈추고 내면을 들여다볼 시간입니다.", "meaning_rev": "세상과의 소통을 끊지 마세요."},
    {"name": "Wheel of Fortune (운명)", "image_key": "Wheel of Fortune", "keywords_up": ["변화", "운명", "행운"], "keywords_rev": ["불운", "저항"], "meaning_up": "운명이 당신 편입니다. 변화를 받아들이세요.", "meaning_rev": "피할 수 없는 변화가 오고 있습니다."},
    {"name": "Justice (정의)", "image_key": "Justice", "keywords_up": ["정의", "공정", "진실"], "keywords_rev": ["불공정", "편견"], "meaning_up": "행동에는 결과가 따릅니다. 공정하세요.", "meaning_rev": "자신에게 솔직해져야 할 때입니다."},
    {"name": "The Hanged Man (매달린 자)", "image_key": "Hanged Man", "keywords_up": ["희생", "새로운 관점"], "keywords_rev": ["무의미한 희생", "정체"], "meaning_up": "다른 관점에서 상황을 바라보세요.", "meaning_rev": "너무 오래 망설이고 있지는 않나요?"},
    {"name": "Death (죽음)", "image_key": "Death", "keywords_up": ["끝", "새로운 시작", "변형"], "keywords_rev": ["저항", "정체", "두려움"], "meaning_up": "과거를 놓아주면 새로운 문이 열립니다.", "meaning_rev": "변화를 두려워하지 말고 받아들이세요."},
    {"name": "Temperance (절제)", "image_key": "Temperance", "keywords_up": ["균형", "중용", "조화"], "keywords_rev": ["불균형", "과도함"], "meaning_up": "극단을 피하고 균형을 찾으세요.", "meaning_rev": "삶의 균형이 깨져 있습니다."},
    {"name": "The Devil (악마)", "image_key": "Devil", "keywords_up": ["속박", "중독", "유혹"], "keywords_rev": ["해방", "자유"], "meaning_up": "자신을 옭아매는 것으로부터 벗어나세요.", "meaning_rev": "어두운 사슬을 끊을 기회입니다."},
    {"name": "The Tower (탑)", "image_key": "Tower", "keywords_up": ["갑작스런 변화", "붕괴"], "keywords_rev": ["재난 모면", "두려움"], "meaning_up": "기초가 무너지고 있습니다. 다시 세우세요.", "meaning_rev": "변화를 거부하면 고통만 길어집니다."},
    {"name": "The Star (별)", "image_key": "Star", "keywords_up": ["희망", "영감", "평온"], "keywords_rev": ["절망", "믿음 부족"], "meaning_up": "어둠 끝에 빛이 보입니다.", "meaning_rev": "긍정적인 마음을 잃지 마세요."},
    {"name": "The Moon (달)", "image_key": "Moon", "keywords_up": ["환상", "불안", "모호함"], "keywords_rev": ["진실 드러남", "평정"], "meaning_up": "보이는 것이 전부가 아닙니다.", "meaning_rev": "안개가 걷히고 진실이 드러납니다."},
    {"name": "The Sun (태양)", "image_key": "Sun", "keywords_up": ["성공", "기쁨", "활력"], "keywords_rev": ["일시적 우울", "지연"], "meaning_up": "모든 것이 밝게 빛납니다.", "meaning_rev": "구름 뒤에 태양은 여전히 있습니다."},
    {"name": "Judgement (심판)", "image_key": "Judgement", "keywords_up": ["부활", "각성", "결단"], "keywords_rev": ["자기 비하", "거부"], "meaning_up": "새로운 부름에 응답하세요.", "meaning_rev": "과거의 실수에 얽매이지 마세요."},
    {"name": "The World (세계)", "image_key": "World", "keywords_up": ["완성", "통합", "성취"], "keywords_rev": ["미완성", "지연"], "meaning_up": "하나의 주기가 완성되었습니다.", "meaning_rev": "마무리가 조금 부족합니다."}
]

# --- 상태 초기화 ---
if 'logs' not in st.session_state: st.session_state.logs = [{"msg": "System initialized...", "type": "system"}, {"msg": "운명을 해킹하러 왔나? 질문을 입력해.", "type": "system"}]
if 'cards' not in st.session_state: st.session_state.cards = [] 
if 'revealed' not in st.session_state: st.session_state.revealed = []
if 'api_key_input' not in st.session_state: st.session_state.api_key_input = ""
if 'is_shuffling' not in st.session_state: st.session_state.is_shuffling = False
if 'shuffle_count' not in st.session_state: st.session_state.shuffle_count = 1 
if 'pending_ai_idx' not in st.session_state: st.session_state.pending_ai_idx = None
# [수정] run_id는 초기화만 하고, 실행 버튼 누를 때만 갱신 (카드 사라짐 방지)
if 'run_id' not in st.session_state: st.session_state.run_id = str(uuid.uuid4())

# --- 유틸리티 함수 ---
@st.cache_data
def get_b64_image(key, rotate=False):
    if HAS_IMAGES and key in tarot_images:
        try:
            b64_str = tarot_images[key]
            if rotate:
                img_bytes = base64.b64decode(b64_str)
                img = Image.open(io.BytesIO(img_bytes))
                img = img.rotate(180)
                buff = io.BytesIO()
                img.save(buff, format="PNG")
                b64_str = base64.b64encode(buff.getvalue()).decode()
            return f"data:image/png;base64,{b64_str}"
        except: return None
    return None

def add_log(msg, type="normal"):
    st.session_state.logs.append({"msg": msg, "type": type})

# --- 콜백 함수 ---
def flip_card_callback(index):
    # 1. 카드 공개
    st.session_state.revealed[index] = True
    # 2. AI 분석 요청 등록
    st.session_state.pending_ai_idx = index
    # [핵심] 여기서 아무것도 안 하고 함수 종료 -> Streamlit이 알아서 리런하여 화면 그림

# --- AI 처리 ---
def process_pending_ai():
    if st.session_state.pending_ai_idx is None: return
    
    idx = st.session_state.pending_ai_idx
    st.session_state.pending_ai_idx = None # 즉시 큐 비우기 (중복 실행 방지)
    
    if st.session_state.cards[idx].get('ai_done', False): return

    api_key = st.session_state.api_key_input
    if not api_key: return

    card = st.session_state.cards[idx]
    count = len(st.session_state.cards)
    question = st.session_state.get('question', '')
    
    if count == 1: pos_name = "결과"
    elif count == 3: pos_name = ["과거", "현재", "미래"][idx]
    elif count == 10:
        celtic_labels = ["현재", "방해물", "기반", "과거", "목표", "미래", "자신", "주변", "희망/두려움", "최종 결과"]
        pos_name = celtic_labels[idx]
    else: pos_name = f"카드 {idx+1}"

    is_last = (idx == count - 1)
    card_data = card['data']
    is_up = card['is_up']
    orientation = "정방향" if is_up else "역방향"
    meaning = card_data['meaning_up'] if is_up else card_data['meaning_rev']

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = (
            f"당신은 사이버펑크 타로 리더입니다. (반말, 냉철함, Cyberpunk 2077의 Jhonny Silverhand 같은 인격)\n"
            f"질문: {question}\n"
            f"현재 카드: {pos_name} - {card_data['name']} ({orientation})\n"
            f"기본 의미: {meaning}\n"
            f"미션: 이 카드가 '{pos_name}' 관점에서 질문에 갖는 의미를 1~2문장으로 타격감 있게 해석해."
        )
        if is_last:
             prompt += "\n\n(추가 미션: 이게 마지막이다. 해석 후에 엔터 두 번 치고, '🛑 [절명시]' 라벨과 함께 전체 조언을 한 문장으로 요약해줘.)"

        response = model.generate_content(prompt)
        add_log(f"[{pos_name}] 분석 결과:\n{response.text}", "ai")
        st.session_state.cards[idx]['ai_done'] = True
        st.rerun() # 로그 업데이트

    except Exception as e:
        add_log(f"통신 오류: {e}", "system")

# --- 영상 셔플 ---
def animate_and_generate():
    video_file_name = "shuffle.mp4"
    video_placeholder = st.empty()
    
    if os.path.exists(video_file_name):
        with open(video_file_name, "rb") as f:
            video_bytes = f.read()
            video_b64 = base64.b64encode(video_bytes).decode()
        video_html = f"""
        <div style="display: flex; justify-content: center; align-items: center; width: 100%; height: 100%;">
            <video autoplay muted playsinline style="max-height: 400px; width: 100%; object-fit: contain;">
                <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
            </video>
        </div>"""
        with video_placeholder: st.markdown(video_html, unsafe_allow_html=True)
        time.sleep(3.5) 
        video_placeholder.empty()
    else:
        with video_placeholder:
            st.info("🔄 데이터 스트림 셔플링 중... (shuffle.mp4 없음)")
            time.sleep(1.5)
        video_placeholder.empty()
    
    raw = random.sample(TAROT_DATA, st.session_state.shuffle_count)
    selected = []
    common_back = get_b64_image("back") or get_b64_image("Fool")
    
    for c in raw:
        is_up = random.choice([True, False])
        front_img = get_b64_image(c['image_key'], rotate=not is_up)
        selected.append({
            "data": c, "is_up": is_up, "ai_done": False,
            "front_src": front_img, "back_src": common_back
        })
    
    st.session_state.cards = selected
    st.session_state.revealed = [False] * st.session_state.shuffle_count
    st.session_state.is_shuffling = False
    add_log("카드 생성 완료. 뒤집어서 확인해.", "system")
    st.rerun()

def start_execution():
    q_input = st.session_state.cmd_input
    if not q_input:
        st.warning("질문을 입력해라.")
        return
    
    # [수정] 실행할 때만 ID 변경 (기존 카드가 사라지지 않도록)
    st.session_state.run_id = str(uuid.uuid4())
    st.session_state.question = q_input
    add_log(f"QUERY: {q_input}", "user")
    add_log("셔플 시퀀스 개시...", "system")
    
    st.session_state.cards = []
    st.session_state.revealed = []
    st.session_state.is_shuffling = True
    
    mode = st.session_state.mode_input
    if "단일" in mode: st.session_state.shuffle_count = 1
    elif "10장" in mode: st.session_state.shuffle_count = 10
    else: st.session_state.shuffle_count = 3

# --- 렌더링 함수 (Fragment 제거) ---
# @st.fragment  <-- 제거됨! 일반 함수로 전환하여 안정성 확보
def render_single_card(index, label_txt, img_width, label_size, run_id, total_count):
    st.markdown(f"<div class='card-wrapper'>", unsafe_allow_html=True)
    st.markdown(f"<div class='pos-label' style='font-size:{label_size}'>{label_txt}</div>", unsafe_allow_html=True)
    
    card = st.session_state.cards[index]
    is_revealed = st.session_state.revealed[index]
    
    back_src = card.get('back_src')
    if not back_src: back_src = get_b64_image("back") or get_b64_image("Fool")
    
    if is_revealed:
        real_src = card.get('front_src')
        if not real_src: real_src = get_b64_image(card['data']['image_key'], rotate=not card['is_up'])
            
        name = card['data']['name']
        ori = "정방향" if card['is_up'] else "역방향"
        badge_class = "status-badge" if card['is_up'] else "status-badge rev"
        
        st.markdown(f"<img src='{real_src}' width='{img_width}' class='card-img'>", unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class='control-area'>
                <div class='card-name-box'>{name}</div>
                <div style='text-align:center;'><span class='{badge_class}'>{ori}</span></div>
            </div>
        """, unsafe_allow_html=True)
        
    else:
        st.markdown(f"<img src='{back_src}' width='{img_width}' class='card-img'>", unsafe_allow_html=True)
        
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        
        if total_count == 10:
            st.button("뒤집기", key=f"flip_{index}_{run_id}", on_click=flip_card_callback, args=(index,), use_container_width=True)
        else:
            if total_count == 1:
                c1, c2, c3 = st.columns([12, 4, 12], gap="small")
            else:
                c1, c2, c3 = st.columns([3, 2, 3], gap="small")
            with c2:
                st.button("뒤집기", key=f"flip_{index}_{run_id}", on_click=flip_card_callback, args=(index,), use_container_width=True)
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# --- 사이드바 ---
with st.sidebar:
    st.title("⚙️ SETTINGS")
    api_input = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요", value=st.session_state.api_key_input)
    if st.button("🔌 시스템 연동 (CONNECT)"):
        st.session_state.api_key_input = api_input
        st.rerun()
    if st.session_state.api_key_input: st.success("✅ Neural Link Active")
    else: st.caption("⚠️ API Key Required")

# --- 메인 레이아웃 ---
st.title("사이버펑크 식으로 타로점 보기")

col_cards, col_chat = st.columns([7, 3])

# ================= LEFT: CARD STAGE =================
with col_cards:
    h_col1, h_col2 = st.columns([3, 1], gap="small")
    with h_col1:
        st.markdown("### 카드 보드")
    with h_col2:
        st.selectbox("MODE", ["단일 카드 (1장)", "시간의 흐름 (과거, 현재, 미래)", "정석 켈틱 크로스 (10장)"], 
                     label_visibility="collapsed", key="mode_input")
    
    # [핵심] 고스트 현상 방지: st.empty + container 조합
    stage_placeholder = st.empty()
    
    if st.session_state.is_shuffling:
        with stage_placeholder.container(height=650, border=True):
            animate_and_generate()
    
    elif st.session_state.cards:
        with stage_placeholder.container(height=650, border=True):
            # run_id는 실행 시에만 바뀜 -> 카드 뒤집어도 그리드 유지됨
            grid_container = st.container(key=f"grid_{st.session_state.run_id}")
            
            with grid_container:
                count = len(st.session_state.cards)
                
                if count == 10:
                    row1 = st.columns(5)
                    row2 = st.columns(5)
                    all_cols = row1 + row2 
                    img_width = 85
                    label_size = "0.8em"
                else:
                    all_cols = st.columns(count)
                    img_width = 150 
                    label_size = "0.9em"
                
                celtic_labels = ["1.현재", "2.방해물", "3.먼과거", "4.가까운과거", "5.목표", "6.가까운미래", "7.본인", "8.주변", "9.두려움", "10.결과"]
                
                for i, col in enumerate(all_cols):
                    with col:
                        if count == 10: label_txt = celtic_labels[i]
                        elif count == 3: label_txt = ["PAST (과거)", "PRESENT (현재)", "FUTURE (미래)"][i]
                        else: label_txt = "THE ANSWER (결과)"
                        
                        render_single_card(i, label_txt, img_width, label_size, st.session_state.run_id, count)
    
    else:
        with stage_placeholder.container(height=600, border=True):
            st.info("운명을 기다리는 중... (아래 칸에 질문을 입력하세요.)")

# ================= RIGHT: LOG SYSTEM =================
with col_chat:
    pc1, pc2 = st.columns([1, 3])
    with pc1:
        p_img = get_b64_image("profile")
        if p_img: st.markdown(f"<img src='{p_img}' width='60' style='border-radius:50%;'>", unsafe_allow_html=True)
        else: st.write("🤖")
    with pc2:
        st.write("**기업에 잠식당한 익명의 타로 점술가**")
        # [수정] 기존 st.caption("● Online")을 HTML 네온 효과로 교체
        st.markdown(
            """
            <div style="
                color: #39FF14; 
                font-size: 12px; 
                font-weight: bold;
                text-shadow: 0 0 5px rgba(57, 255, 20, 0.8);
                margin-top: -5px;
            ">
                ● ONLINE
            </div>
            """, 
            unsafe_allow_html=True
        )

    l_col1, l_col2 = st.columns([4, 1])
    with l_col1:
        st.markdown("### 📟 LOG")
    with l_col2:
        if st.button("CLEAR", key="clear_log_btn", use_container_width=True):
            st.session_state.logs = []
            st.rerun()

    log_box = st.container(height=500, border=True)
    
    with log_box:
        for item in reversed(st.session_state.logs):
            if isinstance(item, dict):
                msg = item.get('msg', '')
                mtype = item.get('type', 'normal')
            else:
                msg = str(item)
                mtype = 'normal'
            
            if mtype == "system": st.markdown(f"<div class='system-msg'>🔄 {msg}</div>", unsafe_allow_html=True)
            elif mtype == "ai": st.markdown(f"<div class='ai-msg'>{msg}</div>", unsafe_allow_html=True)
            elif mtype == "user": st.markdown(f"<div class='user-msg'>➤ {msg}</div>", unsafe_allow_html=True)
            else: st.markdown(f"<div>{msg}</div>", unsafe_allow_html=True)

    row_input = st.columns([3, 1], gap="small")
    with row_input[0]:
        st.text_input("CMD", placeholder="질문 입력...", label_visibility="collapsed", key="cmd_input")
    with row_input[1]:
        st.button("EXECUTE", type="primary", on_click=start_execution)

# --- AI 처리 (메인 루프 끝에서 실행) ---
if st.session_state.pending_ai_idx is not None:
    # [수정] 스피너를 추가하여 분석 중임을 시각적으로 강하게 표시
    with st.spinner("🧠 Neural Network Analyzing... (데이터 해석 중)"):
        process_pending_ai()