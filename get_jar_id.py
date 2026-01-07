import requests

TOKEN = "ui18988NC2nlNKLATHjwRQJ_c41J9_uFARIhYCx3y2RI"
headers = {"X-Token": TOKEN}

try:
    res = requests.get("https://api.monobank.ua/personal/client-info", headers=headers)
    data = res.json()
    if "jars" in data:
        print("✅ Ваші банки:")
        for jar in data["jars"]:
            print(f"Назва: {jar['title']} | ID: {jar['id']} | Баланс: {jar['balance']/100} грн")
    else:
        print("❌ Банки не знайдені або токен невірний.")
        print(data)
except Exception as e:
    print(f"Помилка: {e}")