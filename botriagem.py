import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import os
import datetime
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

ID_CANAL_TRIAGEM = 1391472328994717846
ID_CARGO_MEMBRO = 1360956462180077669
ID_CANAL_LOGS = 1391853666507690034
ID_CANAL_TICKET = 1361677898980790314
ID_CANAL_FAMILIA = 1361045908577456138  # Canal onde o aviso será enviado

class TriagemModal(Modal):
    def __init__(self):
        super().__init__(title="Formulário de Triagem")
        self.nome = TextInput(label="Nome", placeholder="Digite seu nome", max_length=100)
        self.passaporte = TextInput(label="Passaporte (somente números)", placeholder="Ex: 123456", max_length=20)

        self.add_item(self.nome)
        self.add_item(self.passaporte)

    async def on_submit(self, interaction: discord.Interaction):
        nome = self.nome.value.strip()
        passaporte = self.passaporte.value.strip()

        if not passaporte.isdigit():
            await interaction.response.send_message("Passaporte inválido, deve conter somente números.", ephemeral=True)
            return

        apelido = f"{nome} #{passaporte}"
        member = interaction.guild.get_member(interaction.user.id)

        if member and any(role.id == ID_CARGO_MEMBRO or role.position > interaction.guild.get_role(ID_CARGO_MEMBRO).position for role in member.roles):
            await interaction.response.send_message("Você já está cadastrado como membro ou possui cargo superior.", ephemeral=True)
            return

        try:
            await member.edit(nick=apelido)
            cargo = interaction.guild.get_role(ID_CARGO_MEMBRO)
            if cargo:
                await member.add_roles(cargo)

                url = f"https://discord.com/channels/{interaction.guild.id}/{ID_CANAL_TICKET}"
                view = View()
                view.add_item(Button(label="🎫 Abrir Ticket", style=discord.ButtonStyle.blurple, url=url))

                await interaction.response.send_message(
                    f"Cadastro realizado com sucesso!\nApelido definido como `{apelido}` ✅\n\nClique abaixo para abrir um **ticket** e continuar o processo.",
                    ephemeral=True,
                    view=view
                )

                canal_logs = interaction.guild.get_channel(ID_CANAL_LOGS)
                if canal_logs:
                    await canal_logs.send(f"✅ `{apelido}` acabou de passar pela triagem.")
            else:
                await interaction.response.send_message("Cargo de membro não encontrado.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Não tenho permissão para alterar apelido ou cargo.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Erro ao processar: {e}", ephemeral=True)

class TriagemView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Iniciar Triagem", style=discord.ButtonStyle.green)
    async def triagem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.guild.get_member(interaction.user.id)
        cargo_membro = interaction.guild.get_role(ID_CARGO_MEMBRO)
        if member and cargo_membro in member.roles:
            await interaction.response.send_message("Você já é cadastrado como membro.", ephemeral=True)
            return

        modal = TriagemModal()
        await interaction.response.send_modal(modal)

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

    canal = bot.get_channel(ID_CANAL_TRIAGEM)
    if canal:
        mensagem_fixa = "Clique no botão abaixo para iniciar a triagem e registrar seu nome e passaporte."
        view = TriagemView()
        await canal.send(mensagem_fixa, view=view)

@bot.event
async def on_guild_channel_create(channel):
    if isinstance(channel, discord.TextChannel) and channel.name.startswith("ticket-"):
        await asyncio.sleep(2)  # Espera o Ticket Tool configurar o canal

        try:
            messages = [msg async for msg in channel.history(limit=5)]
            for msg in messages:
                apelido = msg.author.nick or msg.author.name
                if apelido:
                    agora = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")
                    await channel.send(f"📬 Ticket de **{apelido}** aberto em {agora}.")
                    break
        except Exception as e:
            print(f"Erro ao enviar mensagem de abertura de ticket: {e}")

# ✅ NOVO EVENTO: Detecção de "ajuda" ou "busca" no canal da família
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == ID_CANAL_FAMILIA:
        conteudo = message.content.lower()

        if "ajuda" in conteudo or "busca" in conteudo:
            await message.channel.send(
                "⚠️ **Aviso:** O uso de metagaming no chat da família é proibido. Persistindo, poderão ocorrer punições."
            )

    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))
