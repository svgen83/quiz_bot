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


def send_msg(event, vk_api):
    if event.text == "Новый вопрос":
       msg = handle_new_question_request(event)
    if event.text == "Сдаться":
       msg = handle_hands_up(event)
    if event.txt == "Мой счёт":
       msg = send_score(event)

    vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1,1000),
        keyboard=keyboard.get_keyboard(),
        message=msg)
        
    
##    vk_api.messages.send(
##    user_id=event.user_id,
##    message=event.text,
##    random_id=random.randint(1,1000)




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

    
def get_user_info (event):
    user_id = event.user_id
    if r.get(user_id):
        user_info = json.loads(r.get(user_id))
    return user_info


def handle_new_question_request(event):
    user_info = get_user_info(event)
    random_question = random.choice(list(quiz_bases))
    answer = quiz_bases.get(random_question)
    short_answer = answer[answer.find(':')+2 : answer.find('.')]
    user_info.update({'chat_id':user_id,
                 "question":random_question,
                 "answer":short_answer
                  })
    r.set(user_info['chat_id'], json.dumps(user_info))
    logger.info (user_info["question"])
    logger.info (user_info["answer"])
    return user_info["question"]
    
    
def handle_solution_attempt(event):
    user_info = get_user_info(event)
    if event.text == user_info["answer"]:
        if 'score' in user_info:
            score = user_info['score']
        else:
            score = 0
        score +=1
        user_info["score"] = score
        r.set(user_info['chat_id'], json.dumps(user_info))
        return ''' Правильно! Поздравляю! 
                                      Для следующего вопроса нажми 'Новый вопрос' 
                                  '''
    else:
        return "Неправильно... Попробуешь ещё раз?"       


def handle_hands_up(event):
    user_info = get_user_info(event)
    return user_info["answer"]
      
         

def send_score(update, context):
    user_info = get_user_info(event)
    if user_info["score"]:
        score = user_info["score"]
    else:
        score = 0
    return f'Ваш счет:{score}'
     


##def send_msg(update, context):
##    random_question = random.choice(list(quiz_bases))
##    if update.message.text == "Новый вопрос":
##        r.set(update.message.chat_id, random_question)
##        question = (r.get(update.message.chat_id)).decode("utf-8")
##        logger.info (question)
##        answer = quiz_bases.get(question)
##        for_answer = answer[answer.find(':')+2 : answer.find('.')]
##        logger.info (for_answer)
##        msg = question
##        r.set(update.message.chat_id, for_answer)
##    elif update.message.text == (r.get(update.message.chat_id)).decode("utf-8"):
##        msg = "Правильно! Поздравляю! Для следующего вопроса нажми 'Новый вопрос'"
##    elif update.message.text == "Сдаться":
##        msg = (r.get(update.message.chat_id)).decode("utf-8")
##    elif update.message.text == "Мой счёт":
##        msg = "в разработке"
##    else: msg = "Неправильно... Попробуешь ещё раз?"
##    update.message.reply_text(msg)




##def error(event):
##    logger.warning('Update "%s" caused error "%s"', event.error)


def start_bot():

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
    
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
            send_msg(event, vk_api)
     

if __name__ == '__main__':

    start_bot()

    
    
    
    
    
    
    
    

