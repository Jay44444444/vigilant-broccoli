import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import threading
import io
import base64
import json
import sys
import os

# 현재 파일 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# --- 이미지 데이터 로드 ---
try:
    from tarot_images import tarot_images
    HAS_IMAGES = True
except ImportError:
    HAS_IMAGES = False
    print("⚠️ 'tarot_images.py'가 없습니다.")

# --- 보안 모듈 ---
try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False
try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# ==========================================
# 🔒 보안 관리자
# ==========================================
class SecurityManager:
    def __init__(self):
        self.service_id = "CyberpunkTarotApp"
        self.username = "master_key"
        self.key = None
        self.cipher = None
        self.init_key()

    def init_key(self):
        if not HAS_CRYPTO: return
        stored_key = None
        if HAS_KEYRING:
            try: stored_key = keyring.get_password(self.service_id, self.username)
            except: pass
        if stored_key: self.key = stored_key.encode()
        else:
            self.key = Fernet.generate_key()
            if HAS_KEYRING:
                try: keyring.set_password(self.service_id, self.username, self.key.decode())
                except: pass
        self.cipher = Fernet(self.key)

    def encrypt(self, text):
        if not self.cipher or not text: return text
        try: return self.cipher.encrypt(text.encode()).decode()
        except: return text

    def decrypt(self, encrypted_text):
        if not self.cipher or not encrypted_text: return encrypted_text
        try: return self.cipher.decrypt(encrypted_text.encode()).decode()
        except: return ""

