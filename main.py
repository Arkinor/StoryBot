import json
import random

# Загрузка данных из JSON файлов
with open('stories.json', 'r', encoding='utf-8') as file:
    stories_data = json.load(file)

with open('goodanswer.json', 'r', encoding='utf-8') as file:
    good_answers_data = json.load(file)

with open('badanswer.json', 'r', encoding='utf-8') as file:
    bad_answers_data = json.load(file)

# Загрузка данных пользователей из users.json
def load_users():
    try:
        with open('users.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"users": []}  # Если файл не найден, возвращаем пустой список

# Сохранение данных пользователей в users.json
def save_users(data):
    with open('users.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Получение истории по ID
def get_story_by_id(story_id):
    for story in stories_data['stories']:
        if story['id'] == story_id:
            return story['text']
    return "История не найдена."

# Получение ответа по ID
def get_answer_by_id(answer_id, is_good_answer):
    if is_good_answer:
        for answer in good_answers_data['answers']:
            if answer['id'] == answer_id:
                return answer['text']
    else:
        for answer in bad_answers_data['answers']:
            if answer['id'] == answer_id:
                return answer['text']
    return "Ответ не найден."

# Обработка запроса на команду
def handle_command(discord_id):
    users_data = load_users()
    user_found = False

    for user in users_data['users']:
        if user['iddiscord'] == discord_id:
            user_found = True
            # Проверяем флаг today
            if user['today'] == 0:
                # Генерация случайного числа для выбора истории
                story_id = random.randint(0, 50)
                story = get_story_by_id(story_id)
                print(f"История с ID {story_id}: {story}")

                # Генерация случайного числа для определения качества ответа
                roll = random.randint(0, 100)
                print(roll)
                is_good_answer = roll > 50

                # Генерация случайного числа для выбора ответа
                answer_id = random.randint(0, 24)
                answer = get_answer_by_id(answer_id, is_good_answer)

                # Вывод результата
                if is_good_answer:
                    print(f"Хороший ответ (ID {answer_id}): {answer}")
                    user['balansemorale'] += 5  # Добавляем 5 очков морали
                else:
                    print(f"Плохой ответ (ID {answer_id}): {answer}")
                    user['balansemorale'] -= 5

                # Обновление today
                # user['today'] = 1
            else:
                print("Сегодня вы уже использовали команду.")
            break

    if not user_found:
        # Если пользователь не найден, добавляем его
        new_user = {
            "iddiscord": discord_id,
            "today": 0,
            "balansemorale": 0
        }
        users_data['users'].append(new_user)
        print("Пользователь добавлен.")

    save_users(users_data)

# Пример использования
handle_command("1234567890")  # Замените на ID пользователя Discord
