import json
import random
import configparser
import disnake
from disnake.ext import commands
from disnake import Button, ActionRow
import asyncio
import os
config = configparser.ConfigParser()
config.read('config.ini')

token = config['Settings']['token']
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
with open('stories3.json', 'r', encoding='utf-8') as file:
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
        await text_channel_pvp.send(embed=embed)
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
        if message.author.id == 229665604372660226:
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
    if message.content == '!!!offstory':
        if message.author.id == 229665604372660226:
            try:
                await message.channel.send('Приложение Выключено!')
                os._exit(0)
            except Exception as e:
                await message.channel.send('Не удалось перезапустить приложение! Ломаю его нах')
                exit(0)
    if message.channel not in [text_channel_story, text_channel_pvp]:
        return
    if message.content.startswith('!story') and message.channel == text_channel_story:
        # await message.reply("Вы запросили историю!")
        discord_id = message.author.id
        users_data = load_users()  # Загружаем данные пользователей
        user = check_user_in_file(users_data, discord_id)

        if user:
            if user['today'] == 0:
                # Генерация случайного числа для выбора истории
                story_id = random.randint(0, 19)
                story = get_story_by_id(story_id)

                if story is None:
                    print(f"История с ID {story_id} не найдена.")
                    return

                # Генерация случайного числа для определения качества ответа
                roll = random.randint(0, 100) + user["lucky"]

                original_roll = roll
                roll_message = f" <@{discord_id}> Вы выбросили значение **{roll}** (с учетом удачи: **{user['lucky']}**)."
                if roll <= 49:
                    if user['badtry'] == 4:
                        roll = random.randint(60, 85)
                        user['badtry'] = 0
                        roll_message = f" <@{discord_id}> Вы выбросили значение **{original_roll}** (с учетом удачи: **{user['lucky']}**, но благодаря вашему спас-броску оно увеличилось до **{roll}**. Спас броски обнулены!"

                embed = disnake.Embed(title=f"Расчет броска", description=roll_message, color=0x0000FF)
                await message.reply(embed=embed)

                answer_id = random.randint(0, 2)

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
                embed = disnake.Embed(title=f"Случайная история", description=f"<@{discord_id}>" + story["text"],
                                      color=embed_color)
                embed.add_field(name="Результат", value=result_message, inline=False)

                # Добавляем информацию о полученных или отнятых очках
                points_message = f"{'Получено' if is_good_answer else 'Отнято'} **{random_balance}** очков\n"
                points_message += f"Ваш текущий баланс морали: **{user['balansemorale']}**\n"
                embed.add_field(name="Очки морали", value=points_message, inline=False)

                embed.add_field(name="Автор истории", value=story["Author"], inline=False)

                # Создаем кнопки
                buttonprofile = disnake.ui.Button(label="Мой профиль", style=disnake.ButtonStyle.green,
                                            custom_id=f"{message.id}_{discord_id}_buttonprofile")
                # button2 = disnake.ui.Button(label="", style=disnake.ButtonStyle.red,
                #                             custom_id=f"{discord_id}_button2")

                # Создаем представление с кнопками
                view = disnake.ui.View()
                view.add_item(buttonprofile)
                # view.add_item(button2)


                # Отправляем embed с кнопками
                await message.reply(embed=embed, view=view)

                # Обновление today
                user['today'] = 1

                # Сохраняем изменения в файле
                save_users(users_data)

            else:
                embed = disnake.Embed(title=f"ОТКАЗ!",
                                      description=f"<@{discord_id}> Сегодня вы уже использовали команду", color=0x000000)
                await message.reply(embed=embed)
        else:
            print("Пользователь не найден, что-то пошло не так.")

    if message.content.startswith('!cleartoday'):
        if message.author.id == 229665604372660226:
            await reset_today_value()
            await message.reply("Таймер сброшен!")
    if message.content.startswith('!clearbalanse'):
        if message.author.id == 229665604372660226:
            await clearbalanse()
            await message.reply("Баланс обнулен!")
    # if message.content.startswith('!me'):
    #     users_data = load_users()  # Загружаем данные пользователей
    #     user = check_user_in_file(users_data, message.author.id)
    #
    #     # Создаем embed-сообщение
    #     embed = disnake.Embed(title="Информация о пользователе", color=0x00FF00)
    #
    #     # Добавляем поля с информацией о пользователе с стандартными названиями ключей
    #     embed.add_field(name="ID Discord", value=user['iddiscord'], inline=False)
    #     allowed_message = "Да" if user['today'] == 0 else "Нет"
    #     embed.add_field(name="Разрешено запросить историю", value=allowed_message, inline=False)
    #     embed.add_field(name="Баланс морали (balansemorale)", value=user['balansemorale'], inline=False)
    #     embed.add_field(name="Броня (armor)", value=user['armor'], inline=False)
    #     embed.add_field(name="Сила (strong)", value=user['strong'], inline=False)
    #     embed.add_field(name="Ловкость (agility)", value=user['agility'], inline=False)
    #     embed.add_field(name="Здоровье (health)", value=user['health'], inline=False)
    #     embed.add_field(name="Боевой дух (health_pvp)", value=user['health_pvp'], inline=False)
    #     embed.add_field(name="Удача (lucky)", value=user['lucky'], inline=False)
    #     embed.add_field(name="Неудачные попытки", value=user['badtry'], inline=False)
    #
    #     # Отправляем embed-сообщение в канал
    #     await message.reply(embed=embed)
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
    if message.content.startswith("!buyagility"):
        users_data = load_users()  # Загружаем данные пользователей
        user = check_user_in_file(users_data, message.author.id)


        if user["agility"] >= 15:
            await message.reply("У вас уже максимальное значение ловкости (15). Нельзя увеличить ловкость больше.")
            return


        if user['balansemorale'] >= 50:
            user['balansemorale'] -= 50
            user['agility'] += 1  #
            await message.reply(
                f"Ваша Ловкость увеличена до {user['agility']}! Баланс морали теперь {user['balansemorale']}.")
        else:
            await message.reply("Недостаточно очков морали для увеличения ловкости. Вам нужно как минимум 50 очков.")

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
        except IndexError:
            await message.reply("Пожалуйста, упомяните пользователя.")
            return

        if member == message.author:
            await message.reply("Китайская мудрость гласит, что бить себя очень плохо.")
            return

        users_data = load_users()  # Загружаем данные пользователей

        ds_id_initiator = message.author.id
        ds_id_consumer = member_id  # Здесь указано упомянутое лицо

        initiator = check_user_in_file(users_data, ds_id_initiator)
        consumer = check_user_in_file(users_data, ds_id_consumer)

        initiator["canpvp"] = 1
        consumer["canpvp"] = 1

        if initiator["canpvp"] == 0 or initiator["health_pvp"] < 1:
            await message.reply(f"Атакующий <@{initiator['iddiscord']}> не готов к сражению.")
            return
        if consumer["canpvp"] == 0 or consumer["health_pvp"] < 1:
            await message.reply(f"Защищающийся <@{consumer['iddiscord']}> не готов к сражению.")
            return



        raund = 0
        while initiator["health_pvp"] > 0 or consumer["health_pvp"] > 0:
            # Бросок на промах для инициатора
            attack_roll_initiator = random.randint(0, 100)
            attack_roll_initiator += initiator['agility']
            if attack_roll_initiator < 25:
                damage_initiator = 0
                attack_result_initiator = (f"Ваш боевой дух: {initiator['health_pvp']} \n "
                                          f"Ваша ловкость: {initiator['agility']} \n "
                                          f"**Вы промахнулись при атаке**\n")
            else:
                # Бросок атаки
                dps = random.randint(20, 105)
                damage_initiator = dps + initiator["strong"] - consumer["armor"]
                attack_result_initiator = (f"Чистая атака:      {dps} \n"
                                           f"Ваш модификатор атаки: {initiator['strong']} \n"
                                           f"Защита противника: {consumer['armor']} \n "
                                           f"Ваш боевой дух: {initiator['health_pvp']} \n "
                                           f"Ваша ловкость: {initiator['agility']} \n "
                                           f"Ваш итоговый урон: {max(damage_initiator, 0)} \n")



            # Бросок на промах для защитника
            attack_roll_consumer = random.randint(0, 100)
            attack_roll_consumer += initiator['agility']
            if attack_roll_consumer < 25:
                damage_consumer = 0
                attack_result_consumer = (f"Ваш боевой дух: {consumer['health_pvp']} \n "
                                          f"Ваша ловкость: {consumer['agility']} \n "
                                          f"**Вы промахнулись при атаке**\n")
            else:
                # Бросок атаки
                dps = random.randint(40, 130)
                damage_consumer = dps + consumer["strong"] - initiator["armor"]


                attack_result_consumer = (f"Чистая атака:      {dps} \n"
                                          f"Ваш модификатор атаки: {consumer['strong']} \n"
                                          f"Защита противника: {initiator['armor']} \n"
                                          f"Ваш боевой дух: {consumer['health_pvp']} \n "
                                          f"Ваша ловкость: {consumer['agility']} \n "
                                          f"Итоговый урон:     {max(damage_consumer, 0)} \n")

            consumer["health_pvp"] -= max(damage_initiator, 0)
            initiator["health_pvp"] -= max(damage_consumer, 0)

            # Создаем новый Embed для текущего раунда
            raund += 1
            round_embed = disnake.Embed(title=f"Результат раунда {raund}", color=disnake.Color.blue())
            round_embed.add_field(name=f"**{message.author.nick}**", value=f"{attack_result_initiator}", inline=False)
            round_embed.add_field(name=f"**{member.nick}**", value=f"{attack_result_consumer}", inline=False)
            round_embed.add_field(name=f"**Результат**", value=f"У <@{initiator['iddiscord']}> осталось боевого духа: **{initiator['health_pvp']}** \n"
                                                               f"У <@{consumer['iddiscord']}> осталось боевого духа: **{consumer['health_pvp']}** ",
                                                                inline=False)

            await message.channel.send(embed=round_embed)

            if initiator["health_pvp"] <= 0 or consumer["health_pvp"] <= 0:
                break

        # Итоговый Embed
        final_embed = disnake.Embed(title="Финал PvP", color=disnake.Color.green())
        if initiator["health_pvp"] > consumer["health_pvp"]:
            final_embed.description = f"Победил {message.author.nick} с {initiator['health_pvp']} боевого духа!"
            initiator["balansemorale"] += 1
            consumer["balansemorale"] -= 1
            # Добавляем сообщения об изменении очков
            final_embed.add_field(name="***----***",
                                  value=f"<@{initiator['iddiscord']}> Очки добавлены: **1** Текущий баланс: **{initiator['balansemorale']}**\n"
                                        f"<@{consumer['iddiscord']}> Очки вычтены: **1** Текущий баланс: **{consumer['balansemorale']}**",
                                  inline=False)

        else:
            final_embed.description = f"Победил {member.nick} с {consumer['health_pvp']} боевого духа!"
            consumer["balansemorale"] += 1
            initiator["balansemorale"] -= 1
            final_embed.add_field(name="***----***",
                                  value=f"<@{consumer['iddiscord']}> Очки добавлены: **1** Текущий баланс: **{consumer['balansemorale']}**\n"
                                        f"<@{initiator['iddiscord']}> Очки вычтены: **1** Текущий баланс: **{initiator['balansemorale']}**",
                                  inline=False)

        round_embed.add_field(name=f"**{message.author.nick}**", value=f"{attack_result_initiator}", inline=False)

        await message.channel.send(embed=final_embed)

        initiator["canpvp"] = 0
        consumer["canpvp"] = 0

        save_users(users_data)  # Сохраняем изменения в файле


