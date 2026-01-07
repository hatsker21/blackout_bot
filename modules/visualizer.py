from PIL import Image, ImageDraw, ImageFont
import io
import os
from datetime import datetime

def get_font(size):
    """Шукає шрифт, враховуючи структуру папок проекту"""
    # Отримуємо шлях до папки, де лежить цей файл (modules/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Переходимо на рівень вище, в корінь проекту
    project_root = os.path.dirname(current_dir)
    
    # Складаємо шлях до шрифту в корені (де лежить main.py та arial.ttf)
    font_path = os.path.join(project_root, "arial.ttf")
    
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    
    # Запасний варіант для Windows
    win_font = "C:\\Windows\\Fonts\\arial.ttf"
    if os.path.exists(win_font):
        return ImageFont.truetype(win_font, size)
    
    # Якщо нічого не знайдено
    print("WARNING: ШРИФТ НЕ ЗНАЙДЕНО! Будуть квадратики.")
    return ImageFont.load_default()

def generate_schedule_image(queue_id, schedule_str):
    # Налаштування розмірів
    W, H = 1100, 500 
    bar_x, bar_y = 60, 180
    bar_w, bar_h = 980, 140
    
    COLOR_BG = (255, 255, 255)
    COLOR_POWER = (76, 175, 80)     # Зелений
    COLOR_BLACKOUT = (244, 67, 54)  # Червоний
    COLOR_GRID = (180, 180, 180)    # Сітка
    COLOR_NOW = (33, 150, 243)      # Синя стрілка

    img = Image.new('RGB', (W, H), color=COLOR_BG)
    draw = ImageDraw.Draw(img)

    # Завантажуємо шрифти
    font_main = get_font(42)
    font_small = get_font(24)
    font_hours = get_font(20)

    # Заголовок та Дата
    draw.text((60, 40), f"Графік відключень: Черга {queue_id}", fill=(0,0,0), font=font_main)
    draw.text((60, 100), f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}", fill=(80,80,80), font=font_small)

    # 1. Малюємо зелену основу (світло є)
    draw.rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], fill=COLOR_POWER)

    # 2. Малюємо червоні зони (відключення)
    if schedule_str and "відсутній" not in schedule_str:
        intervals = schedule_str.replace('.', ':').split(',')
        for interval in intervals:
            try:
                parts = interval.strip().split('-')
                if len(parts) != 2: continue
                
                h_start = int(parts[0].strip().split(':')[0]) + int(parts[0].strip().split(':')[1])/60
                h_end = int(parts[1].strip().split(':')[0]) + int(parts[1].strip().split(':')[1])/60
                
                x1 = bar_x + (h_start * (bar_w / 24))
                x2 = bar_x + (h_end * (bar_w / 24))
                draw.rectangle([x1, bar_y, x2, bar_y + bar_h], fill=COLOR_BLACKOUT)
            except: continue

    # 3. ПОГОДИННА СІТКА ТА ЦИФРИ (0-24)
    for h in range(25):
        x = bar_x + (h * (bar_w / 24))
        
        # Малюємо вертикальну лінію для кожної години
        line_color = (100, 100, 100) if h % 6 == 0 else COLOR_GRID
        draw.line([x, bar_y - 5, x, bar_y + bar_h + 10], fill=line_color, width=2 if h % 6 == 0 else 1)
        
        # Малюємо цифру години під кожною лінією
        txt = f"{h:02d}"
        tw = draw.textlength(txt, font=font_hours)
        draw.text((x - tw/2, bar_y + bar_h + 20), txt, fill=(0, 0, 0), font=font_hours)

    # 4. ПОКАЖЧИК "ЗАРАЗ"
    now = datetime.now()
    current_float_h = now.hour + now.minute/60
    x_now = bar_x + (current_float_h * (bar_w / 24))
    
    # Синя лінія через весь графік
    draw.line([x_now, bar_y - 30, x_now, bar_y + bar_h + 15], fill=COLOR_NOW, width=4)
    # Трикутник зверху
    draw.polygon([x_now-12, bar_y-45, x_now+12, bar_y-45, x_now, bar_y-30], fill=COLOR_NOW)
    # Текст "ЗАРАЗ"
    draw.text((x_now - 35, bar_y - 75), "ЗАРАЗ", fill=COLOR_NOW, font=font_hours)

    # 5. ЛЕГЕНДА
    draw.rectangle([60, 440, 95, 465], fill=COLOR_POWER)
    draw.text((105, 438), "Світло є", fill=(0,0,0), font=font_small)
    draw.rectangle([280, 440, 315, 465], fill=COLOR_BLACKOUT)
    draw.text((325, 438), "Відключення", fill=(0,0,0), font=font_small)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf