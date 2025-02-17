import json
import random
import configparser
import disnake
from disnake.ext import commands
import asyncio
config = configparser.ConfigParser()
config.read('config.ini')

# token = config['Settings']['token']
token = "MTIwMTk2MzAwMzU0MTQ1ODk0NA.G_Qk7u.t7HmYkqqNkiySue-ScCpf7jPp7i2XUYGl7hB94"
text_channel_story_id = config['Settings']['text_channel_story']
text_channel_pvp_id = config['Settings']['text_channel_pvp']
text_channel_story = 0 #Переопределяемый id канала для вывода сообщений
text_channel_pvp = 0
_lastroll = 20


# Создаем экземпляр бота с включенным intent для содержимого сообщений
intents = disnake.Intents.default()
command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('!'),
    intents=intents.all(),
    command_sync_flags=command_sync_flags
)

# Загрузка данных из JSON файлов
with open('stories2.json', 'r', encoding='utf-8') as file:
    stories_data = json.load(file)

@bot.event
async def on_ready():
    global text_channel_story,text_channel_pvp
    for guild in bot.guilds:
        server_id = guild.id
        print(guild.id)
        permissions = guild.me.guild_permissions
        print(f"Права бота: {permissions}")
    try:
        text_channel_story = bot.get_guild(server_id).get_channel(int(text_channel_story_id))
        text_channel_pvp = bot.get_guild(server_id).get_channel(int(text_channel_pvp_id))
        print(f"Канал для вывода сообщений бота найден, это: {text_channel_story.name} id:{text_channel_story.id} ")
        print(f"Канал для вывода сообщений бота найден, это: {text_channel_pvp.name} id:{text_channel_pvp.id} ")
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
        embed = disnake.Embed(title="ТАЙМЕР СБРОШЕН!", description="Сброс таймера. Вы можете повторно запросить историю или устроить сражение!", color=0x000000)
        await text_channel_story.send(embed=embed)
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
    if message.content.startswith('!leavestory'):
        server_id = message.content.split(' ')[1]  # Получаем ID сервера из сообщения

        # server_id = 1123685142255390781
        server = bot.get_guild(int(server_id))
        if server:
            await message.channel.send('Ариведерчи бейба!')
            await server.leave()
            try:
                await message.channel.send('Бот покинул сервер!')
            except:
                print('Бот покинул сервер!')
        else:
            await message.channel.send('Сервер не найден')
    if message.channel not in [text_channel_story, text_channel_pvp]:
        return
    if message.content.startswith('!story') and message.channel == text_channel_story:
        await message.reply("Вы запросили историю!")
        await handle_command(message.author.id)
    if message.content.startswith('!cleartoday'):
        if message.author.id == 229665604372660226:
            await reset_today_value()
            await message.reply("Таймер сброшен!")
    if message.content.startswith('!clearbalanse'):
        if message.author.id == 229665604372660226:
            await clearbalanse()
            await message.reply("Баланс обнулен!")
    if message.content.startswith('!me'):
        users_data = load_users()  # Загружаем данные пользователей
        user = check_user_in_file(users_data, message.author.id)

        # Создаем embed-сообщение
        embed = disnake.Embed(title="Информация о пользователе", color=0x00FF00)

        # Добавляем поля с информацией о пользователе с стандартными названиями ключей
        embed.add_field(name="ID Discord", value=user['iddiscord'], inline=False)
        allowed_message = "Да" if user['today'] == 0 else "Нет"
        embed.add_field(name="Разрешено запросить историю", value=allowed_message, inline=False)
        embed.add_field(name="Баланс морали (balansemorale)", value=user['balansemorale'], inline=False)
        embed.add_field(name="Броня (armor)", value=user['armor'], inline=False)
        embed.add_field(name="Сила (strong)", value=user['strong'], inline=False)
        embed.add_field(name="Здоровье (health)", value=user['health'], inline=False)
        embed.add_field(name="Боевой дух (health_pvp)", value=user['health_pvp'], inline=False)
        embed.add_field(name="Удача (lucky)", value=user['lucky'], inline=False)
        embed.add_field(name="Неудачные попытки", value=user['badtry'], inline=False)

        # Отправляем embed-сообщение в канал
        await message.reply(embed=embed)
    if message.content.startswith('!buylucky'):
        users_data = load_users()  # Загружаем данные пользователей
        user = check_user_in_file(users_data, message.author.id)

        # Проверяем, что удача меньше 10
        if user["lucky"] >= 15:
            await message.reply("У вас уже максимальное значение удачи (15). Нельзя увеличить удачу больше.")
            return

        # Проверяем, что баланс морали больше или равен 50
        if user['balansemorale'] >= 50:
            user['balansemorale'] -= 50  # Вычитаем 50 очков из баланса морали
            user['lucky'] += 1  # Увеличиваем удачу на 1
            await message.reply(
                f"Ваша удача увеличена до {user['lucky']}! Баланс морали теперь {user['balansemorale']}.")
        else:
            await message.reply("Недостаточно очков морали для увеличения удачи. Вам нужно как минимум 50 очков.")

        # Сохраняем изменения
        save_users(users_data)
    if message.content.startswith('!buyarmor'):
        users_data = load_users()  # Загружаем данные пользователей
        user = check_user_in_file(users_data, message.author.id)

        if user["armor"] >= 30:
            await message.reply("У вас уже максимальное значение брони (30). Нельзя увеличить броню больше.")
            return

        # Проверяем, что баланс морали больше или равен 50
        if user['balansemorale'] >= 50:
            user['balansemorale'] -= 50  # Вычитаем 50 очков из баланса морали
            user['armor'] += 1  # Увеличиваем удачу на 1
            await message.reply(
                f"Ваша броня увеличена до {user['armor']}! Баланс морали теперь {user['balansemorale']}.")
        else:
            await message.reply("Недостаточно очков брони для увеличения удачи. Вам нужно как минимум 50 очков.")

        # Сохраняем изменения
        save_users(users_data)
    if message.content.startswith('!buystrong'):
        users_data = load_users()  # Загружаем данные пользователей
        user = check_user_in_file(users_data, message.author.id)

        # Проверяем, что удача меньше 10
        if user["strong"] >= 32:
            await message.reply("У вас уже максимальное значение силы (32). Нельзя увеличить силу больше.")
            return

        # Проверяем, что баланс морали больше или равен 50
        if user['balansemorale'] >= 50:
            user['balansemorale'] -= 50  # Вычитаем 50 очков из баланса морали
            user['strong'] += 1  # Увеличиваем удачу на 1
            await message.reply(
                f"Ваша сила увеличена до {user['strong']}! Баланс морали теперь {user['balansemorale']}.")
        else:
            await message.reply("Недостаточно очков морали для увеличения силы. Вам нужно как минимум 50 очков.")

        # Сохраняем изменения
        save_users(users_data)
    if message.content.startswith('!buyhealth'):
        users_data = load_users()  # Загружаем данные пользователей
        user = check_user_in_file(users_data, message.author.id)

        # Проверяем, что удача меньше 10
        if user["health"] >= 120:
            await message.reply("У вас уже максимальное значение здоровье (120). Нельзя увеличить здоровье больше.")
            return

        # Проверяем, что баланс морали больше или равен 50
        if user['balansemorale'] >= 50:
            user['balansemorale'] -= 50  # Вычитаем 50 очков из баланса морали
            user['health'] += 1  # Увеличиваем удачу на 1
            await message.reply(
                f"Ваше здоровье увеличено до {user['health']}! Баланс морали теперь {user['balansemorale']}.")
        else:
            await message.reply("Недостаточно очков морали для увеличения здоровья. Вам нужно как минимум 50 очков.")

        # Сохраняем изменения
        save_users(users_data)
    if message.content.startswith('!pvptest') and message.channel == text_channel_pvp:
        try:
            member = message.mentions[0]
            member_id = member.id  # Получаем упомянутого участника
        except:
            return

        if member == message.author:
            await message.reply(f"Китайская мудрость гласит, что бить себя очень плохо")
            return
        users_data = load_users()  # Загружаем данные пользователей

        ds_id_initiator = message.author.id
        ds_id_consumer = member_id  # Здесь указано упомянутое лицо

        initiator = check_user_in_file(users_data, ds_id_initiator)
        consumer = check_user_in_file(users_data, ds_id_consumer)

        initiator["canpvp"] = 1
        consumer["canpvp"] = 1

        if initiator["canpvp"] == 0 or initiator["health_pvp"] < 1:
            await message.reply(f"Атакующий <@{initiator['iddiscord']}> не готов к сражению")
            return
        if consumer["canpvp"] == 0 or consumer["health_pvp"] < 1:
            await message.reply(f"Атакующий <@{consumer['iddiscord']}> не готов к сражению")
            return
        raund = 0
        while initiator["health_pvp"] > 0 and consumer["health_pvp"] > 0:
            # Бросок на промах для инициатора
            attack_roll_initiator = random.randint(0, 100)
            if attack_roll_initiator < 5:
                damage_initiator = 0
                attack_result_initiator = "промахнулся"
            else:
                # Бросок атаки
                damage_initiator = random.randint(15, 100) + initiator["strong"] - consumer["armor"]
                consumer["health_pvp"] -= max(damage_initiator, 0)
                attack_result_initiator = (f"Чистая атака: {random.randint(0, 130)} \n"
                                           f"Прибавляем ваше усиление атаки: {initiator['strong']} \n"
                                           f"Вычитаем защиту <@{consumer['iddiscord']}>: {consumer['armor']} \n "
                                           f"Ваш итоговый урон: {max(damage_initiator, 0)} \n"
                                           f"У <@{consumer['iddiscord']}> осталось боевого духа: {consumer['health_pvp']} после вашей атаки")

            # Бросок на промах для защитника
            attack_roll_consumer = random.randint(0, 100)
            if attack_roll_consumer < 5:
                damage_consumer = 0
                attack_result_consumer = "промахнулся"
            else:
                # Бросок атаки
                damage_consumer = random.randint(15, 100) + consumer["strong"] - initiator["armor"]
                initiator["health_pvp"] -= max(damage_consumer, 0)

                attack_result_consumer = (f"Чистая атака: {random.randint(0, 130)} \n"
                                          f"Прибавляем ваше усиление атаки: {consumer['strong']} \n"
                                          f"Вычитаем защиту <@{initiator['iddiscord']}>: {initiator['armor']} \n"
                                          f"Итоговый урон: {max(damage_consumer, 0)} \n"
                                          f"У <@{initiator['iddiscord']}> осталось боевого духа: {initiator['health_pvp']} после вашей атаки")

            # Создаем новый Embed для текущего раунда
            raund += 1
            round_embed = disnake.Embed(title=f"Результат раунда {raund}", color=disnake.Color.blue())
            round_embed.add_field(name=f"{message.author.nick}", value=f"{attack_result_initiator}", inline=False)
            round_embed.add_field(name=f"{member.nick}", value=f"{attack_result_consumer}", inline=False)

            await message.channel.send(embed=round_embed)

        # Итоговый Embed
        final_embed = disnake.Embed(title="Финал PvP", color=disnake.Color.green())
        if initiator["health_pvp"] > 0:
            final_embed.description = f"Победил {message.author.nick} с {initiator['health_pvp']} боевого духа!"
        else:
            final_embed.description = f"Победил {member.nick} с {consumer['health_pvp']} боевого духа!"

        await message.channel.send(embed=final_embed)

        initiator["canpvp"] = 0
        consumer["canpvp"] = 0

        save_users(users_data)  # Сохраняем изменения в файле


