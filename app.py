
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Отзывы о ресторанах", layout="wide")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

def load_data(sheet_id, name):
    sheet = client.open_by_key(sheet_id).sheet1
    data = sheet.get_all_values()[1:]
    df = pd.DataFrame(data, columns=['timestamp', 'email', 'phone', 'date', 'dish', 'comment'])
    df['restaurant'] = name
    df['date'] = pd.to_datetime(df['date'], format="%d.%m.%Y", errors='coerce')
    return df[['date', 'dish', 'comment', 'restaurant']].dropna()

sheet_ids = {
    "23": "1S6p79vDhvgwY1ofudNGqjvgy8qbsQIOs2EqPtVcLppA",
    "25": "1ZHSelY3LLtemFf2HqT7zZ0UW6bUqKGdnemeVHLVJls0",
    "28": "1VlCHNTt0PQzt4YpEV59zhCrYL2djbS8XwgbpJGlX2WI"
}

df = pd.concat([load_data(sheet_id, name) for name, sheet_id in sheet_ids.items()])

st.title("Отзывы о ресторанах")
selected_restaurants = st.multiselect("Рестораны", options=df['restaurant'].unique(), default=df['restaurant'].unique())
selected_dish = st.text_input("Блюдо (поиск)")
selected_dates = st.date_input("Диапазон дат", [])

filtered = df[df['restaurant'].isin(selected_restaurants)]
if selected_dish:
    filtered = filtered[filtered['dish'].str.contains(selected_dish, case=False, na=False)]
if len(selected_dates) == 2:
    filtered = filtered[(filtered['date'] >= pd.to_datetime(selected_dates[0])) & (filtered['date'] <= pd.to_datetime(selected_dates[1]))]

st.write("Найдено отзывов:", len(filtered))
st.dataframe(filtered)
