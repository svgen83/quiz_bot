import os
from pprint import pprint


def get_sliced_text(text, start_word, end_word):
    sliced_texts = []
    for line in text:
        if line.startswith(start_word):
            start_index = text.index(line)
            #print(line, start_index)
            sliced_text = " ".join(text[start_index : text.index(end_word, start_index)])
            sliced_texts.append(sliced_text)
    return sliced_texts


def sliced(text, start_word):
    fragments = []
    splitted_text = text.split("\n\n")
    #pprint(splitted_text)
    for fragment in splitted_text:
        if fragment.startswith(start_word):
            fragments.append(fragment)
    return fragments

quiz_dir = "quiz-questions"

quiz_bases = {}

# i = text.index(start); result = text[i:text.index(end, i) + len(end)]

#r = ''.join(get_inside_lines(open('111.txt', encoding='utf-8'),
#                            'Но пусть она вас больше не тревожит;\n',
#                            'То робостью, то ревностью томим;\n'))

for quiz_file in os.listdir(quiz_dir):
    path_to_file = f"{quiz_dir}/{quiz_file}"
    with open(path_to_file, "r", encoding = "KOI8-R") as quiz_file:
      file_contents = quiz_file.read()
      question = sliced(file_contents, "Вопрос")
      #pprint(question)
      answer = sliced(file_contents, "Ответ:")
      #pprint(answer)
      quiz_base = dict(zip(question, answer))
      quiz_bases.update(quiz_base)
pprint(quiz_bases)
    
      #print(path_to_file)
      #if question and answer:
       #   quiz_base[question]=answer
#pprint(quiz_base)