#region служебная работа с Json
# Загрузка данных пользователей из users.json
def load_users():
    try:
        with open('users.json', 'r', encoding='utf-8') as file:
            users_data = json.load(file)
            # Проверяем, если структура не соответствует ожиданиям
            if 'users' not in users_data:
                print("Ключ 'users' отсутствует. Создаем его с базовой структурой.")
                users_data['users'] = []  # Создаем ключ 'users' с пустым списком
                save_users(users_data)  # Сохраняем обновленную структуру в файл
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


# Добавляем пользователя
def add_user(discord_id):
    users_data = load_users()
    new_user = {
        "iddiscord": discord_id,
        "today": 0,
        "balansemorale": 1,
        "armor": 0,
        "strong": 0,
        "health": 100,
        "health_pvp": 100,
        "lucky": 0,
        "badtry": 0,
        "canpvp": 0

    }
    users_data['users'].append(new_user)
    print("Пользователь добавлен.")

    save_users(users_data)
    return users_data

#Проверям структуру пользователя что в ней есть все ключи
def ensure_user_keys(user):
    # Определяем необходимые ключи и их базовые значения
    required_keys = {
        "iddiscord": 0,
        "today": 0,
        "balansemorale": 1,
        "armor": 0,
        "strong": 0,
        "health": 100,
        "health_pvp": 100,
        "lucky": 0,
        "badtry": 0,
        "canpvp": 0
    }

    # Проверяем каждый ключ
    for key, default_value in required_keys.items():
        if key not in user:
            user[key] = default_value  # Добавляем недостающий ключ с базовым значением

    return user

