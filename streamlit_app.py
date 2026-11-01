# -*- coding: utf-8 -*-
"""Веб-версия кулинарного помощника на Streamlit."""

import sys
import time

import streamlit as st

# Сброс кэша модулей — чтобы правки рецептов подхватывались
for _mod in list(sys.modules.keys()):
    if _mod in ("recipes", "sweet_recipes", "drinks_recipes",
                "preserves_recipes", "world_recipes",
                "sauces_recipes", "bakery_recipes"):
        del sys.modules[_mod]

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

# Состояние
if "clear_counter" not in st.session_state:
    st.session_state.clear_counter = 0
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.strftime("%H:%M:%S")

# ==================== SIDEBAR (без кнопок!) ====================

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

# Кнопки сверху — БЕЗ st.columns, чтобы не было бага
col_refresh, col_clear, col_spacer = st.columns([1, 1, 4])

with col_refresh:
    if st.button("🔄 Обновить", use_container_width=True):
        st.session_state.last_refresh = time.strftime("%H:%M:%S")
        st.rerun()

with col_clear:
    if st.button("🗑 Очистить", use_container_width=True):
        st.session_state.clear_counter += 1
        st.rerun()

mode = None if selected == "все" else selected

# Ключ зависит от счётчика — при "Очистить" виджет пересоздаётся пустым
products_input = st.text_input(
    "🥕 Ваши продукты (через запятую):",
    key=f"products_input_{st.session_state.clear_counter}",
    placeholder="яйца, помидоры, лук, сыр",
    help="Нажмите Enter после ввода",
)

if products_input.strip():
    products = recipes.split_products(products_input)
    if not products:
        st.warning("Не удалось распознать продукты. Попробуйте: яйца, помидоры, лук")
    else:
        matches = recipes.find_matches(products, mode)
        best = [m for m in matches if m[1] >= 50][:10]
        if not best:
            best = matches[:5]

        if not best:
            st.error("😔 Ничего не нашлось. Попробуйте другие продукты или другую категорию.")
        else:
            st.success(f"🔎 Найдено рецептов: **{len(best)}**")
            for i, (recipe, percent, missing) in enumerate(best, 1):
                if missing:
                    label = f"{i}. {recipe['name']} — {percent}%"
                else:
                    label = f"{i}. {recipe['name']} — {percent}% ✅ всё есть"

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
    st.info("👇 Введите продукты в поле выше — и я подберу рецепты")
    st.markdown("**Доступные категории:**")
    for key, label in CATEGORIES.items():
        st.markdown(f"- {label}")

st.divider()
st.caption(
    "💡 **Совет:** после `git push` с новыми рецептами "
    "подождите ~1 минуту и нажмите **🔄 Обновить**."
)
