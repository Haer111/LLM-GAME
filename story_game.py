import streamlit as st
import os, json
from openai import OpenAI
from dotenv import load_dotenv
import base64

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from chapter_prompts import CHAPTERS

SYSTEM_PROMPT = """
[역할 설명]
너는 중국 드라마 <무우도(无忧渡)> 세계관을 기반으로 한 인터랙티브 스토리 게임의 게임 마스터이다.
너의 임무는 장면을 묘사하고, 대화를 보여주며, 플레이어 선택에 따라 이야기를 분기시킨다.

[출력 형식]
반드시 JSON 형식으로만 출력한다:
{
 "scene_summary": "이번 장면 요약 (2~3문장)",
 "narration": "장면 묘사와 등장인물 대화",
 "choices": ["선택1", "선택2"],
 "game_over": false,
 "ending_type": null,
 "chapter_clear": false
}

[표현 규칙]
- narration에는 장면 묘사 + 등장인물 대화를 포함한다.
- 대화 형식: 이름: "대사"
- 플레이어에게 직접 말하지 않는다.
- scene_summary는 2~3문장만 작성한다.
- 전투 묘사는 3문장 이내, 핵심 행동과 결론만 포함한다.

[진행 규칙]
1. 각 챕터는 반드시 **선택 절차 5번 이내에서 끝난다.**
   - 4번째~5번째 선택 이후에는 반드시 결말을 출력한다.
2. 결말은 두 가지뿐이다:
   - 모든 사건이 마무리 → chapter_clear=true
   - 주요 인물(반하, 선야) 중 한 명 이상 사망 → game_over=true
3. '요괴 퇴치 과정/숨겨진 진실'과 '선택지 힌트'를 반드시 활용한다.
4. 원작 선택 → 원작 전개, 다른 선택 → 새로운 전개.

[능력 제한]
- 도술/마법은 선야와 사숙만 사용할 수 있다.
- 반하는 절대 도술/마법을 쓰지 않는다. 그녀의 능력은 '요괴를 볼 수 있는 눈'뿐이다.
- 다른 인물들은 무기, 계략, 대화 등 인간적인 방법만 사용한다.

[금지 사항 — 절대 위반 금지]
- 반하가 도술/마법을 쓰는 장면을 만들지 마라.
- 선택 절차가 6번 이상 이어지지 않도록 반드시 결말로 끝내라.
"""

class StoryGameModel:
    def __init__(self, model_name="gpt-4o-mini"):
        self.model = model_name

    def generate(self, system_prompt: str, user_prompt: str):
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.8
        )
        return json.loads(response.choices[0].message.content)