#endregion




# проверим что пользователь существует если нет, создадим или проверим и допишем его структуру профиля
def check_user_in_file(users_data,discord_id):
    user = next((user for user in users_data['users'] if user['iddiscord'] == discord_id), None)

    if user == None:
        add_user(discord_id)
        users_data = load_users()
        user = next((user for user in users_data['users'] if user['iddiscord'] == discord_id), None)

    else:
        ensure_user_keys(user)
        user = next((user for user in users_data['users'] if user['iddiscord'] == discord_id), None)

        # Обновляем структуру users_data с изменениями в user
        for i in range(len(users_data['users'])):
            if users_data['users'][i]['iddiscord'] == user['iddiscord']:
                users_data['users'][i] = user
                break
        save_users(users_data)
    return user

# Получение истории по ID
def get_story_by_id(story_id):
    for story in stories_data['stories']:
        if story['id'] == story_id:
            return story
    return None

# Возвращает текущий баланс пользователя по его Discord ID.
def get_user_balance(discord_id):
    users_data = load_users()  # Загружаем данные пользователей
    user = check_user_in_file(users_data,discord_id)
    if user:
        return user['balansemorale']  # Возвращаем баланс
    else:
        return "Пользователь не найден."  # Если пользователь не найден

async def reset_today_value():
    users_data = load_users()

    for user in users_data['users']:
        ensure_user_keys(user)
        user['today'] = 0  # Устанавливаем today в 0
        user['health_pvp'] = user['health']

    save_users(users_data)  # Сохраняем изменения

