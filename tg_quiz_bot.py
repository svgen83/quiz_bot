import json
import logging
import os
import random
import redis

from dotenv import load_dotenv
from quiz_base_tools import get_text_fragments, get_quiz_bases

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CallbackContext, ConversationHandler
from telegram.ext import CommandHandler, MessageHandler, Filters


logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY = range(2)

   
def get_user_info (update, context):
    chat_id = update.message.chat_id
    if r.get(chat_id):
        user_info = json.loads(r.get(chat_id))
    return user_info


def start(update, context):  
    custom_keyboard = [['Новый вопрос', 'Сдаться'],['Мой счёт']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text('Привет! Я бот для викторин',
                              reply_markup=reply_markup)
    return CHOOSING
    

def handle_new_question_request(update, context):
    user_info = get_user_info(update, context)
    random_question = random.choice(list(quiz_bases))
    answer = quiz_bases.get(random_question)
    short_answer = answer[answer.find(':')+2 : answer.find('.')]
    user_info.update({'chat_id':update.message.chat_id,
                 'question':random_question,
                 'answer':short_answer
                  })
    r.set(user_info['chat_id'], json.dumps(user_info))
    logger.info (user_info['question'])
    logger.info (user_info['answer'])
    update.message.reply_text(user_info['question'])
    return TYPING_REPLY
    
    
def handle_solution_attempt(update, context):
    user_info = get_user_info(update, context)
    if update.message.text == user_info['answer']:
        update.message.reply_text(''' Правильно! Поздравляю! 
                                      Для следующего вопроса нажми 'Новый вопрос' 
                                  ''')
        if 'score' in user_info:
            score = user_info['score']
        else:
            score = 0
        score +=1
        user_info['score'] = score
        r.set(user_info['chat_id'], json.dumps(user_info))
        return CHOOSING
    else:
        update.message.reply_text('Неправильно... Попробуешь ещё раз?')
        return TYPING_REPLY 
       

def handle_hands_up(update, context):
    user_info = get_user_info(update, context)
    update.message.reply_text(user_info['answer'])
    return CHOOSING  
         

def send_score(update, context):
    user_info = get_user_info(update, context)
    if user_info['score']:
        score = user_info['score']
    else:
        score = 0
    update.message.reply_text(f'Ваш счет:{score}')
    return CHOOSING 


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def start_bot():
    
    updater = Updater(tg_token)
     
    dp = updater.dispatcher
    
    conv_handler = ConversationHandler(
        entry_points=[
                      CommandHandler('start', start),
                      MessageHandler(Filters.regex(r'Новый вопрос'),
                                     handle_new_question_request),
                      MessageHandler(Filters.regex(r'Мой счёт'),
                                     send_score),
                      MessageHandler(Filters.regex(r'Сдаться'),
                                     handle_hands_up)
                      ],

        states={
            CHOOSING: [
                       MessageHandler(Filters.regex(r'Новый вопрос'),
                                      handle_new_question_request),
                       MessageHandler(Filters.regex(r'Сдаться'),
                                      handle_hands_up),
                       MessageHandler(Filters.regex(r'Мой счёт'),
                                      send_score)
                       ],

            TYPING_REPLY: [
                           MessageHandler(Filters.text 
                                          & ~Filters.regex(r'Мой счёт')
                                          & ~Filters.regex(r'Сдаться'),
                                          handle_solution_attempt),
                           MessageHandler(Filters.regex(r'Мой счёт'),
                                          send_score),            
                           MessageHandler(Filters.regex(r'Сдаться'),
                                          handle_hands_up)
                           ]
        },

        fallbacks=[MessageHandler(Filters.regex(r'Мой счёт'), send_score),            
                   MessageHandler(Filters.regex(r'Сдаться'), handle_hands_up)]
        
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    load_dotenv()
    
    logging.basicConfig(
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                  level=logging.INFO
                       )
    
    tg_token = os.getenv('TG_TOKEN')
    
    r = redis.Redis(host=os.getenv('REDIS_ENDPOINT'),
                    port=os.getenv('REDIS_PORT'),
                    password=os.getenv('REDIS_PASSWORD'), db=0)
                    
    quiz_bases = get_quiz_bases('quiz-questions')
    start_bot()

