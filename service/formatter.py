
# Nanoseconds to HH:MM:SS.MS
def format_time(nanoseconds):
    milliseconds = int(nanoseconds / 1000000)
    time_sec = int(milliseconds / 1000)

    # Вычисляем часы, минуты и секунды
    hours = int(time_sec // 3600)
    minutes = int((time_sec % 3600) // 60)
    seconds = int(time_sec % 60)

    milliseconds = milliseconds % 1000

    # Форматируем результат
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"