import json
import random
import configparser
import disnake
from disnake.ext import commands
import asyncio
config = configparser.ConfigParser()
config.read('config.ini')

token = config['Settings']['token']
audit_chanel = config['Settings']['audit_chanel']
text_channel = 0 #Переопределяемый id канала для вывода сообщений


# Создаем экземпляр бота с включенным intent для содержимого сообщений
intents = disnake.Intents.default()
command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('!'),
    intents=intents.all(),
    command_sync_flags=command_sync_flags
)


@bot.event
async def on_ready():
    global text_channel
    for guild in bot.guilds:
        server_id = guild.id
        print(guild.id)
        permissions = guild.me.guild_permissions
        print(f"Права бота: {permissions}")
    try:
        text_channel = bot.get_guild(server_id).get_channel(int(audit_chanel))
        print(f"Канал для вывода сообщений бота найден, это: {text_channel.name} id:{text_channel.id} ")
    except:
        print("Канал для вывода не найден, сообщения будут выводиться в консоль!")

    print(f'Бот {bot.user} успешно запущен')
    print("Команды бота:")
    for command in bot.all_slash_commands:
        print(f"- {command}")

    # Запуск нового потока для выполнения reset_today_value() каждые 3 часа
    bot.loop.create_task(reset_value_periodically())


async def reset_value_periodically():
    while True:
        await reset_today_value()  # Выполнение функции
        embed = disnake.Embed(title="ТАЙМЕР СБРОШЕН!", description="Сброс таймера. Вы можете повторно запросить историю!", color=0x000000)
        await text_channel.send(embed=embed)
        # await asyncio.sleep(3 * 60 * 60)  # Ожидание 3 часа (3 * 60 минут * 60 секунд)
        await asyncio.sleep(60 * 60)  # Ожидание 1 час (60 минут * 60 секунд)


    # server_id = 1123685142255390781
    # server = bot.get_guild(int(server_id))
    # if server:
    #     try:
    #         await server.leave()
    #         print('Бот покинул сервер!')
    #     except:
    #         pass



@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.author.bot:  # Проверяем, является ли автор сообщения ботом
        return
    if message.channel != text_channel:
        return
    if message.content.startswith('!story'):
        await message.reply("Вы запросили историю!")
        await handle_command(message.author.id)

    if message.content.startswith('!mymorale'):
        await message.reply(get_user_balance(message.author.id))
    if message.content.startswith('!cleartoday'):
        await reset_today_value()
        await message.reply("Таймер сброшен!")

    # if message.content.startswith('!!!ArkinorOFF'):
    #         server_id = message.content.split(' ')[1]  # Получаем ID сервера из сообщения
    #
    #         #server_id = 1123685142255390781
    #         server = bot.get_guild(int(server_id))
    #         if server:
    #
    #             await server.leave()
    #             try:
    #                 await message.channel.send('Бот покинул сервер!')
    #             except:
    #                 print('Бот покинул сервер!')
    #         else:
    #             await message.channel.send('Сервер не найден')



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
            users_data = json.load(file)
            # Проверяем, если структура не соответствует ожиданиям
            if 'users' not in users_data:
                raise json.JSONDecodeError("Отсутствует ключ 'users'", '', 0)  # Исключение для обработки
            return users_data
    except FileNotFoundError:
        # Если файл не найден, создаем его с базовой структурой
        initial_data = {"users": []}
        save_users(initial_data)  # Сохраняем базовую структуру в файл
        return initial_data
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON: {e}. Создаем новый файл с базовой структурой.")
        initial_data = {"users": []}
        save_users(initial_data)  # Сохраняем базовую структуру в файл
        return initial_data

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

# проверим что пользователь существует
def check_user_in_file(discord_id):
    """
    Проверяет, существует ли пользователь с заданным discord_id в файле.

    :param discord_id: ID пользователя в Discord
    :return: True, если пользователь найден; False в противном случае
    """
    users_data = load_users()  # Загружаем данные пользователей
    user_dict = {user['iddiscord']: user for user in users_data['users']}

    return discord_id in user_dict  # Проверяем наличие id в словаре
