from datetime import datetime

def get_current_status(schedule_str):
    """
    Аналізує графік і визначає поточний стан світла.
    """
    if not schedule_str or "відсутній" in schedule_str:
        return "⚪️ **Статус невідомий**", "Будь ласка, перевірте актуальність графіка."

    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    # Розбиваємо рядок на часові інтервали
    intervals = schedule_str.replace('.', ':').split(',')
    
    is_blackout = False
    next_event_time = None
    all_starts = []

    for interval in intervals:
        try:
            parts = interval.strip().split('-')
            if len(parts) != 2: continue
            
            start_time = parts[0].strip()
            end_time = parts[1].strip()
            all_starts.append(start_time)

            # Перевірка: чи ми в періоді відключення зараз
            if start_time <= current_time < end_time:
                is_blackout = True
                next_event_time = end_time
                break
            
            # Пошук найближчого майбутнього відключення
            if start_time > current_time:
                if next_event_time is None or start_time < next_event_time:
                    next_event_time = start_time
        except:
            continue

    if is_blackout:
        status = "🔴 **Світло відсутнє**"
        timer = f"⏳ Світло має з'явитися о: **{next_event_time}**"
    else:
        status = "🟢 **Світло є**"
        if next_event_time:
            timer = f"⏳ Наступне вимкнення: **{next_event_time}**"
        else:
            timer = "✅ Вимкнень до кінця доби не заплановано"

    return status, timer