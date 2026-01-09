import requests
import config 

TOKEN = config.MONO_TOKEN
headers = {"X-Token": TOKEN}

try:
    res = requests.get("https://api.monobank.ua/personal/client-info", headers=headers)
    
    if res.status_code == 401:
        print("❌ Помилка: Токен невірний або термін його дії закінчився.")
    else:
        data = res.json()
        if "jars" in data:
            print("✅ Ваші банки:")
            for jar in data["jars"]:
                print(f"Назва: {jar['title']} | ID: {jar['id']} | Баланс: {jar['balance']/100} грн")
        else:
            print("❌ Банки не знайдені.")
            print(data)
            
except Exception as e:
    print(f"Помилка: {e}")