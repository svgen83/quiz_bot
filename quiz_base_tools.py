import os
import logging


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
        path_to_file = f'{quiz_dir}/{quiz_file}'
        with open(path_to_file, 'r', encoding = 'KOI8-R') as quiz_file:
          file_contents = quiz_file.read()
        question = get_text_fragments(file_contents, 'Вопрос', '\n\n')
        answer = get_text_fragments(file_contents, 'Ответ:', '\n\n')
        quiz_base = dict(zip(question, answer))
        quiz_bases.update(quiz_base)
    logger.info ('база вопросов создана')
    return quiz_bases    