# ==========================================
# 🃏 타로 데이터
# ==========================================
TAROT_DATA = [
    {"name": "The Fool (바보)", "image_key": "Fool", 
     "keywords_up": ["새로운 시작", "순수함", "자유"], "keywords_rev": ["무모함", "어리석음", "위험"],
     "meaning_up": "두려움 없는 새로운 여정의 시작.", "meaning_rev": "준비되지 않은 시작은 위험할 수 있습니다."},
    
    {"name": "The Magician (마법사)", "image_key": "Magician", 
     "keywords_up": ["창조", "숙련됨", "의지"], "keywords_rev": ["속임수", "재능 낭비"],
     "meaning_up": "당신은 필요한 모든 도구를 가지고 있습니다.", "meaning_rev": "능력을 잘못된 곳에 쓰고 있습니다."},
    
    {"name": "The High Priestess (여사제)", "image_key": "High Priestess", 
     "keywords_up": ["직관", "무의식", "신비"], "keywords_rev": ["비밀", "내면 무시"],
     "meaning_up": "직관을 따르세요. 답은 안에 있습니다.", "meaning_rev": "내면의 소리를 무시하지 마세요."},
    
    {"name": "The Empress (여황제)", "image_key": "Empress",
     "keywords_up": ["풍요", "모성", "창조성"], "keywords_rev": ["의존", "창조력 고갈"],
     "meaning_up": "풍요로움과 창조성이 넘치는 시기입니다.", "meaning_rev": "자신을 돌보는 데 소홀하지 마세요."},

    {"name": "The Emperor (황제)", "image_key": "Emperor",
     "keywords_up": ["권위", "구조", "통제"], "keywords_rev": ["지배", "고집", "규율 부족"],
     "meaning_up": "질서와 리더십이 필요한 때입니다.", "meaning_rev": "너무 강압적이거나 통제력을 잃지 마세요."},

    {"name": "The Hierophant (교황)", "image_key": "Hierophant",
     "keywords_up": ["전통", "신념", "가르침"], "keywords_rev": ["반항", "부적응"],
     "meaning_up": "전통적인 방식이나 조언을 따르세요.", "meaning_rev": "자신만의 신념을 찾아야 할 때입니다."},

    {"name": "The Lovers (연인)", "image_key": "Lovers",
     "keywords_up": ["사랑", "조화", "선택"], "keywords_rev": ["불화", "불균형"],
     "meaning_up": "중요한 선택의 기로에 서 있습니다.", "meaning_rev": "관계의 갈등이나 후회가 있을 수 있습니다."},

    {"name": "The Chariot (전차)", "image_key": "Chariot",
     "keywords_up": ["승리", "의지", "행동"], "keywords_rev": ["패배", "통제 상실"],
     "meaning_up": "목표를 향해 거침없이 나아가세요.", "meaning_rev": "방향을 잃거나 너무 서두르지 마세요."},

    {"name": "Strength (힘)", "image_key": "Strength",
     "keywords_up": ["용기", "인내", "내면의 힘"], "keywords_rev": ["나약함", "폭발"],
     "meaning_up": "부드러움이 강함을 이깁니다.", "meaning_rev": "자신감을 잃지 마세요."},

    {"name": "The Hermit (은둔자)", "image_key": "Hermit",
     "keywords_up": ["성찰", "고독", "탐구"], "keywords_rev": ["고립", "외로움"],
     "meaning_up": "잠시 멈추고 내면을 들여다볼 시간입니다.", "meaning_rev": "세상과의 소통을 끊지 마세요."},

    {"name": "Wheel of Fortune (운명)", "image_key": "Wheel of Fortune",
     "keywords_up": ["변화", "운명", "행운"], "keywords_rev": ["불운", "저항"],
     "meaning_up": "운명이 당신 편입니다. 변화를 받아들이세요.", "meaning_rev": "피할 수 없는 변화가 오고 있습니다."},

    {"name": "Justice (정의)", "image_key": "Justice",
     "keywords_up": ["정의", "공정", "진실"], "keywords_rev": ["불공정", "편견"],
     "meaning_up": "행동에는 결과가 따릅니다. 공정하세요.", "meaning_rev": "자신에게 솔직해져야 할 때입니다."},

    {"name": "The Hanged Man (매달린 자)", "image_key": "Hanged Man",
     "keywords_up": ["희생", "새로운 관점"], "keywords_rev": ["무의미한 희생", "정체"],
     "meaning_up": "다른 관점에서 상황을 바라보세요.", "meaning_rev": "너무 오래 망설이고 있지는 않나요?"},

    {"name": "Death (죽음)", "image_key": "Death",
     "keywords_up": ["끝", "새로운 시작", "변형"], "keywords_rev": ["저항", "정체", "두려움"],
     "meaning_up": "과거를 놓아주면 새로운 문이 열립니다.", "meaning_rev": "변화를 두려워하지 말고 받아들이세요."},

    {"name": "Temperance (절제)", "image_key": "Temperance",
     "keywords_up": ["균형", "중용", "조화"], "keywords_rev": ["불균형", "과도함"],
     "meaning_up": "극단을 피하고 균형을 찾으세요.", "meaning_rev": "삶의 균형이 깨져 있습니다."},

    {"name": "The Devil (악마)", "image_key": "Devil",
     "keywords_up": ["속박", "중독", "유혹"], "keywords_rev": ["해방", "자유"],
     "meaning_up": "자신을 옭아매는 것으로부터 벗어나세요.", "meaning_rev": "어두운 사슬을 끊을 기회입니다."},

    {"name": "The Tower (탑)", "image_key": "Tower",
     "keywords_up": ["갑작스런 변화", "붕괴"], "keywords_rev": ["재난 모면", "두려움"],
     "meaning_up": "기초가 무너지고 있습니다. 다시 세우세요.", "meaning_rev": "변화를 거부하면 고통만 길어집니다."},

    {"name": "The Star (별)", "image_key": "Star",
     "keywords_up": ["희망", "영감", "평온"], "keywords_rev": ["절망", "믿음 부족"],
     "meaning_up": "어둠 끝에 빛이 보입니다.", "meaning_rev": "긍정적인 마음을 잃지 마세요."},

    {"name": "The Moon (달)", "image_key": "Moon",
     "keywords_up": ["환상", "불안", "모호함"], "keywords_rev": ["진실 드러남", "평정"],
     "meaning_up": "보이는 것이 전부가 아닙니다.", "meaning_rev": "안개가 걷히고 진실이 드러납니다."},

    {"name": "The Sun (태양)", "image_key": "Sun",
     "keywords_up": ["성공", "기쁨", "활력"], "keywords_rev": ["일시적 우울", "지연"],
     "meaning_up": "모든 것이 밝게 빛납니다.", "meaning_rev": "구름 뒤에 태양은 여전히 있습니다."},

    {"name": "Judgement (심판)", "image_key": "Judgement",
     "keywords_up": ["부활", "각성", "결단"], "keywords_rev": ["자기 비하", "거부"],
     "meaning_up": "새로운 부름에 응답하세요.", "meaning_rev": "과거의 실수에 얽매이지 마세요."},

    {"name": "The World (세계)", "image_key": "World",
     "keywords_up": ["완성", "통합", "성취"], "keywords_rev": ["미완성", "지연"],
     "meaning_up": "하나의 주기가 완성되었습니다.", "meaning_rev": "마무리가 조금 부족합니다."}
]

