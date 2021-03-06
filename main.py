import logging
from tkinter import PhotoImage
import strings
import random 
import requests

from telegram import Update, Chat
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, PicklePersistence

from settings import BOT_TOKEN, SUPER_ADMIN_ID, DEBUG, WEBHOOK_URL, BLACKLIST_ID, BACKUP_CHANNEL_ID, SAVE_UPDATE, \
    FORWARD_UPDATE, DELTA_LIMIT, db

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
        value = +1 if context.match.group(1) == '+' else -1
        if len(context.match.group(2)) > 0:
            points = int(context.match.group(2))
        else:
            points = len(context.match.group(1) + context.match.group(2))
        if user.id in BLACKLIST_ID:
            value = -1
        elif message.from_user.id != SUPER_ADMIN_ID:
            
            if abs(points) > DELTA_LIMIT:
                message.reply_text(f"?????????????? ??????????! ?????????? ???? ?????????????????? - {DELTA_LIMIT} ????????????????????????!\n")
                return
            
            points = min(points, DELTA_LIMIT)
        points = value * points
        credit_dic.setdefault(user.id, {'name': user.first_name, 'points': 0})
        if message.from_user.id != SUPER_ADMIN_ID and message.from_user.id == user.id:
            if points > 0:
                text = strings.CREDIT_BOT
            else:
                credit_dic[user.id]['points'] -= points
                text = strings.CREDIT_MINUS_ITSELF
        else:
            credit_dic[user.id]['points'] += points
            text = strings.GetStringForPoints(points)

    if not silence_mode:
        message.reply_text(text, reply_to_message_id = message.reply_to_message.message_id)


def my_credits_command(update: Update, context: CallbackContext) -> None:
    if 'battle' in context.chat_data:
        return
    message = update.effective_message
    user = update.effective_user
    context.chat_data.setdefault(user.id, {'name': user.first_name, 'points': 0})
    points = context.chat_data[user.id]['points']
    message.reply_text(f'?? ???????? {points} {strings.GetPointsMessageForPoints(points)}' if points != 0 else '?? ???????? ?????? ????????????????????????.')


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
    context.chat_data.setdefault(user.id, {'name': user.first_name, 'points': 0})
    points = context.chat_data[user.id]['points']
    message.reply_text(
        f'?? {user.first_name} {points} {strings.GetPointsMessageForPoints(points)}' if points != 0 else f'?? {user.first_name} ?????? ????????????????????????.')


def rank_command(update: Update, context: CallbackContext) -> None:
    if 'battle' in context.chat_data:
        return
    message = update.effective_message
    leaderboard = []
    for key, value in context.chat_data.items():
        if type(key) is int:
            leaderboard.append((value['points'], value['name']))
    leaderboard.sort(reverse=True)
    if len(leaderboard) < 4:
        message.reply_text('???????????????????????? ?????????? ?????? ?????????????????????? ?????????? ????????????!')
        return
    best = leaderboard[:3]
    worst = sorted(leaderboard[-3:])
    text = ''

    text += '???????????? ?????????? ????????????????????????:\n'
    if len(best) == 0:
        text += '???? ?? ????????!'
    for row in best:
        text += '{} ??? {} {}\n'.format(
            row[1],
            str(row[0]),
            strings.GetPointsMessageForPoints(abs(row[0]))
        )

    text += '\n???????????? ?????????? ????????????????????????:\n'
    if len(worst) == 0:
        text += '???? ?? ????????!'
    for row in worst:
        text += '{} ??? {} {}\n'.format(
            row[1],
            str(row[0]),
            strings.GetPointsMessageForPoints(abs(row[0]))
        )
    message.reply_text(text)

def cat_command(update: Update, context: CallbackContext):
    message = update.effective_message
    
    img_data = requests.get("https://thiscatdoesnotexist.com/").content

    message.reply_photo(photo = img_data)


def private_message(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('?????????????? ???????????? ?? ??????????????.')


def error(update, context):
    logger.warning('?????????? ?? ??????????. Update "%s" caused error "%s"', update, context.error)


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
    dispatcher.add_handler(CommandHandler('cat', cat_command))

    dispatcher.add_handler(MessageHandler(
        ~Filters.user(user_id=BLACKLIST_ID) &
        Filters.text & ~Filters.command & Filters.reply & Filters.regex(
            r'([+-])(\d*) (????????????????????|??????????????????????|??????????????????|????????????????????|????????????????????????|??????????????????????)'),
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
