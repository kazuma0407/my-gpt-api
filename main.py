from fastapi import FastAPI
from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Optional
import os

app = FastAPI()

# 認証ファイルのパス（my-gpt-api/credentials.json）
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

@app.get("/read-sheet")
def read_google_sheet(
    spreadsheet_id: str,
    sheet_name: str = "シート1",
    range_str: str = "A1:E100"
):
    # Google認証
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

    # Sheets APIクライアント
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()

    # データ取得
    result = sheet.values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!{range_str}"
    ).execute()

    values = result.get("values", [])

    return {"data": values}

@app.get("/analyze-report")
async def analyze_report():
    df = get_data_from_sheet()  # すでに作成した関数
    df.columns = df.iloc[0]
    df = df.drop(index=0)
    df = df.reset_index(drop=True)

    df["売上"] = df["売り上げ"].astype(int)
    df["広告費"] = df["広告費"].astype(int)
    df["利益"] = df["売上"] - df["広告費"] - df["仕入れ"].astype(int) - df["その他経費"].astype(int)

    total_sales = df["売上"].sum()
    total_profit = df["利益"].sum()
    ad_ratio = round(df["広告費"].sum() / total_sales * 100, 2)

    summary = f"""
    今月の売上は {total_sales} 円、利益は {total_profit} 円です。
    広告費率は {ad_ratio}% です。
    """

    # GPTでアドバイスを生成
    import openai
    openai.api_key = "sk-...hBgA"

    prompt = f"""
    以下はフリーランス事業者の月次売上データです：
    {summary}

    この内容をもとに、改善のアドバイスを箇条書きで3つほどください。
    広告費・仕入れ・経費の見直しや、売上向上のヒントがあればお願いします。
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    advice = response.choices[0].message["content"]
    return {"summary": summary, "advice": advice}