async def clearbalanse():
    users_data = load_users()

    for user in users_data['users']:
        user['balansemorale'] = 0  # Устанавливаем today в 0

    save_users(users_data)  # Сохраняем изменения

async def pvp(message, ds_id_Initiator, ds_id_consumer):
    pass

# Обработка запроса на команду story
async def handle_command(discord_id):
    users_data = load_users()  # Загружаем данные пользователей
    user = check_user_in_file(users_data,discord_id)


    # Обновляем структуру users_data с изменениями в user
    for i in range(len(users_data['users'])):
        if users_data['users'][i]['iddiscord'] == user['iddiscord']:
            users_data['users'][i] = user
            break

    if user:
        if user['today'] == 0:
            # Генерация случайного числа для выбора истории
            story_id = random.randint(0, 59)
            story = get_story_by_id(story_id)

            if story is None:
                print(f"История с ID {story_id} не найдена.")
                return

            # Генерация случайного числа для определения качества ответа
            roll = random.randint(0, 100) + user["lucky"]

            #region защита от критической неудачи
            # global _lastroll
            # if _lastroll <= 10:
            #     roll = random.randint(53, 60)
            # _lastroll = roll
            #endregion

            #region Помогаем паталогическим неудачникам
            # if user['balansemorale'] <= 0:
            #     roll = roll + 5
            #endregion

            original_roll = roll
            roll_message = f" <@{discord_id}> Вы выбросили значение **{roll}** (с учетом удачи: **{user['lucky']}**)."
            if roll <= 49:
                if user['badtry'] == 4:
                    roll = random.randint(60, 85)
                    user['badtry'] = 0
                    roll_message = f" <@{discord_id}> Вы выбросили значение **{original_roll}** (с учетом удачи: **{user['lucky']}**, но благодаря вашему спас-броску оно увеличилось до **{roll}** Спас броски обнулены!"

            embed = disnake.Embed(title=f"Расчет броска", description=roll_message, color=0x0000FF)
            await text_channel_story.send(embed=embed)

            print(roll)
            answer_id = random.randint(0, 2)
            # random_balance = random.randint(1, 15)

            if roll == 0:
                answer = story["neutralanswers"][answer_id]
                embed_color = 0xFFFFFF
                random_balance = 0
                is_good_answer = False
            elif roll > 50:
                answer = story["goodanswers"][answer_id]
                embed_color = 0x00FF00
                random_balance = random.randint(13, 17)
                user['balansemorale'] += random_balance  # Добавляем очки морали
                is_good_answer = True
            else:
                answer = story["badanswers"][answer_id]
                embed_color = 0xFF0000
                random_balance = random.randint(10, 17)
                user['balansemorale'] -= random_balance  # Отнимаем очки морали
                is_good_answer = False
                user['badtry'] += 1

            # Формирование сообщения
            result_message = f"{answer}\n"

            # Формирование embed-сообщения
            embed = disnake.Embed(title=f"Случайная история", description=f"<@{discord_id}>" + story["text"], color=embed_color)
            embed.add_field(name="Результат", value=result_message, inline=False)

            # Добавляем информацию о полученных или отнятых очках
            points_message = f"{'Получено' if is_good_answer else 'Отнято'} **{random_balance}** очков\n"
            points_message += f"Ваш текущий баланс морали: **{user['balansemorale']}**\n"
            embed.add_field(name="Очки морали", value=points_message, inline=False)

            embed.add_field(name="Автор истории", value=story["Author"], inline=False)

            await text_channel_story.send(embed=embed)

            # Обновление today
            user['today'] = 1

        else:
            embed = disnake.Embed(title=f"ОТКАЗ! <@{discord_id}>", description="Сегодня вы уже использовали команду", color=0x000000)
            await text_channel_story.send(embed=embed)
    else:
        print("Пользователь не найден, что-то пошло не так.")

    save_users(users_data)  # Сохраняем изменения в файле



bot.run(token)








