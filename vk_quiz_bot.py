import json
import logging
import os

import random
import redis
import vk_api as vk

from dotenv import load_dotenv
from quiz_base_tools import get_text_fragments, get_quiz_bases

from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


logger = logging.getLogger(__name__)

        
def get_user_info (event, vk_api):
    user_info = {"user_id": event.user_id}
    if r.get(event.user_id):
        user_info = json.loads(r.get(event.user_id))
    return user_info


##def choose_msg(event, vk_api):
##    if event.text == 'Новый вопрос':
##        msg = handle_new_question_request(event, vk_api)
##    elif event.text == 'Сдаться':
##        msg = handle_hands_up(event, vk_api)
##    elif event.text == 'Мой счёт':
##        msg = send_score(event, vk_api)
##    else: msg = handle_solution_attempt(event, vk_api)
##    return msg


def handle_new_question_request(event, vk_api):
    user_info = get_user_info(event, vk_api)
    random_question = random.choice(list(quiz_bases))
    answer = quiz_bases.get(random_question)
    short_answer = answer[answer.find(':')+2 : answer.find('.')]
    user_info.update({'chat_id': event.user_id,
                 'question':random_question,
                 'answer':short_answer
                  })
    r.set(user_info['chat_id'], json.dumps(user_info))
    logger.info (user_info['question'])
    logger.info (user_info['answer'])
    return user_info['question']
    
    
def handle_solution_attempt(event, vk_api):
    user_info = get_user_info(event, vk_api)
    if event.text == user_info['answer']:
        if 'score' in user_info:
            score = user_info['score']
        else:
            score = 0
        score +=1
        user_info['score'] = score
        r.set(user_info['chat_id'], json.dumps(user_info))
        return ''' Правильно! Поздравляю! 
                                      Для следующего вопроса нажми 'Новый вопрос' 
                                  '''
    else:
        return "Неправильно... Попробуешь ещё раз?"       


def handle_hands_up(event, vk_api):
    user_info = get_user_info(event, vk_api)
    return user_info['answer']
      
         

def send_score(event, vk_api):
    user_info = get_user_info(event, vk_api)
    if user_info['score']:
        score = user_info['score']
    else:
        score = 0
    return f'Ваш счет:{score}'
    
    
def make_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color = VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color = VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счёт', color = VkKeyboardColor.NEGATIVE)
    return keyboard
    
     
def send_msg(event, vk_api):
    keyboard = make_keyboard()
    if event.text == 'Новый вопрос':
        msg = handle_new_question_request(event, vk_api)
    elif event.text == 'Сдаться':
        msg = handle_hands_up(event, vk_api)
    elif event.text == 'Мой счёт':
        msg = send_score(event, vk_api)
    else: msg = handle_solution_attempt(event, vk_api)
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=random.randint(1,1000),
        keyboard=keyboard.get_keyboard(),
        message=msg)
    logger.info ('сообщение отправлено')



def start_bot():

    vk_session = vk.VkApi(token=os.getenv('VK_TOKEN'))
    vk_api = vk_session.get_api()
       
    r = redis.Redis(host=os.getenv('REDIS_ENDPOINT'),
                    port=os.getenv('REDIS_PORT'),
                    password=os.getenv('REDIS_PASSWORD'), db=0)
                    
    longpoll = VkLongPoll(vk_session)
                    
    quiz_bases = get_quiz_bases('quiz-questions')
    logger.info ('Бот запущен')
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            send_msg(event, vk_api)
     

if __name__ == '__main__':
       
    load_dotenv()
    
    logging.basicConfig(
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                  level=logging.INFO
                  )
    


    start_bot()

    
    
    
    
    
    
    
    

