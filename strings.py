import random


START_STRING_PRIVATE_CHAT = 'Добавь меня в чат чтобы отслеживать векторбаллы'
START_STRING_CHAT = 'Работаем...'
CREDIT_BOT_BATTLE = "Расстрелять!"
CREDIT_USER_BATTLE = "Не важно, он всё равно ничего не стоил."
CREDIT_BOT = "Запрещено! Немедленно прекратите! Штраф 1000 рублей."
CREDIT_MINUS_ITSELF = "Ok Idiot, You lost it"
ERROR_NO_REPLY = "You should reply this command to someone to see their credits."
CREDIT_BOT_INFO = "Больше чем у тебя"

PLUS_CREDIT_MESSAGES = [
        "Родина гордится тобой! +{} {}!",
        "Отличная работа! +{} {}!",
        "Все дальше от буржуйства! +{} {}!",
        "Так когда-то и Раст начнешь изучать! +{} {}!",
        "Один миска си плюс плюс и аниме жена! +{} {}! 打!"
    ]
MINUS_CREDIT_MESSAGES = [
        "Позор! {} {}!",
        "Прекратите. {} {}.",
        "Так и буржуем можно стать. {} {}.",
        "...\n{} {}.",
        "丟人現眼. Отобрать аниме жена. {} {}."
    ]

def GetPointsMessageForPoints(points):
    last_digit = points % 10

    if last_digit == 1:
        return "векторбалл"

    if last_digit > 1 and last_digit <= 4:
        return "векторбалла"
    
    return "векторбаллов"

def GetStringForPoints(points):
    message = random.choice(PLUS_CREDIT_MESSAGES) if points > 0 else random.choice(MINUS_CREDIT_MESSAGES)

    return message.format(points, GetPointsMessageForPoints(points))

def GetStatusMessageForPoints(points):
    if points == 0:
        return "Новичок"

    if points > 0 and points < 15:
        return "Уважаемый человек"

    if points >= 15 and points < 40:
        return "Смешарик"

    if points >= 40 and points < 100:
        return "Член опергруппы НКВД по раскулачиванию"

    if points > 100:
        return "Программист на Расте"

    if points > 1000:
        return "(Вставить что-то смешное)"

    if points < 0 and points > -10:
        return "Расточитель"

    if points <= -10 and points > -40:
        return "Буржуй"

    if points <= -100:
        return "Стандартодрочер"

    if points < -1000:
        return "Келбон"