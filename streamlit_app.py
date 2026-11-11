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

for _r in recipes.RECIPES:
    if not _r.get("servings"):
        _r["servings"] = 2

# Считаем количество рецептов в каждой категории
_cat_counts = {}
for _r in recipes.RECIPES:
    _c = _r.get("category", "основное")
    _cat_counts[_c] = _cat_counts.get(_c, 0) + 1

CATEGORIES = {
    "все":         f"📖 Все рецепты ({len(recipes.RECIPES)})",
    "основное":    f"🍲 Обычные блюда ({_cat_counts.get('основное', 0)})",
    "салаты":      f"🥗 Салаты ({_cat_counts.get('салаты', 0)})",
    "сладкое":     f"🍰 Сладкое ({_cat_counts.get('сладкое', 0)})",
    "напитки":     f"🥤 Напитки ({_cat_counts.get('напитки', 0)})",
    "заготовки":   f"🥗 Заготовки ({_cat_counts.get('заготовки', 0)})",
    "кухни мира":  f"🌍 Кухни мира ({_cat_counts.get('кухни мира', 0)})",
    "соусы":       f"🥩 Соусы ({_cat_counts.get('соусы', 0)})",
    "выпечка":     f"🧁 Выпечка ({_cat_counts.get('выпечка', 0)})",
}

NAME_SEARCH_PREFIXES = (
    "найди ", "найти ", "найдите ", "поиск ", "поищи ", "поискать ",
    "рецепт ", "рецепта ", "рецепты ", "рецептик ",
    "как приготовить ", "как сделать ", "как готовить ",
    "приготовить ", "приготовь ", "хочу ", "покажи ", "дай ",
)

# Триггеры для категории "салаты"
SALAD_ONLY_COMMANDS = ("салат", "салаты", "салатик", "салатика")
SALAD_SEARCH_PREFIXES = ("сделать салат ", "хочу салат ", "салат из ", "салат с ", "салат ")