# # Проверяем что пользователь может сегодня просить историю
# def user_can_ask(discord_id):
#     users_data = load_users()
#     user_dict = {user['iddiscord']: user for user in users_data['users']}
#     user = user_dict.get(discord_id)
#
#     if user is not None:
#         return user['today'] == 0  # Возвращаем True, если today == 0, и False, если today == 1

# Добавляем пользователя
def add_user(discord_id):
    users_data = load_users()
    new_user = {
        "iddiscord": discord_id,
        "today": 0,
        "balansemorale": 0
    }
    users_data['users'].append(new_user)
    print("Пользователь добавлен.")

    save_users(users_data)
# Возвращает текущий баланс пользователя по его Discord ID.
def get_user_balance(discord_id):
    """
    Возвращает текущий баланс пользователя по его Discord ID.

    :param discord_id: ID пользователя в Discord
    :return: Баланс пользователя или сообщение об ошибке
    """
    users_data = load_users()  # Загружаем данные пользователей
    user = next((user for user in users_data['users'] if user['iddiscord'] == discord_id), None)

    if user:
        return user['balansemorale']  # Возвращаем баланс
    else:
        return "Пользователь не найден."  # Если пользователь не найден


# async def send_embed_message_story(story):
#     global text_channel
#     embed = disnake.Embed(title="Случайная история", description=f"{story}", color=0x800080)
#     await text_channel.send(embed=embed)
#
#
# async def send_embed_message_answer(answer,color):
#     global text_channel
#     embed = disnake.Embed(title="Результат ваших действий", description=f"{answer}", color=color)
#     await text_channel.send(embed=embed)


async def reset_today_value():
    users_data = load_users()

    for user in users_data['users']:
        user['today'] = 0  # Устанавливаем today в 0

    save_users(users_data)  # Сохраняем изменения



# Обработка запроса на команду
async def handle_command(discord_id):
    """
    Обрабатывает команду пользователя. Если пользователь не найден, добавляет его.

    :param discord_id: ID пользователя в Discord
    """
    if not check_user_in_file(discord_id):
        add_user(discord_id)  # Добавляем пользователя, если он не найден

    users_data = load_users()
    user = next((user for user in users_data['users'] if user['iddiscord'] == discord_id), None)

    if user:
        if user['today'] == 0:
            # Генерация случайного числа для выбора истории
            story_id = random.randint(0, 80)
            story = get_story_by_id(story_id)
            print(f"История с ID {story_id}: {story}")

            # Генерация случайного числа для определения качества ответа
            roll = random.randint(0, 100)
            print(roll)
            is_good_answer = roll > 50

            # Генерация случайного числа для выбора ответа
            answer_id = random.randint(0, 24)
            answer = get_answer_by_id(answer_id, is_good_answer)

            # Определяем цвет embed на основе качества ответа
            embed_color = 0x00FF00 if is_good_answer else 0xFF0000
            # Обновление баланса
            random_balance = random.randint(0, 10)
            if is_good_answer:
                user['balansemorale'] += random_balance  # Добавляем очки морали
            else:
                user['balansemorale'] -= random_balance

            # Формирование сообщения
            result_message = f"{answer}\n"


            # Формирование embed-сообщения
            embed = disnake.Embed(title="Случайная история", description=story, color=embed_color)
            embed.add_field(name="Результат", value=result_message, inline=False)

            # Добавляем информацию о полученных или отнятых очках
            points_message = f"{'Получено' if is_good_answer else 'Отнято'} **{random_balance}** очков\n"
            points_message += f"Ваш текущий баланс морали: **{user['balansemorale']}**\n"
            embed.add_field(name="Очки морали", value=points_message, inline=False)

            await text_channel.send(embed=embed)

            # Обновление today
            user['today'] = 1
        else:
            embed = disnake.Embed(title="ОТКАЗ!", description="Сегодня вы уже использовали команду", color=0x000000)
            await text_channel.send(embed=embed)
    else:
        print("Пользователь не найден, что-то пошло не так.")

    save_users(users_data)  # Сохраняем изменения в файле

# Пример использования
# handle_command("1234567898")  # Замените на ID пользователя Discord



bot.run(token)