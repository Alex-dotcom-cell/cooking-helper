# -*- coding: utf-8 -*-
import io
import re
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

NAME_SEARCH_PREFIXES = (
    "найди ", "найти ", "найдите ", "поиск ", "поищи ", "поискать ",
    "рецепт ", "рецепта ", "рецепты ", "рецептик ",
    "как приготовить ", "как сделать ", "как готовить ",
    "приготовить ", "приготовь ", "хочу ", "покажи ", "дай ",
)

for key, default in [
    ("p_input_text", ""),
    ("clear_counter", 0),
    ("voice_counter", 0),
    ("last_refresh", time.strftime("%H:%M:%S")),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ==================== ФУНКЦИИ ПОИСКА ====================

def is_name_search(text):
    t = text.lower().strip()
    return any(t.startswith(p) for p in NAME_SEARCH_PREFIXES)


def clean_query(text):
    t = text.lower().strip()
    for prefix in NAME_SEARCH_PREFIXES:
        if t.startswith(prefix):
            t = t[len(prefix):].strip()
            break
    return re.sub(r"[^а-яёa-z0-9 ]", "", t).strip()


def _words_match(q, n):
    """Проверяет, являются ли слова словоформами одного слова."""
    if not q or not n:
        return False
    if q == n:
        return True
    if len(q) >= 3 and q in n:
        return True
    if len(n) >= 3 and n in q:
        return True
    min_len = min(len(q), len(n))
    if min_len < 3:
        return False
    prefix_len = max(3, min_len - 2)
    return q[:prefix_len] == n[:prefix_len]


def find_by_name(query):
    """Поиск рецепта по названию с учётом словоформ."""
    q = clean_query(query)
    if not q:
        return []
    q_words = [w for w in q.split() if len(w) >= 3]
    if not q_words:
        return []
    results = []
    for recipe in recipes.RECIPES:
        name_clean = re.sub(r"[^а-яёa-z0-9 ]", "", recipe["name"].lower())
        if q in name_clean:
            score = 100 if q == name_clean else 95
            results.append((recipe, score))
            continue
        name_words = name_clean.split()
        matched = 0
        for qw in q_words:
            for nw in name_words:
                if _words_match(qw, nw):
                    matched += 1
                    break
        if matched:
            score = int(matched / len(q_words) * 100)
            if score >= 50:
                results.append((recipe, score))
    results.sort(key=lambda x: -x[1])
    return results


def render_recipe(recipe, percent=None, missing=None, have_products=None, expanded=False):
    title = recipe["name"]
    if percent is not None:
        title = f"{title} — {percent}%"
        if not missing:
            title += " ✅ всё есть"
    with st.expander(title, expanded=expanded):
        st.markdown(f"**⏱ {recipe['time']}  |  🍴 {recipe['servings']} порц.**")
        st.markdown("**📋 Ингредиенты:**")
        for ing in recipe["ingredients"]:
            if have_products is not None:
                mark = "✅" if recipes.normalize(ing) in have_products else "❌"
                st.markdown(f"- {mark} {ing}")
            else:
                st.markdown(f"- {ing}")
        if recipe.get("optional"):
            st.caption(f"Дополнительно: {', '.join(recipe['optional'])}")
        if missing:
            st.warning(f"⚠️ Не хватает: {', '.join(sorted(missing))}")
        st.markdown("**👨‍🍳 Приготовление:**")
        for n, step in enumerate(recipe["steps"], 1):
            st.markdown(f"{n}. {step}")


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
st.caption("Введите продукты или название блюда — получите рецепт")

c1, c2, _ = st.columns([1, 1, 4])
with c1:
    if st.button("🔄 Обновить", use_container_width=True):
        st.session_state.last_refresh = time.strftime("%H:%M:%S")
with c2:
    if st.button("🗑 Очистить", use_container_width=True):
        st.session_state.clear_counter += 1
        st.session_state.p_input_text = ""

# ==================== ГОЛОСОВОЙ ВВОД ====================
st.markdown("### 🎤 Голосовой ввод")
st.caption("Скажите: «*яйца, помидоры, лук*» — или «*найди борщ*». Запись остановится кнопкой.")

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
    "🥕 Ваши продукты (или название блюда):",
    value=st.session_state.p_input_text,
    key=f"p_input_{st.session_state.clear_counter}_{st.session_state.voice_counter}",
    placeholder="яйца, помидоры, лук  ИЛИ  найди борщ",
    help="Введите продукты через запятую — или напишите «найди <блюдо>»",
)

if products_input != st.session_state.p_input_text:
    st.session_state.p_input_text = products_input

# ==================== ПОИСК ====================
if products_input.strip():
    if is_name_search(products_input):
        # === ПОИСК ПО НАЗВАНИЮ ===
        query_clean = clean_query(products_input)
        st.info(f"🔍 Ищу блюдо: **{query_clean}**")

        results = find_by_name(products_input)

        if not results:
            st.error(f"😔 Блюдо «{query_clean}» не найдено.")
            st.caption("Попробуйте другое название или проверьте написание.")
        elif len(results) == 1:
            recipe, score = results[0]
            render_recipe(recipe, expanded=True)
        else:
            st.success(f"Найдено рецептов: **{len(results)}**")
            for i, (recipe, score) in enumerate(results, 1):
                render_recipe(recipe, expanded=(i == 1))
    else:
        # === ПОИСК ПО ПРОДУКТАМ ===
        products = recipes.split_products(products_input)
        if not products:
            st.warning("Не удалось распознать продукты. Попробуйте: яйца, помидоры, лук")
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
                    render_recipe(recipe, percent=percent, missing=missing,
                                  have_products=products, expanded=(i == 1))
else:
    st.info("👇 Введите продукты или название блюда — и я подберу рецепты")
    st.markdown("**Примеры:**")
    st.markdown("- `яйца, помидоры, лук` — поиск по продуктам")
    st.markdown("- `найди борщ` — найти блюдо по названию")
    st.markdown("- `приготовить тирамису` — рецепт конкретного блюда")
    st.markdown("- `как сделать плов` — пошаговая инструкция")