# AI 모듈
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# ==========================================
# 🖥️ 앱 메인 클래스 (v9.0 - 툴팁 기능 추가 + 사용자 텍스트 유지)
# ==========================================
class TarotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🔮 Cyberpunk Tarot v9.0")
        
        self.geometry("1200x800") 
        self.minsize(1100, 750)
        ctk.set_appearance_mode("Dark")
        
        self.security = SecurityManager()
        self.api_key = self.load_saved_api_key()

        # 상태 변수
        self.is_shuffling = False
        self.revealed_cards_count = 0
        self.total_cards_to_reveal = 0
        self.drawn_results = []
        self.canvas_images = [] # 이미지가 가비지 컬렉션되지 않도록 참조 저장
        self.card_items = []    # 캔버스에 그려진 카드 객체 ID 저장
        
        # 툴팁용 변수 (추가됨)
        self.tooltip_window = None
        
        # 메인 그리드 설정
        self.grid_rowconfigure(1, weight=1) 
        self.grid_columnconfigure(0, weight=70) # 왼쪽 70%
        self.grid_columnconfigure(1, weight=30) # 오른쪽 30%

        self.create_ui()

    def create_ui(self):
        # [0. 헤더]
        self.header_frame = ctk.CTkFrame(self, height=50, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 0))
        
        self.lbl_title = ctk.CTkLabel(self.header_frame, text="🌃 Cyberpunk Tarot Reader", 
                                      font=("Roboto Medium", 24), text_color="#00E5FF")
        self.lbl_title.pack(side="left")
        
        self.btn_setting = ctk.CTkButton(self.header_frame, text="⚙️ AI Key", width=80, 
                                         fg_color="#333", command=self.open_api_key_window)
        self.btn_setting.pack(side="right")

        # [1. 좌측: 캔버스 전시대]
        self.left_frame = ctk.CTkFrame(self, fg_color="#101010", corner_radius=15, border_width=1, border_color="#333")
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        
        # Canvas 생성
        self.canvas = tk.Canvas(self.left_frame, bg="#101010", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)
        
        # 테이블 배경 그리기
        self.table_bg_img = self.load_image_object("table", size=(1200, 900))
        if self.table_bg_img:
            self.canvas.create_image(600, 450, image=self.table_bg_img, anchor="center")

        # 초기 안내 문구 (사용자 지정 텍스트 확인 필요 - 여기는 기본값)
        self.intro_text = self.canvas.create_text(420, 315, text="[ SYSTEM READY ]\n\n터미널에서 명령을 실행하십시오.", 
                                                  font=("Consolas", 16), fill="#E0F7FA", justify="center")

        # [2. 우측: 데이터 로그]
        self.right_frame = ctk.CTkFrame(self, fg_color="#222", corner_radius=15, border_width=1, border_color="#333")
        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 20), pady=10)
        
        # 프로필
        self.profile_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent", height=80)
        self.profile_frame.pack(fill="x", padx=15, pady=15)
        
        self.profile_img_ctk = self.load_image_ctk("profile", size=(60, 60))
        if self.profile_img_ctk:
            self.lbl_profile = ctk.CTkLabel(self.profile_frame, image=self.profile_img_ctk, text="")
        else:
            self.lbl_profile = ctk.CTkLabel(self.profile_frame, text="🤖", font=("", 40))
        self.lbl_profile.pack(side="left")
        
        ctk.CTkLabel(self.profile_frame, text="Tarot Bot_V9.0", font=("", 14, "bold"), text_color="#00E5FF").pack(side="left", padx=10)
        ctk.CTkLabel(self.profile_frame, text="● Online", font=("", 12), text_color="#00FF00").pack(side="left")

        # 로그 박스
        self.txt_log = ctk.CTkTextbox(self.right_frame, font=("NanumGothic", 13), 
                                      fg_color="#1a1a1a", text_color="#ccc", wrap="word")
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.log_print("System initialized...")
        self.log_print("운명을 해킹하러 왔나? 좋아.\n질문을 던지고 Enter를 눌러. 네 미래를 데이터로 컴파일해주지.")

        # [3. 하단: 컨트롤]
        self.bottom_frame = ctk.CTkFrame(self, height=80, fg_color="transparent")
        self.bottom_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        
        self.seg_mode = ctk.CTkSegmentedButton(self.bottom_frame, values=["단일 카드 (Single)", "과거/현재/미래 (3-Card)"])
        self.seg_mode.set("단일 카드 (Single)")
        self.seg_mode.pack(side="top", pady=(0, 10))
        
        input_container = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        input_container.pack(fill="x")
        
        self.entry_question = ctk.CTkEntry(input_container, placeholder_text="명령어(질문) 입력 >", 
                                           font=("Consolas", 14), height=40, border_color="#D500F9")
        self.entry_question.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_question.bind("<Return>", self.start_draw_sequence)
        
        self.btn_draw = ctk.CTkButton(input_container, text="EXECUTE", command=self.start_draw_sequence, 
                                      fg_color="#D500F9", hover_color="#AA00FF", width=120, height=40, font=("", 14, "bold"))
        self.btn_draw.pack(side="right")
        
        self.canvas.bind("<Configure>", self.on_canvas_resize)

    def on_canvas_resize(self, event):
        self.canvas.coords(1, event.width/2, event.height/2)
        if hasattr(self, 'intro_text'):
             self.canvas.coords(self.intro_text, event.width/2, event.height/2)

    # --- 툴팁 기능 (마우스 오버) ---
    def show_tooltip(self, event, text):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        
        # 툴팁 윈도우 생성
        x, y = event.x_root + 20, event.y_root + 10
        self.tooltip_window = tk.Toplevel(self)
        self.tooltip_window.wm_overrideredirect(True) # 타이틀바 제거
        self.tooltip_window.geometry(f"+{x}+{y}")
        self.tooltip_window.wm_attributes("-topmost", True)

        # 툴팁 디자인
        frame = tk.Frame(self.tooltip_window, bg="#111", highlightbackground="#00E5FF", highlightthickness=1)
        frame.pack()
        
        label = tk.Label(frame, text=text, justify="left", 
                         bg="#111", fg="#fff", font=("NanumGothic", 10), padx=8, pady=5)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    # --- 유틸리티 ---
    def load_image_object(self, key, size=(200, 320), rotate=False):
        if not HAS_IMAGES or key not in tarot_images: return None
        try:
            pil_image = Image.open(io.BytesIO(base64.b64decode(tarot_images[key])))
            pil_image = pil_image.resize(size, Image.Resampling.LANCZOS)
            if rotate: pil_image = pil_image.rotate(180)
            return ImageTk.PhotoImage(pil_image)
        except: return None

    def load_image_ctk(self, key, size=(200, 320)):
        if not HAS_IMAGES or key not in tarot_images: return None
        try:
            pil_image = Image.open(io.BytesIO(base64.b64decode(tarot_images[key])))
            return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=size)
        except: return None

    def log_print(self, text):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", text + "\n\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    # =========================================================
    # ★ 메인 로직
    # =========================================================
    def start_draw_sequence(self, event=None):
        if self.is_shuffling: return
        question = self.entry_question.get().strip()
        if not question:
            messagebox.showwarning("[SYSTEM MESSAGE]", "네 운명을 알고싶나?")
            return

        self.is_shuffling = True
        self.revealed_cards_count = 0
        self.drawn_results = []
        
        self.canvas.delete("card_obj") 
        self.canvas.delete("text_obj")
        if hasattr(self, 'intro_text'): self.canvas.delete(self.intro_text)
        
        self.log_print(f">>> QUESTION RECEIVED: {question}")
        self.log_print("🔄 [SYSTEM] 데이터를 헤짚는 중...")

        mode = self.seg_mode.get()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        
        if mode == "단일 카드 (Single)":
            self.total_cards_to_reveal = 1
            self.drawn_results = [self.pick_random_card()]
            
            cx, cy = cw / 2, ch / 2
            item = self.canvas.create_image(cx, cy, tags="card_obj")
            self.card_items = [item]
            
        else:
            self.total_cards_to_reveal = 3
            positions_txt = ["과거", "현재", "미래"]
            self.drawn_results = []
            raw_cards = random.sample(TAROT_DATA, 3)
            
            gap = cw / 4
            cy = ch / 2
            self.card_items = []
            
            for i in range(3):
                cx = gap * (i + 1)
                self.drawn_results.append({"card": raw_cards[i], "is_up": random.choice([True, False])})
                
                self.canvas.create_text(cx, cy - 160, text=positions_txt[i], 
                                        font=("Arial", 14, "bold"), fill="#00E5FF", tags="text_obj")
                item = self.canvas.create_image(cx, cy, tags="card_obj")
                self.card_items.append(item)

        self.animate_shuffle(steps=20)

    def pick_random_card(self):
        return {"card": random.choice(TAROT_DATA), "is_up": random.choice([True, False])}

    def animate_shuffle(self, steps):
        if steps > 0:
            self.canvas_images = []
            for item in self.card_items:
                rnd = random.choice(TAROT_DATA)
                size = (165, 270) if self.total_cards_to_reveal == 3 else (280, 450)
                img = self.load_image_object(rnd["image_key"], size=size)
                if img:
                    self.canvas_images.append(img)
                    self.canvas.itemconfig(item, image=img)
            self.after(80, lambda: self.animate_shuffle(steps - 1))
        else:
            self.show_backs()

    def show_backs(self):
        self.is_shuffling = False
        # ★ 사용자 수정 텍스트 유지
        self.log_print("네 운명은 결정되었다... 해석이 필요하다면 카드를 눌러 뒤집어 보도록...")
        
        self.canvas_images = []
        size = (165, 270) if self.total_cards_to_reveal == 3 else (280, 450)
        back_img = self.load_image_object("back", size=size) or self.load_image_object("Fool", size=size)
        self.canvas_images.append(back_img)

        for idx, item in enumerate(self.card_items):
            self.canvas.itemconfig(item, image=back_img)
            self.canvas.tag_bind(item, "<Button-1>", lambda event, i=idx, item_id=item: self.reveal_card(i, item_id))

    def reveal_card(self, index, item_id):
        if self.drawn_results[index].get("revealed", False): return

        self.drawn_results[index]["revealed"] = True
        
        result = self.drawn_results[index]
        card_data = result["card"]
        is_up = result["is_up"]
        
        # 이미지 교체
        size = (165, 270) if self.total_cards_to_reveal == 3 else (280, 450)
        real_img = self.load_image_object(card_data["image_key"], size=size, rotate=not is_up)
        
        self.canvas_images.append(real_img)
        self.canvas.itemconfig(item_id, image=real_img)
        
        # 텍스트 추가
        orientation = "정방향" if is_up else "역방향"
        coords = self.canvas.coords(item_id)
        cx, cy = coords[0], coords[1]
        
        offset = 160 if self.total_cards_to_reveal == 3 else 250
        self.canvas.create_text(cx, cy + offset, text=f"{card_data['name']}\n({orientation})", 
                                font=("NanumGothic", 12, "bold"), fill="#FFD700", justify="center", tags="text_obj")

        # ★ 툴팁 이벤트 바인딩 추가됨
        meaning = card_data['meaning_up'] if is_up else card_data['meaning_rev']
        keywords = card_data['keywords_up'] if is_up else card_data['keywords_rev']
        tooltip_text = f"[{card_data['name']}]\n{orientation}\n\nKey: {', '.join(keywords)}\n\n{meaning}"
        
        self.canvas.tag_bind(item_id, "<Enter>", lambda event, t=tooltip_text: self.show_tooltip(event, t))
        self.canvas.tag_bind(item_id, "<Leave>", self.hide_tooltip)

        # AI 요청
        question = self.entry_question.get()
        pos_name = "결과"
        if self.total_cards_to_reveal == 3:
            pos_name = ["과거", "현재", "미래"][index]
        
        self.log_print(f"⚡ Decrypting [{pos_name}]: {card_data['name']}...")
        
        is_last = (self.revealed_cards_count + 1 == self.total_cards_to_reveal)
        threading.Thread(target=self.ask_gemini_step, 
                         args=(question, card_data, is_up, pos_name, is_last)).start()

        self.revealed_cards_count += 1

    def ask_gemini_step(self, question, card_data, is_up, pos_name, is_last):
        if not HAS_GEMINI or not self.api_key:
            meaning = card_data['meaning_up'] if is_up else card_data['meaning_rev']
            self.log_print(f"[{pos_name} 기본 해석]\n{meaning}")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")

            orientation = "정방향" if is_up else "역방향"
            meaning = card_data['meaning_up'] if is_up else card_data['meaning_rev']

            prompt = (
                f"당신은 사이버펑크 타로 리더입니다. (반말, 냉철함)\n"
                f"질문: {question}\n"
                f"현재 카드: {pos_name} - {card_data['name']} ({orientation})\n"
                f"기본 의미: {meaning}\n\n"
                f"미션: 이 카드가 '{pos_name}' 관점에서 질문에 갖는 의미를 1~2문장으로 타격감 있게 해석해."
            )
            
            if is_last and self.total_cards_to_reveal == 3:
                prompt += "\n\n(추가 미션: 이게 마지막이다. 해석 후에 엔터 두 번 치고, '🛑 [절명시]' 라벨과 함께 전체 조언을 한 문장으로 요약해줘.)"

            response = model.generate_content(prompt)
            self.log_print(f"➤ {pos_name} 분석:\n{response.text.strip()}")

        except Exception as e:
            self.log_print(f"❌ 접속 오류: {e}")

    # --- API 관리 ---
    def load_saved_api_key(self):
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r", encoding="utf-8") as f:
                    return self.security.decrypt(json.load(f).get("api_key", ""))
        except: pass
        return ""
    def save_api_key(self, raw_key):
        try:
            encrypted = self.security.encrypt(raw_key)
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump({"api_key": encrypted}, f)
            self.api_key = raw_key
            messagebox.showinfo("저장", "키 저장 완료")
        except Exception as e: messagebox.showerror("오류", f"{e}")
    def open_api_key_window(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("API Key")
        dialog.geometry("400x200")
        ctk.CTkLabel(dialog, text="Gemini API Key").pack(pady=20)
        entry = ctk.CTkEntry(dialog, width=300, show="*")
        entry.pack(pady=5)
        if self.api_key: entry.insert(0, self.api_key)
        def save():
            self.save_api_key(entry.get().strip())
            dialog.destroy()
        ctk.CTkButton(dialog, text="저장", command=save).pack(pady=20)

if __name__ == "__main__":
    app = TarotApp()
    app.mainloop()