MANUAL_QUANTITIES = {
    "Борщ": {"мясо": "500 г", "свёкла": "2 шт", "капуста": "300 г",
             "картошка": "4 шт", "морковь": "1 шт", "лук": "2 шт"},
    "Яичница с помидорами и луком": {"яйца": "4 шт", "помидоры": "3 шт", "лук": "1 шт"},
    "Омлет с сыром": {"яйца": "4 шт", "молоко": "50 мл", "сыр": "100 г"},
    "Шарлотка с яблоками": {"яблоки": "4 шт", "яйца": "4 шт", "мука": "200 г", "сахар": "200 г"},
    "Плов с курицей": {"рис": "2 стакана", "курица": "500 г", "морковь": "2 шт", "лук": "2 шт"},
    "Тирамису": {"маскарпоне": "250 г", "яйца": "4 шт", "сахар": "4 ст. л.", "кофе": "200 мл"},
    "Паста карбонара": {"макароны": "200 г", "яйца": "2 шт", "сыр": "50 г", "чеснок": "1 зубч."},
    "Творожная запеканка": {"творог": "500 г", "яйца": "3 шт", "сахар": "3 ст. л.", "манка": "3 ст. л."},
    "Медовик": {"мёд": "3 ст. л.", "мука": "3 стакана", "яйца": "2 шт", "сахар": "1 стакан", "сметана": "500 г"},
    "Шоколадный кекс в кружке": {"мука": "4 ст. л.", "какао": "2 ст. л.", "сахар": "3 ст. л.", "молоко": "4 ст. л.", "масло": "2 ст. л."},
    "Сырники из творога": {"творог": "400 г", "яйца": "1 шт", "мука": "3 ст. л."},
    "Картофельное пюре": {"картошка": "6-7 шт", "молоко": "100 мл", "масло сливочное": "50 г"},
    "Куриный суп с картошкой и морковью": {"курица": "500 г", "картошка": "3-4 шт", "морковь": "1 шт", "лук": "1 шт"},
    "Крем-брюле": {"сливки": "400 мл", "яйца": "4 желтка", "сахар": "4 ст. л."},
    "Курица с картошкой в духовке": {"курица": "800 г", "картошка": "6-7 шт", "лук": "2 шт"},
    "Салат Оливье": {"картошка": "3-4 шт", "морковь": "1-2 шт", "яйца": "3-4 шт", "колбаса": "200-300 г", "огурцы солёные": "3-4 шт", "горошек": "400 г (1 банка)", "майонез": "200 г"},
    "Паста с песто": {"макароны": "200 г", "базилик": "50 г", "чеснок": "2 зубчика", "сыр": "50 г", "орехи": "30 г", "масло оливковое": "100 мл"},
    "Лагман узбекский": {"мясо": "500 г", "лапша": "300 г", "морковь": "2 шт", "лук": "2 шт", "помидоры": "3 шт", "перец": "1 шт", "картошка": "3 шт", "чеснок": "4 зубчика", "масло растительное": "100 мл"},
    "Салат из свежей капусты с морковью": {"капуста": "400 г", "морковь": "1 шт", "лук": "1 шт", "масло растительное": "2 ст. л."},
    "Салат «Витаминный» из капусты и яблока": {"капуста": "300 г", "морковь": "1 шт", "яблоки": "1 шт", "лимон": "0,5 шт", "масло растительное": "2 ст. л."},
    "Салат из капусты с огурцом": {"капуста": "400 г", "огурцы": "2 шт", "лук": "1 шт", "масло растительное": "2 ст. л."},
    "Морковь по-корейски": {"морковь": "500 г", "чеснок": "3 зубчика", "масло растительное": "4 ст. л.", "уксус": "1 ст. л.", "сахар": "1 ст. л."},
    "Салат «Щётка» из капусты и свёклы": {"капуста": "300 г", "морковь": "1 шт", "свёкла": "1 шт", "лук": "0,5 шт", "масло оливковое": "2 ст. л."},
    "Салат из свежих овощей с луком": {"огурцы": "2 шт", "помидоры": "3 шт", "лук": "1 шт", "перец": "1 шт"},
    "Салат «Весенний» с редисом и яйцом": {"редис": "200 г", "огурцы": "2 шт", "яйца": "2 шт", "зелень": "1 пучок"},
    "Салат из капусты с кукурузой и сухариками": {"капуста": "300 г", "кукуруза": "200 г", "сухарики": "100 г", "майонез": "100 г", "морковь": "1 шт"},
    "Салат «Цезарь» с курицей": {"курица": "300 г", "салат": "100 г", "хлеб": "2 ломтика", "сыр": "50 г", "майонез": "100 г"},
    "Салат «Мимоза»": {"рыба консервированная": "1 банка", "яйца": "4 шт", "картошка": "3 шт", "морковь": "2 шт", "лук": "1 шт", "майонез": "150 г"},
    "Салат из моркови с чесноком и сыром": {"морковь": "3 шт", "чеснок": "2 зубчика", "сыр": "100 г", "майонез": "100 г"},
    "Салат из капусты и огурца с уксусом": {"капуста": "400 г", "огурцы": "2 шт", "морковь": "1 шт", "уксус": "1 ст. л."},
    "Салат из огурцов и помидоров": {"огурцы": "2 шт", "помидоры": "3 шт", "лук": "1 шт", "зелень": "1 пучок"},
    "Греческий салат": {"помидоры": "3 шт", "огурцы": "2 шт", "сыр": "150 г", "лук": "1 шт", "оливки": "50 г"},
    "Винегрет": {"свёкла": "1 шт", "морковь": "2 шт", "картошка": "3 шт", "огурцы солёные": "2 шт", "лук": "1 шт"},
}


def get_quantity(ingredient, recipe):
    manual = MANUAL_QUANTITIES.get(recipe["name"], {})
    if ingredient in manual:
        return manual[ingredient]
    ing = ingredient.lower()
    steps_text = " ".join(recipe["steps"]).lower()
    stem = re.sub(r"(ы|и|а|я|у|ю|е|ой|ей|ам|ям|ов|ев|ах|ях)$", "", ing)
    if len(stem) < 3:
        stem = ing
    for m in re.finditer(re.escape(stem), steps_text):
        start = max(0, m.start() - 60)
        end = min(len(steps_text), m.end() + 60)
        context = steps_text[start:end]
        patterns = [
            rf"\(?\s*(\d+(?:[.,]\d+)?(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?)\s*(г|кг|мл|л|шт\.?|ст\.?\s*л\.?|ч\.?\s*л\.?|стакан[а-яё]*|зубч[а-яё]*|пуч[а-яё]*)\s*\)?\s*{re.escape(stem)}",
            rf"{re.escape(stem)}[а-яё]*\s*\(?\s*(\d+(?:[.,]\d+)?(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?)\s*(г|кг|мл|л|шт\.?|ст\.?\s*л\.?|ч\.?\s*л\.?|стакан[а-яё]*|зубч[а-яё]*|пуч[а-яё]*)\s*\)?",
        ]
        for p in patterns:
            m2 = re.search(p, context)
            if m2:
                return f"{m2.group(1)} {m2.group(2)}".strip()
    return None


