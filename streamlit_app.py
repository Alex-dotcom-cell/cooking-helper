# -*- coding: utf-8 -*-
import io
import time
import streamlit as st
import speech_recognition as sr
import recipes

st.set_page_config(
    page_title="Кулинарный помощник",
    page_icon="🍳",
    layout="centered",
    initial_sidebar_state="expanded",
)

CATEGORIES = {
    "все": "📖 Все рецепты",
    "основное": "🍲 Обычные блюда",
    "сладкое": "🍰 Сладкое",
    "напитки": "🥤 Напитки",
    "заготовки": "🥗 Заготовки",
    "кухни мира": "🌍 Кухни мира",
    "соусы": "🥩 Соусы",
    "выпечка": "🧁 Выпечка",
}

if "p_input_text" not in st.session_state:
    st.session_state.p_input_text = ""
if "clear_counter" not in st.session_state:
    st.session_state.clear_counter = 0
if "voice_counter" not in st.session_state:
    st.session_state.voice_counter = 0
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.strftime("%H:%M:%S")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("Категория")
    selected = st.radio(
        "Выберите:",
        list(CATEGORIES.keys()),
        format_func=lambda x: CATEGORIES[x],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(f"📚 В базе: **{len(recipes.RECIPES)}** рецептов")
    st.caption(f"🕐 Обновлено: **{st.session_state.last_refresh}**")

# ==================== ОСНОВНАЯ ЧАСТЬ ====================
st.title("🍳 Кулинарный помощник")
st.caption("Введите продукты — получите рецепты с пошаговой инструкцией")

c1, c2, _ = st.columns([1, 1, 4])
with c1:
    if st.button("🔄 Обновить", use_container_width=True):
        st.session_state.last_refresh = time.strftime("%H:%M:%S")
with c2:
    if st.button("🗑 Очистить", use_container_width=True):
        st.session_state.clear_counter += 1
        st.session_state.p_input_text = ""

# ==================== ГОЛОСОВОЙ ВВОД (нативный) ====================
st.markdown("### 🎤 Голосовой ввод")
st.caption("Нажмите на микрофон, перечислите продукты (например: *яйца, помидоры, лук*). Запись остановится по кнопке.")

# Встроенный компонент Streamlit 1.39+
audio_value = st.audio_input("Записать голос", key=f"audio_{st.session_state.voice_counter}")

if audio_value is not None:
    try:
        r = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_value.getvalue())) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language="ru-RU")
        st.session_state.p_input_text = text
        st.session_state.voice_counter += 1
        st.success(f"✅ Распознано: **{text}**")
        st.rerun()
    except sr.UnknownValueError:
        st.error("😔 Не удалось разобрать речь. Попробуйте сказать чётче.")
    except sr.RequestError as e:
        st.error(f"⚠️ Ошибка сервиса распознавания: {e}")
    except Exception as e:
        st.error(f"⚠️ Ошибка: {e}")

# ==================== ПОЛЕ ВВОДА ====================
mode = None if selected == "все" else selected

products_input = st.text_input(
    "🥕 Ваши продукты (через запятую):",
    value=st.session_state.p_input_text,
    key=f"p_input_{st.session_state.clear_counter}_{st.session_state.voice_counter}",
    placeholder="яйца, помидоры, лук, сыр",
    help="Нажмите Enter после ввода",
)

if products_input != st.session_state.p_input_text:
    st.session_state.p_input_text = products_input

# ==================== ПОИСК РЕЦЕПТОВ ====================
if products_input.strip():
    products = recipes.split_products(products_input)
    if not products:
        st.warning("Не удалось распознать продукты.")
    else:
        matches = recipes.find_matches(products, mode)
        best = [m for m in matches if m[1] >= 50][:10]
        if not best:
            best = matches[:5]

        if not best:
            st.error("😔 Ничего не нашлось. Попробуйте другие продукты.")
        else:
            st.success(f"🔎 Найдено рецептов: **{len(best)}**")
            for i, (recipe, percent, missing) in enumerate(best, 1):
                label = f"{i}. {recipe['name']} — {percent}%"
                if not missing:
                    label += " ✅ всё есть"

                with st.expander(label, expanded=(i == 1)):
                    st.markdown(f"**⏱ {recipe['time']}  |  🍴 {recipe['servings']} порц.**")

                    st.markdown("**📋 Ингредиенты:**")
                    for ing in recipe["ingredients"]:
                        if recipes.normalize(ing) in products:
                            st.markdown(f"- ✅ {ing}")
                        else:
                            st.markdown(f"- ❌ {ing}")

                    if recipe["optional"]:
                        have_opt = [
                            o for o in recipe["optional"]
                            if recipes.normalize(o) in products
                        ]
                        if have_opt:
                            st.caption(f"У вас есть для вкуса: {', '.join(have_opt)}")

                    if missing:
                        st.warning(f"⚠️ Не хватает: {', '.join(sorted(missing))}")

                    st.markdown("**👨‍🍳 Приготовление:**")
                    for n, step in enumerate(recipe["steps"], 1):
                        st.markdown(f"{n}. {step}")
else:
    st.info("👇 Введите продукты в поле выше (или используйте микрофон) — и я подберу рецепты")
