import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
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

class EstoqueModal(Modal):
    def __init__(self, acao):
        super().__init__(title=f"{acao} Munição")
        self.acao = acao
        self.tipo = TextInput(label="Tipo (5mm, 9mm, 762mm, 12cbc)")
        self.qtd = TextInput(label="Quantidade", placeholder="Somente números")
        self.obs = TextInput(label="Observação", required=False)
        self.add_item(self.tipo)
        self.add_item(self.qtd)
        self.add_item(self.obs)

    async def on_submit(self, interaction: discord.Interaction):
        tipo = self.tipo.value.lower().strip()
        if tipo not in ["5mm", "9mm", "762mm", "12cbc"]:
            await interaction.response.send_message("Tipo inválido.", ephemeral=True)
            return

        if not self.qtd.value.isdigit():
            await interaction.response.send_message("Quantidade inválida.", ephemeral=True)
            return

        quantidade = int(self.qtd.value)
        estoque_atual = obter_estoque().get(tipo, 0)

        if self.acao == "Retirar":
            quantidade = -quantidade
            atualizar_estoque(tipo, quantidade)
            sinal = "➖"
        elif self.acao == "Adicionar":
            atualizar_estoque(tipo, quantidade)
            sinal = "➕"
        elif self.acao == "Editar":
            definir_estoque(tipo, quantidade)
            sinal = "✏️"

        await atualizar_mensagem_estoque()

        canal_log = bot.get_channel(ID_CANAL_LOG_MUNICAO)
        if canal_log:
            if self.acao == "Editar":
                await canal_log.send(f"✏️ `{interaction.user.display_name}` alterou **{tipo.upper()}** de {estoque_atual} para {quantidade}\n📝 {self.obs.value or 'Sem observações.'}")
            else:
                await canal_log.send(f"{sinal} `{interaction.user.display_name}` {self.acao.lower()} {abs(quantidade)} de **{tipo.upper()}**\n📝 {self.obs.value or 'Sem observações.'}")

        await interaction.response.send_message("Registro salvo com sucesso!", ephemeral=True)

class EstoqueView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="➕ Adicionar Munição", style=discord.ButtonStyle.green)
    async def adicionar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EstoqueModal("Adicionar"))

    @discord.ui.button(label="➖ Retirar Munição", style=discord.ButtonStyle.red)
    async def retirar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EstoqueModal("Retirar"))

    @discord.ui.button(label="✏️ Editar Munição", style=discord.ButtonStyle.blurple)
    async def editar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EstoqueModal("Editar"))

@bot.command()
async def painelmunicao(ctx):
    await atualizar_mensagem_estoque()
    await ctx.send("Painel de munições iniciado no canal correto.")

@bot.event
async def on_ready():
    iniciar_db()
    await atualizar_mensagem_estoque()
    print(f"Bot conectado como {bot.user}")

# Inicie o bot
TOKEN = os.getenv("DISCORD_TOKEN") or "SEU_TOKEN_AQUI"
bot.run(TOKEN)

bot.run(os.getenv("DISCORD_TOKEN"))
