import json
import logging
import os
import random
import redis

from dotenv import load_dotenv
from functools import partial
from quiz_base_tools import get_text_fragments, get_quiz_bases
from quiz_base_tools import get_user_info

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CallbackContext, ConversationHandler
from telegram.ext import CommandHandler, MessageHandler, Filters

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY = range(2)


def start(update, context):
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text('Привет! Я бот для викторин',
                              reply_markup=reply_markup)
    return CHOOSING


def handle_new_question_request(redis_call, quiz_bases,
                                update, context):
    user_info = get_user_info(update.message.chat.id,
                              redis_call)
    random_question, answer = random.choice(list(quiz_bases.items()))
    short_answer = answer[answer.find(':') + 2:answer.find('.')]
    user_info.update({
        'chat_id': update.message.chat.id,
        'question': random_question,
        'answer': short_answer
    })
    redis_call.set(user_info['chat_id'], json.dumps(user_info))
    logger.info(user_info['question'])
    logger.info(user_info['answer'])
    update.message.reply_text(user_info['question'])
    return TYPING_REPLY


def handle_solution_attempt(redis_call, update, context):
    user_info = get_user_info(update.message.chat.id,
                              redis_call)
    if update.message.text == user_info['answer']:
        update.message.reply_text(''' Правильно! Поздравляю!
                                      Для следующего вопроса нажми 'Новый вопрос'
                                  ''')
        if 'score' in user_info:
            score = user_info['score']
        else:
            score = 0
        score += 1
        user_info['score'] = score
        redis_call.set(user_info['chat_id'], json.dumps(user_info))
        return CHOOSING
    else:
        update.message.reply_text('Неправильно... Попробуешь ещё раз?')
        return TYPING_REPLY


def handle_hands_up(redis_call, update, context):
    user_info = get_user_info(update.message.chat.id,
                              redis_call)
    update.message.reply_text(user_info['answer'])
    return CHOOSING


def send_score(redis_call, update, context):
    user_info = get_user_info(update.message.chat.id,
                              redis_call)
    if user_info['score']:
        score = user_info['score']
    else:
        score = 0
    update.message.reply_text(f'Ваш счет:{score}')
    return CHOOSING


def error(update, context):
    logger.warning('Update "%s" caused error "%s"',
                   update,
                   context.error)


def start_bot():
    load_dotenv()

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

    tg_token = os.getenv('TG_TOKEN')

    quiz_bases = get_quiz_bases('quiz-questions')
    r = redis.Redis(host=os.getenv('REDIS_ENDPOINT'),
                    port=os.getenv('REDIS_PORT'),
                    password=os.getenv('REDIS_PASSWORD'),
                    db=0)

    updater = Updater(tg_token)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(Filters.regex(r'Новый вопрос'),
                           partial(handle_new_question_request,
                                   r, quiz_bases)),
            MessageHandler(Filters.regex(r'Мой счёт'),
                           partial(send_score, r)),
            MessageHandler(Filters.regex(r'Сдаться'),
                           partial(handle_hands_up, r))
        ],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex(r'Новый вопрос'),
                               partial(handle_new_question_request,
                                       r, quiz_bases)),
                MessageHandler(Filters.regex(r'Сдаться'),
                               partial(handle_hands_up, r)),
                MessageHandler(Filters.regex(r'Мой счёт'),
                               partial(send_score, r))
            ],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~
                    Filters.regex(r'Мой счёт') & ~
                    Filters.regex(r'Сдаться'),
                    partial(handle_solution_attempt, r)),
                MessageHandler(Filters.regex(r'Мой счёт'),
                               partial(send_score, r)),
                MessageHandler(Filters.regex(r'Сдаться'),
                               partial(handle_hands_up, r))
            ]
        },
        fallbacks=[
            MessageHandler(Filters.regex(r'Мой счёт'),
                           partial(send_score, r)),
            MessageHandler(Filters.regex(r'Сдаться'),
                           partial(handle_hands_up, r))
        ])

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    start_bot()
