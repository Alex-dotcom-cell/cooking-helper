# -*- coding: utf-8 -*-
"""Веб-версия кулинарного помощника на Streamlit."""

import importlib
import sys
import time

import streamlit as st

# Сбрасываем кэш модулей — чтобы правки recipes.py подхватывались при обновлении
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

# Инициализация состояния
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.strftime("%H:%M:%S")
if "products_input" not in st.session_state:
    st.session_state.products_input = ""

# ==================== SIDEBAR ====================

with st.sidebar:
    st.header("🎛 Управление")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Обновить", use_container_width=True, type="primary"):
            st.session_state.last_refresh = time.strftime("%H:%M:%S")
            st.rerun()
    with col2:
        if st.button("🗑 Очистить", use_container_width=True):
            st.session_state.products_input = ""
            st.rerun()

    st.divider()

    st.subheader("Категория")
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

# Кнопки сверху (дублирующие) — для удобства на телефоне
top_col1, top_col2, _ = st.columns([1, 1, 4])
with top_col1:
    if st.button("🔄", help="Обновить", use_container_width=True):
        st.session_state.last_refresh = time.strftime("%H:%M:%S")
        st.rerun()
with top_col2:
    if st.button("🗑", help="Очистить", use_container_width=True):
        st.session_state.products_input = ""
        st.rerun()

mode = None if selected == "все" else selected

products_input = st.text_input(
    "🥕 Ваши продукты (через запятую):",
    key="products_input",
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
    "подождите ~1 минуту и нажмите **🔄 Обновить** — новые рецепты появятся."
)
