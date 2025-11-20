import os
import json
import requests
import boto3
from botocore.exceptions import ClientError

# Configuration
TG_BOT_TOKEN = os.environ['TG_BOT_TOKEN']
BUCKET_NAME = os.environ['BUCKET_NAME']
OBJECT_KEY = os.environ['OBJECT_KEY']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

# Yandex Object Storage client
s3_client = boto3.client(
    's3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def get_instruction():
    """Get instruction from Object Storage"""
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=OBJECT_KEY)
        return response['Body'].read().decode('utf-8')
    except ClientError as e:
        print(f"Error getting instruction: {e}")
        return None

def send_telegram_message(chat_id, text):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def is_exam_question(text):
    """Check if text is an exam question about operating systems"""
    exam_keywords = [
        "управление памятью", "процессы", "файловые системы", 
        "кооперация процессов", "операционные системы", "память",
        "планирование", "ввод-вывод", "семафоры", "страничная",
        "виртуальная", "диспетчеризация", "критическая секция",
        "взаимоисключения", "тупики", "deadlock", "алгоритм",
        "стратегия", "управление", "распределение", "организация"
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in exam_keywords)

def generate_answer(question):
    """Generate answer for exam question"""
    question_lower = question.lower()
    
    if "управление памятью" in question_lower or "память" in question_lower:
        return """🎯 **Управление памятью в операционных системах**

**Основные функции:**
• Распределение памяти между процессами
• Виртуальная память
• Страничная организация памяти
• Сегментная организация
• Кэширование

**Алгоритмы замещения страниц:**
- FIFO (First-In-First-Out)
- LRU (Least Recently Used)
- OPT (Optimal)
- NFU (Not Frequently Used)

**Проблемы:**
- Фрагментация (внешняя и внутренняя)
- Thrashing (перегрузка системы подкачкой)"""

    elif "процессы" in question_lower or "планирование" in question_lower:
        return """🎯 **Процессы и планирование в ОС**

**Процесс** - экземпляр выполняющейся программы.

**Состояния процесса:**
1. Создан (New)
2. Готов (Ready)
3. Выполняется (Running)
4. Ожидание (Waiting)
5. Завершен (Terminated)

**Алгоритмы планирования:**
- FCFS (First-Come, First-Served)
- SJF (Shortest Job First)
- Round Robin
- Приоритетное планирование

**Контекст процесса** включает: состояние регистров, указатель стека, состояние памяти и т.д."""

    elif "файловые системы" in question_lower:
        return """🎯 **Файловые системы**

**Основные функции:**
• Организация хранения данных на дисках
• Управление каталогами и файлами
• Контроль доступа
• Резервное копирование

**Методы распределения пространства:**
- Непрерывное распределение
- Связный список
- Индексные узлы (i-nodes)
- FAT (File Allocation Table)

**Типы файлов:**
- Обычные файлы
- Каталоги
- Символические ссылки
- Устройства"""

    elif "кооперация процессов" in question_lower or "взаимодействие" in question_lower:
        return """🎯 **Кооперация процессов**

**Средства взаимодействия:**
• Семафоры
• Мьютексы
• Мониторы
• Сообщения
• Разделяемая память

**Проблемы синхронизации:**
- Взаимоисключения (mutual exclusion)
- Гонки данных (race condition)
- Взаимоблокировки (deadlocks)
- Голодание (starvation)

**Алгоритмы:**
- Алгоритм Петерсона
- Test-and-Set команды
- Семафоры Дейкстры"""

    else:
        return f"""🎯 **Ответ на вопрос по операционным системам**

Вопрос: {question}

Это экзаменационный вопрос по операционным системам. Для более точного ответа требуется дополнительная контекстуальная информация.

**Основные темы операционных систем:**
- Управление процессами и памятью
- Файловые системы и ввод-вывод
- Взаимодействие и синхронизация процессов
- Безопасность и защита"""

def handler(event, context):
    """Main handler function"""
    try:
        body = json.loads(event['body'])
        message = body['message']
        chat_id = message['chat']['id']
        
        # Handle /start and /help commands
        if 'text' in message:
            text = message['text']
            
            if text in ['/start', '/help']:
                response_text = """🤖 **Шпаргалка ИТИС 2024 vvot23**

Я помогу ответить на экзаменационный вопрос по «Операционным системам».

**Как использовать:**
1. Пришлите вопрос текстом
2. Или отправьте фотографию с вопросом
3. Я подготовлю структурированный ответ

**Поддерживаемые темы:**
• Управление памятью
• Процессы и планирование
• Файловые системы
• Кооперация процессов
• Управление вводом-выводом"""
                send_telegram_message(chat_id, response_text)
                return {'statusCode': 200, 'body': 'OK'}
        
        # Handle text messages
        if 'text' in message:
            user_question = message['text']
            
            if is_exam_question(user_question):
                answer = generate_answer(user_question)
                send_telegram_message(chat_id, answer)
            else:
                send_telegram_message(chat_id, 
                    "❌ **Я не могу понять вопрос**\n\n"
                    "Пришлите экзаменационный вопрос по «Операционным системам».\n\n"
                    "**Примеры вопросов:**\n"
                    "• Что такое управление памятью?\n"
                    "• Объясните планирование процессов\n"
                    "• Как работают файловые системы?")
        
        # Handle photos
        elif 'photo' in message:
            photos = message.get('photo', [])
            
            if len(photos) > 1:
                send_telegram_message(chat_id, "📷 Я могу обработать только одну фотографию за раз.")
                return {'statusCode': 200, 'body': 'OK'}
            
            send_telegram_message(chat_id, 
                "📷 **Обработка фотографий**\n\n"
                "Функция распознавания текста с фотографий в настоящее время настраивается.\n"
                "Пожалуйста, пришлите вопрос текстом для получения ответа.")
        
        # Handle other message types
        else:
            send_telegram_message(chat_id, 
                "⚠️ **Неподдерживаемый формат**\n\n"
                "Я могу обработать только:\n"
                "• Текстовые сообщения с вопросами\n"
                "• Фотографии с вопросами (скоро)\n\n"
                "Пришлите вопрос текстом.")
        
        return {'statusCode': 200, 'body': 'OK'}
        
    except Exception as e:
        print(f"Error: {e}")
        send_telegram_message(chat_id, "❌ Произошла ошибка при обработке запроса. Попробуйте позже.")
        return {'statusCode': 500, 'body': str(e)}