def _fmt(num):
    return str(int(num)) if num == int(num) else f"{num:.1f}".rstrip("0").rstrip(".")


def scale_quantity(qty_str, coeff):
    if not qty_str or coeff == 1:
        return qty_str
    m = re.match(r"(\d+(?:[.,]\d+)?)\s*[-–]\s*(\d+(?:[.,]\d+)?)\s*(.*)", qty_str)
    if m:
        lo = float(m.group(1).replace(",", ".")) * coeff
        hi = float(m.group(2).replace(",", ".")) * coeff
        return f"{_fmt(lo)}-{_fmt(hi)} {m.group(3)}".strip()
    m = re.match(r"(\d+(?:[.,]\d+)?)\s*(.*)", qty_str)
    if m:
        num = float(m.group(1).replace(",", ".")) * coeff
        return f"{_fmt(num)} {m.group(2)}".strip()
    return qty_str


# ============================================================
# РАСПОЗНАВАНИЕ КОМАНД
# ============================================================
def is_name_search(text):
    t = text.lower().strip()
    return any(t.startswith(p) for p in NAME_SEARCH_PREFIXES)


def is_salad_only_command(text):
    return text.lower().strip() in SALAD_ONLY_COMMANDS


def is_salad_search(text):
    t = text.lower().strip()
    return any(t.startswith(p) for p in SALAD_SEARCH_PREFIXES) and len(t.split()) > 2


def extract_salad_products(text):
    t = text.lower().strip()
    for prefix in SALAD_SEARCH_PREFIXES:
        if t.startswith(prefix):
            return t[len(prefix):].strip()
    return t


def clean_query(text):
    t = text.lower().strip()
    for prefix in NAME_SEARCH_PREFIXES:
        if t.startswith(prefix):
            t = t[len(prefix):].strip()
            break
    return re.sub(r"[^а-яёa-z0-9 ]", "", t).strip()


def _words_match(q, n):
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
            results.append((recipe, 100 if q == name_clean else 95))
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


def render_recipe(recipe, percent=None, missing=None, have_products=None,
                  expanded=False, uid=0):
    base_servings = int(recipe.get("servings", 2))
    title = recipe["name"]
    if percent is not None:
        title = f"{title} — {percent}%"
        if not missing:
            title += " ✅ всё есть"

    with st.expander(title, expanded=expanded):
        col_t, col_s = st.columns(2)
        with col_t:
            st.metric("⏱ Время", recipe.get("time", "—"))
        with col_s:
            st.metric("🍴 Порций (по рецепту)", base_servings)

        st.markdown("**⚖️ Готовлю на (порций):**")
        new_servings = st.number_input(
            "Порций:", min_value=1, max_value=100,
            value=base_servings, step=1,
            key=f"serv_{uid}_{recipe['name']}",
            label_visibility="collapsed",
        )
        coeff = new_servings / base_servings
        if coeff == 1:
            st.caption(f"✅ Рецепт на **{base_servings} порц.** — количества без изменений.")
        else:
            st.info(f"💡 Коэффициент **× {coeff:.2f}** (было {base_servings} → стало {new_servings} порц.)")

        st.markdown("**📋 Ингредиенты:**")
        for ing in recipe["ingredients"]:
            qty = get_quantity(ing, recipe)
            if qty:
                if coeff != 1:
                    scaled = scale_quantity(qty, coeff)
                    qty_str = f"**{scaled}** *(было {qty})*"
                else:
                    qty_str = f"**{qty}**"
            else:
                qty_str = "*по вкусу*"

            if have_products is not None:
                mark = "✅" if recipes.normalize(ing) in have_products else "❌"
                st.markdown(f"- {mark} {qty_str} — **{ing}**")
            else:
                st.markdown(f"- {qty_str} — **{ing}**")

        if recipe.get("optional"):
            st.caption(f"Дополнительно: {', '.join(recipe['optional'])}")
        if missing:
            st.warning(f"⚠️ Не хватает: {', '.join(sorted(missing))}")

        st.markdown("**👨‍🍳 Приготовление:**")
        for n, step in enumerate(recipe["steps"], 1):
            st.markdown(f"{n}. {step}")