@bot.event
async def on_button_click(interaction: disnake.MessageInteraction):
    message_id = interaction.data['custom_id'].split('_')[0]  # Получаем ID сообщения, на которое был ответ
    message = await interaction.channel.fetch_message(message_id)
    discord_id = interaction.data['custom_id'].split('_')[1]  # Получаем ID пользователя из custom_id
    button_name = interaction.data['custom_id'].split('_')[2]  # Получаем имя кнопки из custom_id



    if interaction.user.id == int(discord_id):  # Проверяем, что нажал тот, кому адресован embed
        # await interaction.response.send_message(f"Вы нажали {button_name}!", ephemeral=True)
        profile = await get_profile(message)
        print(f"нажатие на кнопку {button_name}")
        await interaction.response.send_message(embed=profile, ephemeral=True)

    else:
        await interaction.response.send_message("Эта кнопка не для вас!", ephemeral=True)



async def get_profile(message):
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
    embed.add_field(name="Ловкость (agility)", value=user['agility'], inline=False)
    embed.add_field(name="Здоровье (health)", value=user['health'], inline=False)
    embed.add_field(name="Боевой дух (health_pvp)", value=user['health_pvp'], inline=False)
    embed.add_field(name="Удача (lucky)", value=user['lucky'], inline=False)
    embed.add_field(name="Неудачные попытки", value=user['badtry'], inline=False)

    # Отправляем embed-сообщение в канал
    return embed



