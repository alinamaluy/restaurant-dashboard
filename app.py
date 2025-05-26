import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime

# --- Streamlit настройки страницы ---
st.set_page_config(page_title="Дашборд отзывов ресторанов", layout="wide")

# --- Заголовок дашборда ---
st.title("📊 Дашборд отзывов ресторанов")

# --- Подключение к Google Sheets через API ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    credentials = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
except Exception as e:
    st.error("Ошибка при авторизации. Убедитесь, что вы настроили `secrets` в Streamlit Cloud.")
    st.stop()

client = gspread.authorize(creds)

# --- Загрузка данных из Google Sheets ---
sheet = client.open_by_key("1ymTQHXs7rCH6giN8lyefioQeyXR2nToYLosTRcj5--s").worksheet("Sheet1")
data = sheet.get_all_records()
df = pd.DataFrame(data)

# --- Обработка данных ---
df['date'] = pd.to_datetime(df['date'], format="%d.%m.%Y", errors="coerce")

# --- Боковая панель с фильтрами ---
st.sidebar.header("Фильтры")

date_range = st.sidebar.date_input("Выберите диапазон дат", [df['date'].min(), df['date'].max()])

restaurants = st.sidebar.multiselect(
    "Выберите ресторан",
    options=df['source'].unique(),
    default=df['source'].unique()
)

all_dishes = df[df['source'].isin(restaurants)]['dish'].unique() if restaurants else df['dish'].unique()

selected_dishes = st.sidebar.multiselect(
    "Выберите блюдо",
    options=all_dishes,
    default=all_dishes
)

negative_filter = st.sidebar.checkbox("Показать только негативные отзывы", value=False)

# --- Фильтрация таблицы ---
filtered_df = df[
    (df['date'].dt.date >= date_range[0]) &
    (df['date'].dt.date <= date_range[1]) &
    (df['dish'].isin(selected_dishes)) &
    (df['source'].isin(restaurants))
]

# --- Определение негативных отзывов ---
filtered_df['Negative'] = filtered_df['comment'].str.lower().str.contains("плохо|ужасно|невкусно|жутко", na=False)

if negative_filter:
    filtered_df = filtered_df[filtered_df['Negative']]

# --- Формат даты для отображения ---
filtered_df['date'] = filtered_df['date'].dt.strftime("%d.%m.%Y")

# --- Вывод сводной таблицы ---
st.subheader("📋 Количество отзывов по блюдам")
dish_counts = filtered_df.groupby('dish').size().reset_index(name='Количество отзывов')
dish_counts = dish_counts.sort_values('Количество отзывов', ascending=False)
st.dataframe(dish_counts, use_container_width=True)

# --- Круговая диаграмма ---
st.subheader("🥧 Распределение отзывов по ресторанам")
restaurant_counts = filtered_df.groupby('source').size().reset_index(name='Количество')
fig_pie = px.pie(restaurant_counts, names='source', values='Количество', color='source')
st.plotly_chart(fig_pie, use_container_width=True)

# --- Линейный график по датам ---
st.subheader("📈 Динамика отзывов по датам")
date_counts = filtered_df.groupby('date').size().reset_index(name='Количество')
fig_line = px.line(date_counts, x='date', y='Количество', title="Отзывы по дням")
fig_line.update_xaxes(tickformat="%d.%m.%Y")
st.plotly_chart(fig_line, use_container_width=True)

# --- Подробная таблица ---
st.subheader("📝 Подробные отзывы")
st.dataframe(filtered_df[['date', 'comment', 'dish', 'source', 'Negative']], use_container_width=True)