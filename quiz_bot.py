import json
import logging
import os
import random
import redis

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CallbackContext
from telegram.ext import CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


def get_text_fragments(text, start_symbols, split_symbols):
    fragments = []
    splitted_text = text.split(split_symbols)
    for fragment in splitted_text:
        if fragment.startswith(start_symbols):
            fragments.append(fragment)
    return fragments


def get_quiz_bases(quiz_dir):
    quiz_bases = {}
    for quiz_file in os.listdir(quiz_dir):
        path_to_file = f"{quiz_dir}/{quiz_file}"
        with open(path_to_file, "r", encoding = "KOI8-R") as quiz_file:
          file_contents = quiz_file.read()
        question = get_text_fragments(file_contents, "Вопрос", "\n\n")
        answer = get_text_fragments(file_contents, "Ответ:", "\n\n")
        quiz_base = dict(zip(question, answer))
        quiz_bases.update(quiz_base)
    return quiz_bases
    

def start(update, context):  
    custom_keyboard = [["Новый вопрос", "Сдаться"],["Мой счёт"]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text('Привет! Я бот для викторин', reply_markup=reply_markup)
    

def send_msg(update, context):
    random_question = random.choice(list(quiz_bases))
    if update.message.text == "Новый вопрос":
        r.set(update.message.chat_id, random_question)
        question = (r.get(update.message.chat_id)).decode("utf-8")
        logger.info (question)
        answer = quiz_bases.get(question)
        for_answer = answer[answer.find(':')+2 : answer.find('.')]
        logger.info (for_answer)
        msg = question
        r.set(update.message.chat_id, for_answer)
    elif update.message.text == (r.get(update.message.chat_id)).decode("utf-8"):
        msg = "Правильно! Поздравляю! Для следующего вопроса нажми 'Новый вопрос'"
    elif update.message.text == "Сдаться":
        msg = (r.get(update.message.chat_id)).decode("utf-8")
    elif update.message.text == "Мой счёт":
        msg = "в разработке"
    else: msg = "Неправильно... Попробуешь ещё раз?"
    update.message.reply_text(msg)


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def start_bot():

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
    
    updater = Updater(tg_token)
    
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, send_msg))
    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    load_dotenv()
    
    tg_token = os.getenv("TG_TOKEN")
    
    r = redis.Redis(host=os.getenv("REDIS_ENDPOINT"),
                    port=os.getenv("REDIS_PORT"),
                    password=os.getenv("REDIS_PASSWORD"), db=0)
                    
    quiz_bases = get_quiz_bases("quiz-questions")
    start_bot()