#region служебная работа с Json
# Загрузка данных пользователей из users.json
def load_users():
    try:
        with open('users.json', 'r', encoding='utf-8') as file:
            users_data = json.load(file)
            # Проверяем, если структура не соответствует ожиданиям
            if 'users' not in users_data:
                print("Ключ 'users' отсутствует. Создаем его с базовой структурой.")
                users_data = {'users': []}  # Создаем новую структуру
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
    try:
        with open('users.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print("Данные успешно сохранены...")
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")


#endregion

def check_user_in_file(users_data, discord_id):
    # Определяем базовую структуру пользователя
    base_user_structure = {
        "iddiscord": discord_id,
        "today": 0,
        "balansemorale": 1,
        "armor": 0,
        "strong": 0,
        "health": 100,
        "health_pvp": 100,
        "agility": 0,
        "lucky": 0,
        "badtry": 0,
        "canpvp": 0
    }

    # Проверяем существование пользователя
    for user in users_data['users']:
        if user['iddiscord'] == discord_id:
            # Обновляем структуру пользователя, если какие-то ключи отсутствуют
            for key in base_user_structure.keys():
                if key not in user:
                    user[key] = base_user_structure[key]
            save_users(users_data)  # Сохраняем обновленные данные
            return user  # Возвращаем существующего пользователя

    # Если пользователь не найден, добавляем нового
    users_data['users'].append(base_user_structure)
    save_users(users_data)  # Сохраняем изменения
    return base_user_structure  # Возвращаем нового пользователя


# Проверяем структуру пользователя, что в ней есть все ключи/////
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
        "agility": 0,
        "lucky": 0,
        "badtry": 0,
        "canpvp": 0
    }

    # Проверяем каждый ключ
    for key, default_value in required_keys.items():
        if key not in user:
            user[key] = default_value  # Добавляем недостающий ключ с базовым значением

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
        # ensure_user_keys(user)
        user['today'] = 0  # Устанавливаем today в 0
        if user['health'] > 150:
            user['health'] = 150
        user['health_pvp'] = user['health']

    save_users(users_data)  # Сохраняем изменения

