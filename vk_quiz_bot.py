import json
import logging
import os
import random
import redis

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

from dotenv import load_dotenv


logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY = range(2)


def echo(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1,1000),
        keyboard=keyboard.get_keyboard(),
        message='Пример клавиатуры'
    )
#    vk_api.messages.send(
 #       user_id=event.user_id,
  #      message=event.text,
   #     random_id=random.randint(1,1000)
    #)



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

    
def get_user_info (update, context):
    chat_id = update.message.chat_id
    if r.get(chat_id):
        user_info = json.loads(r.get(chat_id))
    return user_info


def start(update, context):  
    custom_keyboard = [["Новый вопрос", "Сдаться"],["Мой счёт"]]
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
                 "question":random_question,
                 "answer":short_answer
                  })
    r.set(user_info['chat_id'], json.dumps(user_info))
    logger.info (user_info["question"])
    logger.info (user_info["answer"])
    update.message.reply_text(user_info["question"])
    return TYPING_REPLY
    
    
def handle_solution_attempt(update, context):
    user_info = get_user_info(update, context)
    #print(user_info)
    if update.message.text == user_info["answer"]:
        update.message.reply_text(''' Правильно! Поздравляю! 
                                      Для следующего вопроса нажми 'Новый вопрос' 
                                  ''')
        if 'score' in user_info:
            score = user_info['score']
        else:
            score = 0
        score +=1
        user_info["score"] = score
        r.set(user_info['chat_id'], json.dumps(user_info))
        return CHOOSING
    else:
        update.message.reply_text("Неправильно... Попробуешь ещё раз?")
        return TYPING_REPLY 
       


def handle_hands_up(update, context):
    user_info = get_user_info(update, context)
    update.message.reply_text(user_info["answer"])
    return CHOOSING  
         

def send_score(update, context):
    user_info = get_user_info(update, context)
    if user_info["score"]:
        score = user_info["score"]
    else:
        score = 0
    update.message.reply_text(f'Ваш счет:{score}')
    return CHOOSING 


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
    
    #dp.add_handler(CommandHandler("start", start))
    #dp.add_handler(MessageHandler(Filters.text & ~Filters.command, send_msg))
    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    load_dotenv()
    
    #vk_token = os.getenv("VK_TOKEN")
    
    r = redis.Redis(host=os.getenv("REDIS_ENDPOINT"),
                    port=os.getenv("REDIS_PORT"),
                    password=os.getenv("REDIS_PASSWORD"), db=0)
                    
    quiz_bases = get_quiz_bases("quiz-questions")
    
    vk_session = vk.VkApi(token=os.getenv("VK_TOKEN"))
    vk_api = vk_session.get_api()
    
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос') #, color=VkKeyboardColor.DEFAULT)
    keyboard.add_button('Сдаться') #, color=VkKeyboardColor.POSITIVE)

    keyboard.add_line()  # Переход на вторую строку
    keyboard.add_button('Мой счет') #, color=VkKeyboardColor.NEGATIVE)
   
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            echo(event, vk_api)
    
    
    
    
    
    
    
    

