import logging
from tkinter import PhotoImage
import strings
import random 
import requests
import re

from telegram import Update, Chat, User
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, PicklePersistence

from settings import BOT_TOKEN, SUPER_ADMIN_ID, DEBUG, WEBHOOK_URL, BLACKLIST_ID, BACKUP_CHANNEL_ID, SAVE_UPDATE, \
    FORWARD_UPDATE, DELTA_LIMIT, MAX_CURRENCY_LEN, db

logger = logging.getLogger(__name__)


def save_update(f):
    def g(update: Update, context: CallbackContext):
        response = f(update, context)
        if not DEBUG and SAVE_UPDATE:
            db.updates.insert_one(update.to_dict())
        return response
    return g


def forward_update(f):
    def g(update: Update, context: CallbackContext):
        response = f(update, context)
        if not DEBUG and (((Filters.video | Filters.photo | Filters.document) & ~Filters.document.gif)(update)) and FORWARD_UPDATE:
            update.message.forward(BACKUP_CHANNEL_ID)
        return response
    return g


@save_update
def start_command(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    message = update.message
    if message.chat.type == Chat.PRIVATE:
        message.reply_markdown_v2(strings.START_STRING_PRIVATE_CHAT)
    else:
        message.reply_text(strings.START_STRING_CHAT)


@save_update
def credit_message(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    user = message.reply_to_message.from_user
    context.chat_data.setdefault('silence', False)
    silence_mode = context.chat_data['silence']
    if 'battle' in context.chat_data:
        context.chat_data.setdefault('battle', {})
        credit_dic = context.chat_data['battle']
        silence_mode = True
    else:
        credit_dic = context.chat_data
    if user.is_bot:
        if user.id == context.bot.id:
            text = strings.CREDIT_BOT_BATTLE
        else:
            text = strings.CREDIT_USER_BATTLE
    else:
        currency = context.match.group(3)
        if len(currency) > MAX_CURRENCY_LEN:
            message.reply_text(f"Слишком длинно! Лимит на длину - {MAX_CURRENCY_LEN} символов!\n")
            return
        value = +1 if context.match.group(1) == '+' else -1
        if len(context.match.group(2)) > 0:
            points = int(context.match.group(2))
        else:
            points = len(context.match.group(1) + context.match.group(2))
        if user.id in BLACKLIST_ID:
            value = -1
        elif message.from_user.id != SUPER_ADMIN_ID:

            if abs(points) > DELTA_LIMIT:
                message.reply_text(f"Слишком много! Лимит на изменение - {DELTA_LIMIT} {currency}баллов!\n")
                return
            
            points = min(points, DELTA_LIMIT)
        points = value * points
        credit_dic.setdefault(user.id, {'name': user.first_name, 'points': {}})
        credit_dic[user.id]['points'].setdefault(currency, 0)
        if message.from_user.id != SUPER_ADMIN_ID and message.from_user.id == user.id:
            if points > 0:
                text = strings.CREDIT_BOT
            else:
                credit_dic[user.id]['points'][currency] -= points
                text = strings.CREDIT_MINUS_ITSELF
        else:
            credit_dic[user.id]['points'][currency] += points
            text = strings.GetStringForPoints(currency, points)

    if not silence_mode:
        message.reply_text(text, reply_to_message_id = message.reply_to_message.message_id)


def get_credits_string(user: User, context: CallbackContext) -> str:
    context.chat_data.setdefault(user.id, {'name': user.first_name, 'points': {}})
    currencies = {}
    for key, value in context.chat_data[user.id]['points'].items():
        if value != 0:
            currencies[key] = value
    return " \n".join(
            [f'{value} {key}{strings.GetPointsMessageForPoints(value)}' for key, value in currencies.items()]
        ) if len(currencies) > 0 else None


def my_credits_command(update: Update, context: CallbackContext) -> None:
    if 'battle' in context.chat_data:
        return
    message = update.effective_message
    user = update.effective_user
    credits = get_credits_string(user, context)
    message.reply_text(
        str.format('У тебя:\n{}', credits) if credits is not None else 'У тебя нет баллов.')


def credits_command(update: Update, context: CallbackContext) -> None:
    if 'battle' in context.chat_data:
        return
    message = update.effective_message
    if not message.reply_to_message:
        my_credits_command(update, context)
        return
    user = message.reply_to_message.from_user
    if user.id == context.bot.id:
        message.reply_text(strings.CREDIT_BOT_INFO)
        return
    credits = get_credits_string(user, context)
    message.reply_text(
        str.format('У {}:\n{}', user.first_name, credits) if credits is not None else f'У {user.first_name} нет баллов.')


def extract_currency(name: str) -> str:
    m = re.search(r'([^\s]+)бал', name)
    return name if m is None else m.group(1)


def rank_command(update: Update, context: CallbackContext) -> None:
    if 'battle' in context.chat_data:
        return
    currency = extract_currency(context.args[0]) if len(context.args) > 0 else strings.CREDIT_BOT_DEFAULT_CURRENCY
    message = update.effective_message
    leaderboard = []
    for key, value in context.chat_data.items():
        if type(key) is not int:
            continue
        points = value['points'].get(currency, 0)
        if points != 0:
            leaderboard.append((points, value['name']))
    leaderboard.sort(reverse=True)
    if len(leaderboard) < 4:
        message.reply_text('Недостаточно людей для составления доски почета!')
        return
    best = leaderboard[:3]
    worst = sorted(leaderboard[-3:])
    text = ''

    text += f'Больше всего {currency}баллов:\n'
    if len(best) == 0:
        text += 'ни у кого!'
    for row in best:
        text += '{} ➔ {} {}{}\n'.format(
            row[1],
            str(row[0]),
            currency,
            strings.GetPointsMessageForPoints(abs(row[0]))
        )

    text += f'\nМеньше всего {currency}баллов:\n'
    if len(worst) == 0:
        text += 'ни у кого!'
    for row in worst:
        text += '{} ➔ {} {}{}\n'.format(
            row[1],
            str(row[0]),
            currency,
            strings.GetPointsMessageForPoints(abs(row[0]))
        )
    message.reply_text(text)


def top_currencies_command(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    currencies = {}
    for key, value in context.chat_data.items():
        if type(key) is not int:
            continue
        for currency in value['points'].keys():
            currencies[currency] = currencies.get(currency, 0) + 1
    currencies = sorted(currencies.items(), reverse=True, key=lambda item: item[1])[:4]
    text = ''
    for currency, points in currencies:
        text += '{}баллы ➔ {} {}\n'.format(
            currency,
            points,
            strings.GetHoldersMessageForHolders(abs(points))
        )
    message.reply_text(text)


def cat_command(update: Update, context: CallbackContext):
    message = update.effective_message
    
    img_data = requests.get("https://thiscatdoesnotexist.com/").content

    message.reply_photo(photo = img_data)


def private_message(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Работаю только в группах.')


def error(update, context):
    logger.warning('Пошел я нахуй. Update "%s" caused error "%s"', update, context.error)


@save_update
@forward_update
def any_message(update, context):
    pass


def main() -> None:
    persistence = PicklePersistence(filename='VectorCreditBot')

    updater = Updater(BOT_TOKEN, persistence=persistence)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('credits', credits_command, filters=Filters.chat_type.groups))
    dispatcher.add_handler(CommandHandler('rank', rank_command, filters=Filters.chat_type.groups))
    dispatcher.add_handler(CommandHandler('top_currencies', top_currencies_command, filters=Filters.chat_type.groups))
    dispatcher.add_handler(CommandHandler('cat', cat_command))

    dispatcher.add_handler(MessageHandler(
        ~Filters.user(user_id=BLACKLIST_ID) &
        Filters.text & ~Filters.command & Filters.reply & Filters.regex(
            r'([+-])(\d*) ([^\s]+)бал'),
        credit_message
    ))
    dispatcher.add_handler(MessageHandler(Filters.chat_type.private, private_message))

    dispatcher.add_handler(MessageHandler(Filters.all, any_message))
    dispatcher.add_error_handler(error)

    if DEBUG:
        logger.info(f"Start Polling...")
        updater.start_polling()
    else:
        logger.info(f"Webhook on port: 5000")
        updater.start_webhook(listen="0.0.0.0", port=5000, url_path=BOT_TOKEN, webhook_url=WEBHOOK_URL + BOT_TOKEN)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
