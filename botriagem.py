import botriagem
import os
from discord.ext import commands

intents = botriagem.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# CONFIGURAÇÕES
ID_CANAL_TRIAGEM = 1361050940383428838
ID_CARGO_MEMBRO = 1360956462180077669

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Verifica se a mensagem foi no canal de triagem
    if message.channel.id != ID_CANAL_TRIAGEM:
        return

    # Filtra últimas mensagens do usuário no canal
    history = [msg async for msg in message.channel.history(limit=20)]
    user_msgs = [msg for msg in reversed(history) if msg.author == message.author]

    if len(user_msgs) < 2:
        return

    nome = user_msgs[-2].content.strip()
    passaporte = user_msgs[-1].content.strip()

    if not passaporte.isdigit():
        await message.channel.send(f"{message.author.mention}, o **passaporte** deve ser um número.")
        return

    apelido = f"{nome} #{passaporte}"

    try:
        # Muda o apelido
        await message.author.edit(nick=apelido)

        # Atribui o cargo
        cargo = message.guild.get_role(ID_CARGO_MEMBRO)
        if cargo:
            await message.author.add_roles(cargo)
            await message.channel.send(
                f"{message.author.mention}, você foi promovido a **Membro**!\nApelido definido como `{apelido}` ✅"
            )
        else:
            await message.channel.send(f"{message.author.mention}, cargo de membro **não encontrado**.")
    except botriagem.Forbidden:
        await message.channel.send(f"{message.author.mention}, não tenho permissão para mudar seu apelido ou cargo.")
    except Exception as e:
        await message.channel.send(f"⚠️ Erro ao processar: `{e}`")

    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))