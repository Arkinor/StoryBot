import json
import random
import configparser
import disnake
from disnake.ext import commands
from disnake import Button, ActionRow
import asyncio
import os
from datetime import datetime

config = configparser.ConfigParser()
config.read('config.ini')

token = config['Settings']['token']
text_channel_story_id = config['Settings']['text_channel_story']
text_channel_pvp_id = config['Settings']['text_channel_pvp']
text_channel_story = 0  # Переопределяемый id канала для вывода сообщений
text_channel_pvp = 0


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

# Максимальные значения статов
MAX_STATS = {
    "lucky": 15,
    "armor": 30,
    "strong": 32,
    "agility": 15,
    "health": 120
}


@bot.event
async def on_ready():
    global text_channel_story, text_channel_pvp
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
        embed = disnake.Embed(
            title="🔄 ТАЙМЕР СБРОШЕН!",
            description="Сброс таймера. Вы можете повторно запросить историю или устроить сражение!",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        await text_channel_story.send(embed=embed)
        await text_channel_pvp.send(embed=embed)
        # await asyncio.sleep(3 * 60 * 60)  # Ожидание 3 часа (3 * 60 минут * 60 секунд)
        await asyncio.sleep(60 * 60)  # Ожидание 1 час (60 минут * 60 секунд)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.author.bot:  # Проверяем, является ли автор сообщения ботом
        return

    # Административные команды
    if message.content.startswith('!leavestory'):
        if message.author.id == 229665604372660226:
            server_id = message.content.split(' ')[1]  # Получаем ID сервера из сообщения
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

    if message.content.startswith('!cleartoday'):
        if message.author.id == 229665604372660226:
            await reset_today_value()
            await message.reply("Таймер сброшен!")

    if message.content.startswith('!clearbalanse'):
        if message.author.id == 229665604372660226:
            await clearbalanse()
            await message.reply("Баланс обнулен!")

    # Основные команды
    if message.channel not in [text_channel_story, text_channel_pvp]:
        return

    if message.content.startswith('!story') and message.channel == text_channel_story:
        await handle_story_command(message)

    if message.content.startswith('!pvp') and message.channel == text_channel_pvp:
        await handle_pvp_command(message)

    if message.content.startswith('!profile') or message.content.startswith('!me'):
        await handle_profile_command(message)

    if message.content.startswith('!leaderboard') or message.content.startswith('!top'):
        await handle_leaderboard_command(message)

    if message.content.startswith('!help'):
        await handle_help_command(message)


async def handle_story_command(message):
    discord_id = message.author.id
    users_data = load_users()
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

            # Создаем красивый embed для броска
            roll_embed = disnake.Embed(
                title="🎲 Бросок удачи",
                description=f"<@{discord_id}> выбросил значение **{roll}** (база: {original_roll - user['lucky']} + удача: {user['lucky']})",
                color=0x3498db
            )
            await message.reply(embed=roll_embed)

            # Обработка спас-броска
            if roll <= 49:
                if user['badtry'] == 4:
                    roll = random.randint(60, 85)
                    user['badtry'] = 0
                    rescue_embed = disnake.Embed(
                        title="✨ Спас-бросок!",
                        description=f"Благодаря вашему спас-броску значение увеличилось до **{roll}**!",
                        color=0xf39c12
                    )
                    await message.channel.send(embed=rescue_embed)

            # Определение результата
            answer_id = random.randint(0, 2)
            if roll == 0:
                answer = story["neutralanswers"][answer_id]
                embed_color = 0x95a5a6
                random_balance = 0
                is_good_answer = False
                result_title = "⚪ Нейтральный исход"
            elif roll > 50:
                answer = story["goodanswers"][answer_id]
                embed_color = 0x2ecc71
                random_balance = random.randint(13, 17)
                user['balansemorale'] += random_balance
                is_good_answer = True
                result_title = "🟢 Успех!"
            else:
                answer = story["badanswers"][answer_id]
                embed_color = 0xe74c3c
                random_balance = random.randint(10, 17)
                user['balansemorale'] -= random_balance
                is_good_answer = False
                user['badtry'] += 1
                result_title = "🔴 Неудача"

            # Создаем основной embed истории
            embed = disnake.Embed(
                title="📖 Случайная история",
                description=story["text"],
                color=embed_color
            )
            embed.add_field(name=result_title, value=answer, inline=False)

            # Добавляем информацию об очках
            balance_change = f"{'🔼 Получено' if is_good_answer else '🔽 Потеряно'} **{random_balance}** очков морали\n"
            balance_change += f"💰 Текущий баланс: **{user['balansemorale']}**\n"
            if not is_good_answer and user['badtry'] > 0:
                balance_change += f"⚠️ Неудачных попыток подряд: **{user['badtry']}/4**"
            embed.add_field(name="📊 Изменения", value=balance_change, inline=False)

            embed.add_field(name="✍️ Автор", value=story["Author"], inline=False)
            embed.set_footer(text="Нажмите кнопку ниже чтобы посмотреть профиль")

            # Создаем кнопки
            view = disnake.ui.View()
            view.add_item(disnake.ui.Button(
                label="👤 Мой профиль",
                style=disnake.ButtonStyle.primary,
                custom_id=f"{message.id}_{discord_id}_profile"
            ))
            view.add_item(disnake.ui.Button(
                label="📊 Топ игроков",
                style=disnake.ButtonStyle.secondary,
                custom_id=f"{message.id}_{discord_id}_leaderboard"
            ))

            await message.reply(embed=embed, view=view)
            user['today'] = 1
            save_users(users_data)

        else:
            embed = disnake.Embed(
                title="⏰ Лимит исчерпан",
                description=f"<@{discord_id}> Вы уже использовали команду сегодня. Попробуйте завтра!",
                color=0xe74c3c
            )
            await message.reply(embed=embed)
    else:
        print("Пользователь не найден, что-то пошло не так.")


async def handle_pvp_command(message):
    try:
        member = message.mentions[0]
        member_id = member.id
    except IndexError:
        embed = disnake.Embed(
            title="❌ Ошибка",
            description="Пожалуйста, упомяните пользователя для сражения.\nПример: `!pvp @username`",
            color=0xe74c3c
        )
        await message.reply(embed=embed)
        return

    if member == message.author:
        embed = disnake.Embed(
            title="🤔 Сомнительная идея",
            description="Китайская мудрость гласит, что бить себя очень плохо для психики.",
            color=0xf39c12
        )
        await message.reply(embed=embed)
        return

    users_data = load_users()
    initiator = check_user_in_file(users_data, message.author.id)
    consumer = check_user_in_file(users_data, member_id)

    if initiator["health_pvp"] < 1:
        embed = disnake.Embed(
            title="❌ Не готов к бою",
            description=f"Атакующий <@{initiator['iddiscord']}> не готов к сражению. Боевой дух истощен!",
            color=0xe74c3c
        )
        await message.reply(embed=embed)
        return

    if consumer["health_pvp"] < 1:
        embed = disnake.Embed(
            title="❌ Противник не готов к бою",
            description=f"Защищающийся <@{consumer['iddiscord']}> не готов к сражению. Боевой дух истощен!",
            color=0xe74c3c
        )
        await message.reply(embed=embed)
        return

    # Детальный embed с параметрами бойцов
    embed = disnake.Embed(
        title="⚔️ ВЫЗОВ НА ДУЭЛЬ",
        description=f"<@{initiator['iddiscord']}> вызывает на бой <@{consumer['iddiscord']}>!",
        color=0xe74c3c
    )

    # Детальная информация об атакующем
    initiator_stats = f"""
    ❤️ **Боевой дух:** {initiator['health_pvp']}
    💪 **Сила:** {initiator['strong']}
    🛡️ **Броня:** {initiator['armor']}
    🐆 **Ловкость:** {initiator['agility']}
    """
    # 🎲 **Удача:** {initiator['lucky']}
    # Детальная информация о защитнике
    consumer_stats = f"""
    ❤️ **Боевой дух:** {consumer['health_pvp']}
    💪 **Сила:** {consumer['strong']}
    🛡️ **Броня:** {consumer['armor']}
    🐆 **Ловкость:** {consumer['agility']}
    """

    embed.add_field(name=f"⚡ {message.author.display_name}", value=initiator_stats, inline=True)
    embed.add_field(name=f"🛡️ {member.display_name}", value=consumer_stats, inline=True)

    # Механика боя (соответствует оригинальной)
    mechanics_info = """
    **📊 Механика боя:**
    • **Промах:** бросок 0-100 + ловкость < 25
    • **Чистая атака:** 20-105 урона + сила - броня
    """
    embed.add_field(name="🎯 Правила боя", value=mechanics_info, inline=False)

    await message.reply(embed=embed)
    await asyncio.sleep(3)

    # Бой - ВОССТАНАВЛИВАЕМ ОРИГИНАЛЬНУЮ ЛОГИКУ
    raund = 0
    initiator_hp = initiator['health_pvp']
    consumer_hp = consumer['health_pvp']

    while initiator_hp > 0 and consumer_hp > 0:
        raund += 1

        # Бросок на промах для инициатора (оригинальная логика)
        attack_roll_initiator = random.randint(0, 100)
        attack_roll_initiator += initiator['agility']

        if attack_roll_initiator < 25:
            # Промах
            damage_initiator = 0
            attack_details_initiator = f"""
            **🎯 Бросок попадания:** {attack_roll_initiator - initiator['agility']} + {initiator['agility']} ловкость = {attack_roll_initiator}
            **❌ Результат:** ПРОМАХ (нужно ≥ 25)
            **💥 Урон:** 0
            """
        else:
            # Попадание - ОРИГИНАЛЬНЫЕ ДИАПАЗОНЫ
            dps = random.randint(20, 105)
            damage_initiator = max(dps + initiator["strong"] - consumer["armor"], 0)
            attack_details_initiator = f"""
            **🎯 Бросок попадания:** {attack_roll_initiator - initiator['agility']} + {initiator['agility']} ловкость = {attack_roll_initiator}
            **✅ Результат:** ПОПАДАНИЕ
            **⚔️ Урон:** {dps} (чистая атака) + {initiator['strong']} сила - {consumer['armor']} броня = {damage_initiator}
            """

        # Бросок на промах для защитника (оригинальная логика)
        attack_roll_consumer = random.randint(0, 100)
        attack_roll_consumer += consumer['agility']

        if attack_roll_consumer < 25:
            # Промах
            damage_consumer = 0
            attack_details_consumer = f"""
            **🎯 Бросок попадания:** {attack_roll_consumer - consumer['agility']} + {consumer['agility']} ловкость = {attack_roll_consumer}
            **❌ Результат:** ПРОМАХ (нужно ≥ 25)
            **💥 Урон:** 0
            """
        else:
            # Попадание - ОРИГИНАЛЬНЫЕ ДИАПАЗОНЫ
            dps = random.randint(20, 105)
            damage_consumer = max(dps + consumer["strong"] - initiator["armor"], 0)
            attack_details_consumer = f"""
            **🎯 Бросок попадания:** {attack_roll_consumer - consumer['agility']} + {consumer['agility']} ловкость = {attack_roll_consumer}
            **✅ Результат:** ПОПАДАНИЕ
            **⚔️ Урон:** {dps} (чистая атака) + {consumer['strong']} сила - {initiator['armor']} броня = {damage_consumer}
            """

        # Применение урона (оригинальная логика)
        old_consumer_hp = consumer_hp
        old_initiator_hp = initiator_hp
        consumer_hp = max(consumer_hp - damage_initiator, 0)
        initiator_hp = max(initiator_hp - damage_consumer, 0)

        # Создаем детальный embed для раунда
        round_embed = disnake.Embed(
            title=f"⚔️ РАУНД {raund}",
            description="Результаты атаки в этом раунде:",
            color=0xf39c12
        )

        # Атака инициатора
        round_embed.add_field(
            name=f"🎯 АТАКА: {message.author.display_name}",
            value=attack_details_initiator +
                  f"\n**❤️ Боевой дух:** {old_consumer_hp} → {consumer_hp} " +
                  (f"(-{damage_initiator})" if damage_initiator > 0 else ""),
            inline=False
        )

        # Атака защитника
        round_embed.add_field(
            name=f"🎯 АТАКА: {member.display_name}",
            value=attack_details_consumer +
                  f"\n**❤️ Боевой дух:** {old_initiator_hp} → {initiator_hp} " +
                  (f"(-{damage_consumer})" if damage_consumer > 0 else ""),
            inline=False
        )

        # Итог раунда
        status_initiator = "💀 ПОРАЖЕНИЕ" if initiator_hp <= 0 else "⚡ В БОЮ"
        status_consumer = "💀 ПОРАЖЕНИЕ" if consumer_hp <= 0 else "⚡ В БОЮ"

        round_embed.add_field(
            name="📊 ИТОГ РАУНДА",
            value=f"**{message.author.display_name}:** {initiator_hp} HP - {status_initiator}\n" +
                  f"**{member.display_name}:** {consumer_hp} HP - {status_consumer}",
            inline=False
        )

        await message.channel.send(embed=round_embed)
        await asyncio.sleep(3)

        # Проверка конца боя
        if initiator_hp <= 0 or consumer_hp <= 0:
            break

    # Определение победителя (оригинальная логика наград)
    if initiator_hp > consumer_hp:
        winner = message.author
        loser = member
        winner_data = initiator
        loser_data = consumer
        winner_hp = initiator_hp
        # ОРИГИНАЛЬНЫЕ НАГРАДЫ: +1/-1
        winner_data['balansemorale'] += 1
        loser_data['balansemorale'] -= 1
    else:
        winner = member
        loser = message.author
        winner_data = consumer
        loser_data = initiator
        winner_hp = consumer_hp
        # ОРИГИНАЛЬНЫЕ НАГРАДЫ: +1/-1
        winner_data['balansemorale'] += 1
        loser_data['balansemorale'] -= 1

    # Обновление статусов
    # initiator['today'] = 1
    # consumer['today'] = 1
    # initiator['health_pvp'] = initiator['health']
    # consumer['health_pvp'] = consumer['health']

    save_users(users_data)

    # Детальный финальный embed
    final_embed = disnake.Embed(
        title="🏆 БИТВА ЗАВЕРШЕНА!",
        description=f"**ПОБЕДИТЕЛЬ:** {winner.mention}\n**С боевым духом:** {winner_hp}⚡",
        color=0x2ecc71
    )

    final_embed.add_field(
        name="📊 РЕЗУЛЬТАТЫ БОЯ",
        value=f"**{message.author.display_name}:** {max(initiator_hp, 0)}⚡\n**{member.display_name}:** {max(consumer_hp, 0)}⚡",
        inline=True
    )

    final_embed.add_field(
        name="💰 ИЗМЕНЕНИЕ БАЛАНСА",
        value=f"**{winner.display_name}:** +1 очко\n**{loser.display_name}:** -1 очко",
        inline=True
    )

    final_embed.add_field(
        name="💳 НОВЫЕ БАЛАНСЫ",
        value=f"**{winner.display_name}:** {winner_data['balansemorale']} очков\n**{loser.display_name}:** {loser_data['balansemorale']} очков",
        inline=False
    )

    # final_embed.set_footer(text="Боевой дух восстановлен до максимума!")

    await message.channel.send(embed=final_embed)

async def handle_profile_command(message):
    users_data = load_users()
    user = check_user_in_file(users_data, message.author.id)

    embed = create_profile_embed(user, message.author)
    view = create_profile_view(message.id, message.author.id)

    await message.reply(embed=embed, view=view)


async def handle_leaderboard_command(message):
    users_data = load_users()

    # Сортируем пользователей по балансу
    sorted_users = sorted(users_data['users'], key=lambda x: x['balansemorale'], reverse=True)[:10]

    embed = disnake.Embed(
        title="🏆 ТОП ИГРОКОВ",
        description="Рейтинг игроков по очкам морали",
        color=0xf39c12
    )

    for i, user in enumerate(sorted_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        member = bot.get_user(user['iddiscord'])
        username = member.display_name if member else f"User{user['iddiscord']}"
        embed.add_field(
            name=f"{medal} {username}",
            value=f"**{user['balansemorale']}** очков морали",
            inline=False
        )

    embed.set_footer(text="Поднимайтесь в рейтинге, участвуя в историях и сражениях!")
    await message.reply(embed=embed)


async def handle_help_command(message):
    embed = disnake.Embed(
        title="📚 ПОМОЩЬ ПО КОМАНДАМ",
        description="Список доступных команд и их описание",
        color=0x3498db
    )

    embed.add_field(
        name="📖 Основные команды",
        value="""`!story` - Получить случайную историю
`!profile` или `!me` - Показать ваш профиль
`!leaderboard` - Показать топ игроков
`!help` - Показать это сообщение""",
        inline=False
    )

    embed.add_field(
        name="⚔️ PvP команды",
        value="`!pvp @username` - Вызвать игрока на дуэль",
        inline=False
    )

    embed.add_field(
        name="📝 Примечания",
        value="""• Вы можете получить только 1 историю в день
• PvP бои также доступны раз в день
• Участвуйте в активностях для повышения рейтинга""",
        inline=False
    )

    await message.reply(embed=embed)


def create_profile_embed(user, member):
    embed = disnake.Embed(
        title=f"👤 ПРОФИЛЬ {member.display_name}",
        color=0x9b59b6
    )

    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)

    # Основная информация
    embed.add_field(
        name="💰 Баланс",
        value=f"**{user['balansemorale']}** очков морали",
        inline=True
    )

    embed.add_field(
        name="🎯 Доступные действия",
        value="✅ Доступно" if user['today'] == 0 else "❌ Использовано",
        inline=True
    )

    embed.add_field(
        name="🎲 Удача",
        value=f"**{user['lucky']}/{MAX_STATS['lucky']}**",
        inline=True
    )

    # Статы с прогресс-баром
    stats_value = f"""
    ❤️ **Здоровье:** {user['health']}/{MAX_STATS['health']}
    {create_progress_bar(user['health'], MAX_STATS['health'])}

    💪 **Сила:** {user['strong']}/{MAX_STATS['strong']}
    {create_progress_bar(user['strong'], MAX_STATS['strong'])}

    🛡️ **Броня:** {user['armor']}/{MAX_STATS['armor']}
    {create_progress_bar(user['armor'], MAX_STATS['armor'])}

    🐆 **Ловкость:** {user['agility']}/{MAX_STATS['agility']}
    {create_progress_bar(user['agility'], MAX_STATS['agility'])}
    """

    embed.add_field(name="📊 ХАРАКТЕРИСТИКИ", value=stats_value, inline=False)

    # Дополнительная информация
    if user['badtry'] > 0:
        embed.add_field(
            name="⚠️ Статус",
            value=f"Неудачных попыток: **{user['badtry']}/4**",
            inline=True
        )

    embed.set_footer(text="Используйте кнопки ниже для улучшения характеристик")
    return embed


def create_progress_bar(current, maximum, length=10):
    filled = int((current / maximum) * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"`[{bar}]`"


def create_profile_view(message_id, user_id):
    view = disnake.ui.View()

    # Кнопки улучшения статов
    stats_buttons = [
        ("💪 Сила", "strong", 50),
        ("🛡️ Броня", "armor", 50),
        ("🐆 Ловкость", "agility", 50),
        ("🎲 Удача", "lucky", 50),
        ("❤️ Здоровье", "health", 50),
    ]

    for label, stat, cost in stats_buttons:
        view.add_item(disnake.ui.Button(
            label=label,
            style=disnake.ButtonStyle.primary,
            custom_id=f"{message_id}_{user_id}_buy_{stat}",
            emoji=label.split()[0]
        ))

    return view


@bot.event
async def on_button_click(interaction: disnake.MessageInteraction):
    custom_id_parts = interaction.data['custom_id'].split('_')
    message_id = custom_id_parts[0]
    discord_id = custom_id_parts[1]
    action = custom_id_parts[2]

    if interaction.user.id != int(discord_id):
        await interaction.response.send_message("Эта кнопка не для вас!", ephemeral=True)
        return

    users_data = load_users()
    user = check_user_in_file(users_data, interaction.user.id)

    if action == "profile":
        embed = create_profile_embed(user, interaction.user)
        view = create_profile_view(message_id, discord_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    elif action == "leaderboard":
        await handle_leaderboard_command(interaction)

    elif action == "buy":
        stat = custom_id_parts[3]
        await handle_buy_stat(interaction, user, stat, users_data)


async def handle_buy_stat(interaction, user, stat, users_data):
    max_value = MAX_STATS.get(stat, 0)
    current_value = user.get(stat, 0)
    cost = 50

    if current_value >= max_value:
        embed = disnake.Embed(
            title="❌ Максимальный уровень",
            description=f"Характеристика **{get_stat_name(stat)}** уже достигла максимума!",
            color=0xe74c3c
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if user['balansemorale'] < cost:
        embed = disnake.Embed(
            title="❌ Недостаточно очков",
            description=f"Для улучшения **{get_stat_name(stat)}** нужно {cost} очков морали!\nВаш баланс: {user['balansemorale']}",
            color=0xe74c3c
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Улучшение стата
    user[stat] += 1
    user['balansemorale'] -= cost
    save_users(users_data)

    embed = disnake.Embed(
        title="✅ Успешное улучшение!",
        description=f"Характеристика **{get_stat_name(stat)}** улучшена до **{user[stat]}/{max_value}**",
        color=0x2ecc71
    )
    embed.add_field(name="💰 Потрачено", value=f"**{cost}** очков морали", inline=True)
    embed.add_field(name="💳 Осталось", value=f"**{user['balansemorale']}** очков", inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=True)


def get_stat_name(stat_key):
    names = {
        "strong": "Сила",
        "armor": "Броня",
        "agility": "Ловкость",
        "lucky": "Удача",
        "health": "Здоровье"
    }
    return names.get(stat_key, stat_key)


# region служебная работа с Json
def load_users():
    try:
        with open('users.json', 'r', encoding='utf-8') as file:
            users_data = json.load(file)
            if 'users' not in users_data:
                print("Ключ 'users' отсутствует. Создаем его с базовой структурой.")
                users_data = {'users': []}
                save_users(users_data)
            return users_data
    except FileNotFoundError:
        initial_data = {"users": []}
        save_users(initial_data)
        return initial_data
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON: {e}. Создаем новый файл с базовой структурой.")
        initial_data = {"users": []}
        save_users(initial_data)
        return initial_data


def save_users(data):
    try:
        with open('users.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print("Данные успешно сохранены...")
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")


def check_user_in_file(users_data, discord_id):
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

    for user in users_data['users']:
        if user['iddiscord'] == discord_id:
            for key in base_user_structure.keys():
                if key not in user:
                    user[key] = base_user_structure[key]
            save_users(users_data)
            return user

    users_data['users'].append(base_user_structure)
    save_users(users_data)
    return base_user_structure


def ensure_user_keys(user):
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

    for key, default_value in required_keys.items():
        if key not in user:
            user[key] = default_value

    return user


def get_story_by_id(story_id):
    for story in stories_data['stories']:
        if story['id'] == story_id:
            return story
    return None


def get_user_balance(discord_id):
    users_data = load_users()
    user = check_user_in_file(users_data, discord_id)
    if user:
        return user['balansemorale']
    else:
        return "Пользователь не найден."


async def reset_today_value():
    users_data = load_users()

    for user in users_data['users']:
        user['today'] = 0
        if user['health'] > 150:
            user['health'] = 150
        user['health_pvp'] = user['health']

    save_users(users_data)


async def clearbalanse():
    users_data = load_users()

    for user in users_data['users']:
        user['balansemorale'] = 0

    save_users(users_data)


bot.run(token)