def set_background(img_path: str):
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            [data-testid="stAppViewContainer"] {{
                background: 
                    linear-gradient(rgba(255,255,255,0.6), rgba(255,255,255,0.6)),
                    url("data:image/jpg;base64,{img_base64}") no-repeat center center fixed;
                background-size: cover;
            }}
            [data-testid="stHeader"], [data-testid="stSidebar"] {{
                background: rgba(0,0,0,0);
            }}
            h1 {{ font-size: 3rem !important; font-weight: 700 !important; }}
            h2 {{ font-size: 2rem !important; font-weight: 600 !important; }}
            h3 {{ font-size: 1.5rem !important; font-weight: 500 !important; }}
            p, li, span {{ font-size: 1.2rem !important; }}
            button, .stButton>button {{
                font-size: 1.2rem !important;
                padding: 0.6em 1.2em !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

if "page" not in st.session_state:
    st.session_state.page = "intro"
if "chapter" not in st.session_state:
    st.session_state.chapter = 0
if "result" not in st.session_state:
    st.session_state.result = None
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "chapter_intro" not in st.session_state:
    st.session_state.chapter_intro = True
if "model" not in st.session_state:
    st.session_state.model = StoryGameModel()
if "choices_log" not in st.session_state:
    st.session_state.choices_log = []


def intro_page():
    set_background("main_poster2.jpg") 

    st.title("무우도(无忧渡) — 인터랙티브 스토리 게임")

    st.subheader("배경 설명")
    st.markdown("""
    번화한 광평성에서는 인간과 요괴가 함께 살아가고 있지만, 
    요괴들이 인간으로 위장해 흔적도 없이 숨어 있기에 인간들은 그들의 존재를 쉽게 알아차리지 못한다. 
    부잣집 아가씨 반하는 신비한 눈을 가지고 있어 존재할 리 없는 존재들을 자주 본다. 
    어느 날, 반하는 새언니가 사실 요괴라는 비밀을 알아채고 목숨을 위협받게 되었고, 
    이로 인해 요괴 사냥꾼인 선야를 만나게 된다. 
    두 사람은 함께 광평성에서 벌어지는 기이한 사건들을 조사하면서 가까워지는데...
    """)

    st.subheader("주요 등장인물")
    st.markdown("""
    - **반하**: 요괴의 실체를 볼 수 있는 특별한 눈을 가진 여인. 
    - **선야**: 요괴 사냥꾼으로, 반하와 함께 여러 사건을 해결한다.
    - **지설**: 반하와 선야를 돕는 동료(토끼 요괴)
    """)

    if st.button("게임 시작"):
        st.session_state.page = "game"
        st.session_state.chapter = 0
        st.session_state.result = None
        st.session_state.chapter_intro = True
        st.session_state.game_over = False
        st.session_state.choices_log = []
        st.rerun()


def game_page():
    bg_path = f"bg_ch{st.session_state.chapter+1}.jpg"
    set_background(bg_path)

    if st.session_state.game_over:
        st.subheader("🎬 게임 종료")
        st.write(f"엔딩 타입: {st.session_state.result['ending_type']}")
        st.write(st.session_state.result["narration"])

        st.subheader("📜 당신의 선택 기록")
        for idx, log in enumerate(st.session_state.choices_log, 1):
            st.write(f"{idx}. {log}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("다시 시작"):
                st.session_state.page = "game"
                st.session_state.chapter = 0
                st.session_state.result = None
                st.session_state.game_over = False
                st.session_state.chapter_intro = True
                st.session_state.choices_log = []
                st.rerun()

        with col2:
            if st.button("처음 화면으로 돌아가기"):
                st.session_state.page = "intro"
                st.session_state.chapter = 0
                st.session_state.result = None
                st.session_state.game_over = False
                st.session_state.chapter_intro = True
                st.session_state.choices_log = []
                st.rerun()
        return

    if st.session_state.chapter_intro:
        chapter_data = CHAPTERS[st.session_state.chapter]
        st.title(chapter_data["title"])
        col1, col2 = st.columns([1, 2])
        with col1:
            img_path = f"chapter{st.session_state.chapter+1}.jpg"
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True)
        with col2:
            st.markdown(chapter_data["display_intro"])
            bcol1, bcol2, bcol3 = st.columns([1, 2, 1])
        with bcol2:
            if st.button("챕터 시작하기", use_container_width=True):
                chapter_data = CHAPTERS[st.session_state.chapter]
                user_prompt = f"""
                {chapter_data['title']}
                {chapter_data['full_prompt']}
                이번 챕터에서 반드시 아래 규칙을 지켜라:
                {SYSTEM_PROMPT}
                """
                st.session_state.result = st.session_state.model.generate(SYSTEM_PROMPT, user_prompt)
                st.session_state.chapter_intro = False
                st.rerun()
        return

    result = st.session_state.result
    st.write("📖 **내레이션**")
    st.write(result["narration"])

    # 강제 결말 처리
    if len(st.session_state.choices_log) >= 5 and not result.get("chapter_clear", False) and not result.get("game_over", False):
        chapter_data = CHAPTERS[st.session_state.chapter]
        forced_ending_prompt = f"""
        {chapter_data['title']}
        {chapter_data['full_prompt']}

        지금은 반드시 '챕터 결말'을 출력해야 한다.
        선택지는 만들지 말고, 아래 중 하나로 끝내라:
        - 사건이 해결되면 chapter_clear=true
        - 주요 인물이 죽으면 game_over=true

        반드시 [요괴 퇴치 과정과 숨겨진 진실]을 반영하여 결말을 구성하라.
        """
        st.session_state.result = st.session_state.model.generate(SYSTEM_PROMPT, forced_ending_prompt)

        if st.session_state.result["game_over"]:
            st.session_state.game_over = True
        elif st.session_state.result.get("chapter_clear", False):
            st.session_state.chapter += 1
            st.session_state.choices_log = []
            if st.session_state.chapter < len(CHAPTERS):
                st.session_state.chapter_intro = True
                st.session_state.result = None
            else:
                ending_type = "원작엔딩"
                if any("새로운" in log for log in st.session_state.choices_log):
                    ending_type = "새로운엔딩"
                st.session_state.game_over = True
                st.session_state.result = {
                    "scene_summary": "모든 이야기가 끝났습니다.",
                    "narration": "🥳 모든 챕터를 완료했습니다.",
                    "choices": [],
                    "game_over": True,
                    "ending_type": ending_type,
                    "chapter_clear": True
                }
        st.rerun()
        return

    if result["choices"]:
        for choice in result["choices"]:
            if st.button(choice):
                st.session_state.choices_log.append(choice)
                followup = f"""
                이전 장면 요약: {result['scene_summary']}
                플레이어는 '{choice}'을 선택했다.
                그 결과 장면을 이어서 진행하라.
                """
                st.session_state.result = st.session_state.model.generate(SYSTEM_PROMPT, followup)

                if st.session_state.result["game_over"]:
                    st.session_state.game_over = True
                elif st.session_state.result.get("chapter_clear", False):
                    st.session_state.chapter += 1
                    if st.session_state.chapter < len(CHAPTERS):
                        st.session_state.chapter_intro = True
                        st.session_state.result = None
                    else:
                        ending_type = "원작엔딩"
                        if any("새로운" in log for log in st.session_state.choices_log):
                            ending_type = "새로운엔딩"
                        st.session_state.game_over = True
                        st.session_state.result = {
                            "scene_summary": "모든 이야기가 끝났습니다.",
                            "narration": "🥳 모든 챕터를 완료했습니다.",
                            "choices": [],
                            "game_over": True,
                            "ending_type": ending_type,
                            "chapter_clear": True
                        }
                st.rerun()


if st.session_state.page == "intro":
    intro_page()
elif st.session_state.page == "game":
    game_page()