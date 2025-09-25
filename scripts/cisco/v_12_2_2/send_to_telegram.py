import requests

# 從 @BotFather 拿到的 Token
TOKEN = "7978003158:AAHv2080OBxazfxSRvKhU-Ihx5rWORrzUm4"

# 你的 chat_id （用 getUpdates 拿到）
CHAT_ID = "8216101171"


def notify_telegram(msg: str):
    """發送訊息到 Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    resp = requests.post(url, data=payload)

    if resp.status_code == 200:
        print(f"訊息已送出 ✔ ({msg})")
    else:
        print("失敗:", resp.text)


if __name__ == "__main__":
    notify_telegram("Manual run ✅")