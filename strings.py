import random


START_STRING_PRIVATE_CHAT = 'Добавь меня в чат чтобы отслеживать баллы'
START_STRING_CHAT = 'Работаем...'
CREDIT_BOT_BATTLE = "Расстрелять!"
CREDIT_USER_BATTLE = "Не важно, он всё равно ничего не стоил."
CREDIT_BOT = "Запрещено! Немедленно прекратите! Штраф 1000 рублей."
CREDIT_MINUS_ITSELF = "Ok Idiot, You lost it"
ERROR_NO_REPLY = "You should reply this command to someone to see their credits."
CREDIT_BOT_INFO = "Больше чем у тебя"
CREDIT_BOT_DEFAULT_CURRENCY = "вектор"

PLUS_CREDIT_MESSAGES = [
        "Родина гордится тобой! +{} {}{}!",
        "Отличная работа! +{} {}{}!",
        "Все дальше от буржуйства! +{} {}{}!",
        "Так когда-то и Раст начнешь изучать! +{} {}{}!",
        "Один миска си плюс плюс и аниме жена! +{} {}{}! 打!"
    ]
MINUS_CREDIT_MESSAGES = [
        "Позор! {} {}{}!",
        "Прекратите. {} {}{}.",
        "Так и буржуем можно стать. {} {}{}.",
        "Плохо!\n{} {}{}.",
        "丟人現眼. Отобрать аниме жена. {} {}{}."
    ]

def GetPointsMessageForPoints(points):
    last_digit = abs(points) % 10

    if last_digit == 1:
        return "балл"

    if last_digit > 1 and last_digit <= 4:
        return "балла"
    
    return "баллов"

def GetStringForPoints(currency, points):
    message = random.choice(PLUS_CREDIT_MESSAGES) if points > 0 else random.choice(MINUS_CREDIT_MESSAGES)

    return message.format(points, currency, GetPointsMessageForPoints(points))