# ============================================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================================
for key, default in [
    ("p_input_text", ""),
    ("clear_counter", 0),
    ("voice_counter", 0),
    ("last_refresh", time.strftime("%H:%M:%S")),
]:
    if key not in st.session_state:
        st.session_state[key] = default

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

st.markdown("### 🎤 Голосовой ввод")
st.caption("Скажите: «*яйца, помидоры, лук*» или «*салат капуста, морковь*».")

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

mode = None if selected == "все" else selected

products_input = st.text_input(
    "🥕 Ваши продукты (или название блюда):",
    value=st.session_state.p_input_text,
    key=f"p_input_{st.session_state.clear_counter}_{st.session_state.voice_counter}",
    placeholder="яйца, помидоры, лук  ИЛИ  найди борщ  ИЛИ  салат капуста, морковь",
)

if products_input != st.session_state.p_input_text:
    st.session_state.p_input_text = products_input

# ============================================================
# ОБРАБОТКА ВВОДА
# ============================================================
if products_input.strip():
    txt = products_input.strip()

    # 1. Просто "салат" / "салаты" — показать все салаты
    if is_salad_only_command(txt):
        salads = [r for r in recipes.RECIPES if r.get("category") == "салаты"]
        st.success(f"🥗 Все салаты: **{len(salads)}**")
        for i, recipe in enumerate(salads, 1):
            render_recipe(recipe, expanded=(i == 1), uid=i)

    # 2. "салат капуста, морковь" — искать по продуктам ТОЛЬКО в салатах
    elif is_salad_search(txt):
        salad_products = extract_salad_products(txt)
        products = recipes.split_products(salad_products)
        if not products:
            st.warning("Укажите продукты после слова «салат». Например: `салат капуста, морковь`")
        else:
            st.info(f"🥗 Ищу салаты из: **{', '.join(sorted(products))}**")
            matches = recipes.find_matches(products, "салаты")
            best = [m for m in matches if m[1] >= 30][:10]
            if not best:
                st.error("😔 Салатов из этих продуктов не нашлось.")
            else:
                st.success(f"Найдено: **{len(best)}**")
                for i, (recipe, percent, missing) in enumerate(best, 1):
                    render_recipe(recipe, percent=percent, missing=missing,
                                  have_products=products, expanded=(i == 1), uid=i)

    # 3. Поиск по названию блюда ("найди борщ")
    elif is_name_search(txt):
        query_clean = clean_query(txt)
        st.info(f"🔍 Ищу блюдо: **{query_clean}**")
        results = find_by_name(txt)
        if not results:
            st.error(f"😔 Блюдо «{query_clean}» не найдено.")
        elif len(results) == 1:
            recipe, _ = results[0]
            render_recipe(recipe, expanded=True, uid=0)
        else:
            st.success(f"Найдено рецептов: **{len(results)}**")
            for i, (recipe, _) in enumerate(results, 1):
                render_recipe(recipe, expanded=(i == 1), uid=i)

    # 4. Обычный поиск по продуктам
    else:
        products = recipes.split_products(txt)
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
                    render_recipe(recipe, percent=percent, missing=missing,
                                  have_products=products, expanded=(i == 1), uid=i)
else:
    # Показываем рецепты: либо конкретной категории, либо ВСЕ если selected == "все"
    if mode:
        cat_recipes = [r for r in recipes.RECIPES if r.get("category") == mode]
        header = f"{CATEGORIES[mode]} — **{len(cat_recipes)}** рецептов"
    else:
        cat_recipes = list(recipes.RECIPES)
        header = f"📖 Все рецепты — **{len(cat_recipes)}**"

    if cat_recipes:
        st.success(header)
        st.caption("Нажмите на блюдо, чтобы раскрыть рецепт.")
        for i, recipe in enumerate(cat_recipes, 1):
            render_recipe(recipe, expanded=False, uid=f"cat_{selected}_{i}")
    else:
        st.info(f"В категории {CATEGORIES[selected]} пока нет рецептов.")
        if cat_recipes:
            st.success(f"{CATEGORIES[mode]} — **{len(cat_recipes)}** рецептов")
            st.caption("Нажмите на блюдо, чтобы раскрыть рецепт.")
            for i, recipe in enumerate(cat_recipes, 1):
                render_recipe(recipe, expanded=False, uid=f"cat_{mode}_{i}")
        else:
            st.info(f"В категории {CATEGORIES[mode]} пока нет рецептов.")