async def clearbalanse():
    users_data = load_users()

    for user in users_data['users']:
        user['balansemorale'] = 0  # Устанавливаем today в 0

    save_users(users_data)  # Сохраняем изменения


# Обработка запроса на команду story
async def handle_command(discord_id):
    users_data = load_users()  # Загружаем данные пользователей
    user = check_user_in_file(users_data, discord_id)

    if user:
        if user['today'] == 0:
            # Генерация случайного числа для выбора истории
            story_id = random.randint(0, 19)
            story = get_story_by_id(story_id)

            if story is None:
                print(f"История с ID {story_id} не найдена.")
                return

            # Генерация случайного числа для определения качества ответа
            roll = random.randint(0, 100) + user["lucky"]

            original_roll = roll
            roll_message = f" <@{discord_id}> Вы выбросили значение **{roll}** (с учетом удачи: **{user['lucky']}**)."
            if roll <= 49:
                if user['badtry'] == 4:
                    roll = random.randint(60, 85)
                    user['badtry'] = 0
                    roll_message = f" <@{discord_id}> Вы выбросили значение **{original_roll}** (с учетом удачи: **{user['lucky']}**, но благодаря вашему спас-броску оно увеличилось до **{roll}**. Спас броски обнулены!"

            embed = disnake.Embed(title=f"Расчет броска", description=roll_message, color=0x0000FF)
            await text_channel_story.send(embed=embed)

            answer_id = random.randint(0, 2)

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

            # Создаем кнопки
            button1 = Button(label="Кнопка 1", custom_id="button1")
            button2 = Button(label="Кнопка 2", custom_id="button2")


            await text_channel_story.send(embed=embed)

            # Обновление today
            user['today'] = 1

            # Сохраняем изменения в файле
            save_users(users_data)

        else:
            embed = disnake.Embed(title=f"ОТКАЗ! <@{discord_id}>", description="Сегодня вы уже использовали команду", color=0x000000)
            await text_channel_story.send(embed=embed)
    else:
        print("Пользователь не найден, что-то пошло не так.")



bot.run(token)








