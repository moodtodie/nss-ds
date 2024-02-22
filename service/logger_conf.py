import logging
import colorlog

logging_level = logging.DEBUG

# Создание обработчика для вывода логов в консоль с цветовой коррекцией
console_handler = colorlog.StreamHandler()
console_handler.setLevel(logging_level)

# Настройка форматтера для логов с цветовой коррекцией
formatter = colorlog.ColoredFormatter(
    '%(asctime)s  %(name)s  [%(log_color)s%(levelname)s%(reset)s]  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red',
    },
    reset=True,
    style='%'
)
console_handler.setFormatter(formatter)