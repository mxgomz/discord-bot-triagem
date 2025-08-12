import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select
from discord import SelectOption
import os
import datetime
import asyncio
import sqlite3

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# IDs fixos
ID_CANAL_TRIAGEM = 1391472328994717846
ID_CARGO_MEMBRO = 1360956462180077669
ID_CANAL_LOGS = 1391853666507690034
ID_CANAL_TICKET = 1361677898980790314
ID_CANAL_FAMILIA = 1361045908577456138
ID_CANAL_ESTOQUE = 1397730060030443662
ID_CANAL_LOG_MUNICAO = 1397730241190953091

# Banco de dados
def iniciar_db():
    con = sqlite3.connect("estoque.db")
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS estoque (
        tipo TEXT PRIMARY KEY,
        quantidade INTEGER DEFAULT 0
    )""")
    for tipo in ["5mm", "9mm", "762mm", "12cbc"]:
        cur.execute("INSERT OR IGNORE INTO estoque (tipo, quantidade) VALUES (?, 0)", (tipo,))
    con.commit()
    con.close()

def atualizar_estoque(tipo, delta):
    con = sqlite3.connect("estoque.db")
    cur = con.cursor()
    cur.execute("UPDATE estoque SET quantidade = quantidade + ? WHERE tipo = ?", (delta, tipo))
    con.commit()
    con.close()

def definir_estoque(tipo, novo_valor):
    con = sqlite3.connect("estoque.db")
    cur = con.cursor()
    cur.execute("UPDATE estoque SET quantidade = ? WHERE tipo = ?", (novo_valor, tipo))
    con.commit()
    con.close()

def obter_estoque():
    con = sqlite3.connect("estoque.db")
    cur = con.cursor()
    cur.execute("SELECT tipo, quantidade FROM estoque")
    dados = {tipo: qtd for tipo, qtd in cur.fetchall()}
    con.close()
    return dados

mensagem_estoque_id = None

async def atualizar_mensagem_estoque():
    global mensagem_estoque_id
    canal = bot.get_channel(ID_CANAL_ESTOQUE)
    estoque = obter_estoque()
    conteudo = "📦 **ESTOQUE ATUAL - Facção Turquesa**\n\n"
    for tipo, qtd in estoque.items():
        conteudo += f"🔫 {tipo.upper()}: {qtd}\n"
    view = EstoqueView()
    try:
        if mensagem_estoque_id:
            msg = await canal.fetch_message(mensagem_estoque_id)
            await msg.edit(content=conteudo, view=view)
        else:
            msg = await canal.send(content=conteudo, view=view)
            mensagem_estoque_id = msg.id
    except Exception as e:
        print(f"Erro ao atualizar mensagem de estoque: {e}")

# ----------- Modal Estoque -----------
class EstoqueModal(Modal):
    def __init__(self, acao, tipo):
        super().__init__(title=f"{acao} Munição - {tipo.upper()}")
        self.acao = acao
        self.tipo = tipo
        self.qtd = TextInput(label="Quantidade", placeholder="Somente números")
        self.obs = TextInput(label="Observação", required=False)
        self.add_item(self.qtd)
        self.add_item(self.obs)

    async def on_submit(self, interaction: discord.Interaction):
        if not self.qtd.value.isdigit():
            await interaction.response.send_message("Quantidade inválida.", ephemeral=True)
            return

        quantidade = int(self.qtd.value)
        estoque_atual = obter_estoque().get(self.tipo, 0)

        if self.acao == "Retirar":
            quantidade = -quantidade
            atualizar_estoque(self.tipo, quantidade)
            sinal = "➖"
        elif self.acao == "Adicionar":
            atualizar_estoque(self.tipo, quantidade)
            sinal = "➕"
        elif self.acao == "Editar":
            definir_estoque(self.tipo, quantidade)
            sinal = "✏️"

        await atualizar_mensagem_estoque()

        canal_log = bot.get_channel(ID_CANAL_LOG_MUNICAO)
        if canal_log:
            if self.acao == "Editar":
                await canal_log.send(f"✏️ {interaction.user.display_name} alterou **{self.tipo.upper()}** de {estoque_atual} para {quantidade}\n📝 {self.obs.value or 'Sem observações.'}")
            else:
                await canal_log.send(f"{sinal} {interaction.user.display_name} {self.acao.lower()} {abs(quantidade)} de **{self.tipo.upper()}**\n📝 {self.obs.value or 'Sem observações.'}")

        await interaction.response.send_message("Registro salvo com sucesso!", ephemeral=True)

# ----------- Estoque Views -----------

class TipoSelect(Select):
    def __init__(self, acao):
        options = [
            SelectOption(label="5mm", value="5mm"),
            SelectOption(label="9mm", value="9mm"),
            SelectOption(label="762mm", value="762mm"),
            SelectOption(label="12cbc", value="12cbc"),
        ]
        super().__init__(placeholder="Selecione o tipo de munição", options=options)
        self.acao = acao

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EstoqueModal(self.acao, self.values[0]))

class TipoSelectView(View):
    def __init__(self, acao):
        super().__init__(timeout=60)
        self.add_item(TipoSelect(acao))

class EstoqueView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="➕ Adicionar Munição", style=discord.ButtonStyle.green)
    async def adicionar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecione o tipo de munição para adicionar:", view=TipoSelectView("Adicionar"), ephemeral=True)

    @discord.ui.button(label="➖ Retirar Munição", style=discord.ButtonStyle.red)
    async def retirar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecione o tipo de munição para retirar:", view=TipoSelectView("Retirar"), ephemeral=True)

    @discord.ui.button(label="✏️ Editar Munição", style=discord.ButtonStyle.blurple)
    async def editar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecione o tipo de munição para editar:", view=TipoSelectView("Editar"), ephemeral=True)

# ----------- Triagem -----------

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

# ----------- Eventos -----------

@bot.event
async def on_ready():
    iniciar_db()
    await atualizar_mensagem_estoque()
    print(f"✅ Bot online como {bot.user}")

    canal = bot.get_channel(ID_CANAL_TRIAGEM)
    if canal:
        mensagem_fixa = "Clique no botão abaixo para iniciar a triagem e registrar seu nome e passaporte."
        view = TriagemView()
        await canal.send(mensagem_fixa, view=view)

@bot.event
async def on_guild_channel_create(channel):
    if isinstance(channel, discord.TextChannel) and channel.name.startswith("ticket-"):
        await asyncio.sleep(2)
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

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # NOVA FUNÇÃO: resposta por palavra-chave no canal específico
    if message.channel.id == 1366016740605165670:
        conteudo = message.content.lower()

        if conteudo.startswith("toze preços"):
            await message.channel.send("Use: Toze [Munição / Drogas / Attachs / Armas / Flippers]")

        elif conteudo.startswith("toze munição"):
            await message.channel.send(embed=discord.Embed().set_image(url="https://i.imgur.com/TaoEOn7.png"))

        elif conteudo.startswith("toze drogas"):
            await message.channel.send(embed=discord.Embed().set_image(url="https://i.imgur.com/dciMFnD.png"))

        elif conteudo.startswith("toze attachs"):
            await message.channel.send(embed=discord.Embed().set_image(url="https://i.imgur.com/S1aS1o9.png"))

        elif conteudo.startswith("toze armas"):
            await message.channel.send(embed=discord.Embed().set_image(url="https://i.imgur.com/NvrzKdQ.png"))
            await message.channel.send(embed=discord.Embed().set_image(url="https://i.imgur.com/cr5Xere.png"))
            await message.channel.send(embed=discord.Embed().set_image(url="https://i.imgur.com/ylAyVfq.png"))

        elif conteudo.startswith("toze flippers"):
            await message.channel.send(embed=discord.Embed().set_image(url="https://i.imgur.com/h6MJfHF.png"))

    # Mantém sua função original para canal família
    if message.channel.id == ID_CANAL_FAMILIA:
        conteudo = message.content.lower()
        palavras_chave = ["ajuda", "busca", "loc", "salva", "morto", "to na", "to em", "help", "ajudar", "onde"]
        if any(palavra in conteudo for palavra in palavras_chave):
            await message.channel.send("⚠️ **Aviso:** O uso de metagaming no chat da família é proibido. Persistindo, poderão ocorrer punições.")

    await bot.process_commands(message)

# ----------- Comando Painel Estoque -----------

@bot.command()
async def painelmunicao(ctx):
    await atualizar_mensagem_estoque()
    await ctx.send("Painel de munições iniciado no canal correto.")

bot.run(os.getenv("DISCORD_TOKEN"))
