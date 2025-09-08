import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select
from discord import SelectOption
import os
import json
import datetime
import sqlite3
import gspread
from google.oauth2.service_account import Credentials


# ----------------- GOOGLE SHEETS -----------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
if 'GOOGLE_SA_JSON' not in os.environ or not os.environ['GOOGLE_SA_JSON']:
    raise ValueError("A variável de ambiente GOOGLE_SA_JSON não está configurada!")
sa_info = json.loads(os.environ['GOOGLE_SA_JSON'])
creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
gclient = gspread.authorize(creds)
SHEET_ID = "1ZZrnyhpDdjgTP6dYu9MgpKGvq1JHHzyuQ9EyD1P8TfI"
sheet = gclient.open_by_key(SHEET_ID).sheet1

# ----------------- FUNÇÕES PARA PLANILHA -----------------
def registrar_financeiro(gerente, tipo, descricao, valor):
    valor = float(valor)
    data = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    linhas = sheet.get_all_values()
    
    # Obter saldo atual
    saldo_atual = float(linhas[1][4]) if len(linhas) > 1 and linhas[1][4] else 0.0
    if tipo.lower() == "entrada":
        saldo_total = saldo_atual + valor
    else:
        saldo_total = saldo_atual - valor
    
    # Nova linha: sempre na primeira linha (logo abaixo do header)
    nova_linha = [data, gerente, tipo, descricao, str(valor), str(saldo_total)]
    if len(linhas) <= 1:
        sheet.append_row(nova_linha)
    else:
        sheet.insert_row(nova_linha, index=2)

# ----------------- CONFIGURAÇÕES BOT -----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- IDS -----------------
ID_CANAL_FINANCEIRO = 1409591228265398393
ID_CANAL_LOG_FINANCEIRO = 1414685341797056623

# ----------------- MODAL -----------------
class FinanceModal(Modal):
    def __init__(self):
        super().__init__(title="Registrar Valor no Cofre")
        # Tipo: Entrada/Saída
        self.tipo = Select(
            placeholder="Selecione o tipo",
            options=[
                SelectOption(label="Entrada", value="Entrada"),
                SelectOption(label="Saída", value="Saída")
            ]
        )
        self.tipo.required = True
        self.add_item(self.tipo)
        
        # Descrição
        self.descricao = TextInput(label="Descrição", placeholder="Ex: Venda de item", required=True)
        self.add_item(self.descricao)
        
        # Valor
        self.valor = TextInput(label="Valor (R$)", placeholder="Ex: 1000", required=True)
        self.add_item(self.valor)

    async def on_submit(self, interaction: discord.Interaction):
        gerente = interaction.user.display_name
        tipo = self.tipo.values[0]
        descricao = self.descricao.value
        valor = self.valor.value
        
        try:
            # Registrar na planilha
            registrar_financeiro(gerente, tipo, descricao, valor)
            
            # Log
            canal_log = bot.get_channel(ID_CANAL_LOG_FINANCEIRO)
            if canal_log:
                await canal_log.send(f"💰 {gerente} fez um novo registro no cofre.")
            
            await interaction.response.send_message("✅ Registro realizado com sucesso!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao registrar: {e}", ephemeral=True)

# ----------------- VIEW -----------------
class FinanceView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Registrar no Cofre", style=discord.ButtonStyle.green, custom_id="btn_finance"))

    @discord.ui.button(label="Registrar no Cofre", style=discord.ButtonStyle.green, custom_id="btn_finance")
    async def registrar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = FinanceModal()
        await interaction.response.send_modal(modal)

# ----------------- ENVIAR MENSAGEM COM BOTÃO -----------------
@bot.command()
async def painelcofre(ctx):
    canal = bot.get_channel(ID_CANAL_FINANCEIRO)
    if not canal:
        await ctx.send("Canal financeiro não encontrado.", delete_after=5)
        return
    view = FinanceView()
    await canal.send("💰 Clique no botão abaixo para registrar uma entrada ou saída no cofre.", view=view)
    await ctx.send("✅ Painel financeiro iniciado.", delete_after=5)


SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

if 'GOOGLE_SA_JSON' not in os.environ or not os.environ['GOOGLE_SA_JSON']:
    raise ValueError("A variável de ambiente GOOGLE_SA_JSON não está configurada!")

sa_info = json.loads(os.environ['GOOGLE_SA_JSON'])
creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)

gclient = gspread.authorize(creds)
SHEET_ID = "1ZZrnyhpDdjgTP6dYu9MgpKGvq1JHHzyuQ9EyD1P8TfI"
sheet = gclient.open_by_key(SHEET_ID).sheet1

def obter_estoque():
    con = sqlite3.connect("estoque.db")
    cur = con.cursor()
    cur.execute("SELECT tipo, quantidade FROM estoque")
    dados = {tipo: qtd for tipo, qtd in cur.fetchall()}
    con.close()
    return dados

def registrar_planilha(gerente, acao, item, quantidade, comentario=""):
    data = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    linhas = sheet.get_all_values()
    estoque = obter_estoque()
    total_5mm = estoque.get("5mm", 0)
    total_9mm = estoque.get("9mm", 0)
    total_762mm = estoque.get("762mm", 0)
    total_12cbc = estoque.get("12cbc", 0)
    nova_linha = [
        data,
        gerente,
        acao,
        item,
        quantidade,
        comentario,
        "",
        total_5mm,
        total_9mm,
        total_762mm,
        total_12cbc
    ]
    if len(linhas) <= 1:
        sheet.append_row(nova_linha)
    else:
        sheet.insert_row(nova_linha, index=2)
        sheet.update(f"H3:K{len(linhas)+1}", [[""]*4]*(len(linhas)-1))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

ID_CANAL_TRIAGEM = 1391472328994717846
ID_CARGO_MEMBRO = 1360956462180077669
ID_CANAL_LOGS = 1391853666507690034
ID_CANAL_TICKET = 1361677898980790314
ID_CANAL_FAMILIA = 1361045908577456138
ID_CANAL_ESTOQUE = 1397730060030443662
ID_CANAL_LOG_MUNICAO = 1397730241190953091
ID_CANAL_HIERARQUIA = 1408883105225511092
ID_CARGO_HIERARQUIA = 1361719183787954236

MENSAGEM_PAINEL_ID = None
mensagem_estoque_id = None

CARGOS_CONFIG = [
    {"nome": "👑 Líder", "limite": 1, "role": "Líder"},
    {"nome": "👥 Vice-Líder", "limite": 0, "role": "Vice-Líder"},
    {"nome": "⚙️ Gerente de Produção", "limite": 0, "role": "Gerente de Produção"},
    {"nome": "🌾 Gerente de Farm", "limite": 0, "role": "Gerente de Farm"},
    {"nome": "📜 Gerente de Recrutamento", "limite": 0, "role": "Gerente de Recrutamento"},
    {"nome": "💰 Gerente de Vendas", "limite": 0, "role": "Gerente de Vendas"},
    {"nome": "🎯 Gerente de Ação", "limite": 0, "role": "Gerente de Ação"},
    {"nome": "💻 Gerente Discord", "limite": 0, "role": "Gerente Discord"},
    {"nome": "🧑‍💼 Gerente", "limite": 0, "role": "Gerente"},
    {"nome": "🚩 Membros", "limite": 0, "role": "Membros"}
]

def gerar_barra(ocupados: int, limite: int, tamanho: int = 20) -> str:
    if limite == 0:
        return "─" * tamanho
    proporcao = ocupados / limite
    preenchidos = round(tamanho * proporcao)
    vazios = tamanho - preenchidos
    return "▰" * preenchidos + "▱" * vazios

async def atualizar_mensagem_painel():
    global MENSAGEM_PAINEL_ID
    canal = bot.get_channel(ID_CARGO_HIERARQUIA)
    if not canal:
        return
    guild = canal.guild
    embed = discord.Embed(title="📌 Painel de Hierarquia", color=discord.Color.blue())
    membros_ocupados = set()
    for config in CARGOS_CONFIG:
        role = discord.utils.get(guild.roles, name=config["role"])
        membros = []
        if config["role"] == "Membros":
            membros = [m.mention for m in guild.members if not m.bot and m not in membros_ocupados]
        elif role:
            membros = [m.mention for m in guild.members if role in m.roles and not m.bot]
            for m in guild.members:
                if role in m.roles:
                    membros_ocupados.add(m)
        ocupados = len(membros)
        limite = config["limite"]
        lista_membros = "\n".join(f"➔ {m}" for m in membros) if membros else "🔴 Nenhum"
        barra = gerar_barra(ocupados, limite)
        embed.add_field(
            name=f"{config['nome']} - ({ocupados}/{limite})" if limite > 0 else f"{config['nome']} - ({ocupados})",
            value=f"{lista_membros}\n\n{barra}",
            inline=False
        )
    if MENSAGEM_PAINEL_ID:
        try:
            msg = await canal.fetch_message(MENSAGEM_PAINEL_ID)
            await msg.edit(embed=embed)
            return
        except:
            MENSAGEM_PAINEL_ID = None
    async for m in canal.history(limit=10):
        if m.author == bot.user and m.embeds and m.embeds[0].title == "📌 Painel de Hierarquia":
            await m.edit(embed=embed)
            MENSAGEM_PAINEL_ID = m.id
            return
    msg = await canal.send(embed=embed)
    MENSAGEM_PAINEL_ID = msg.id

@bot.command()
async def atualizarlista(ctx):
    author = ctx.author
    cargo_autorizado = ctx.guild.get_role(ID_CARGO_HIERARQUIA)
    if cargo_autorizado not in author.roles:
        await ctx.send("❌ Você não tem permissão para usar este comando.", delete_after=5)
        return
    await atualizar_mensagem_painel()
    await ctx.send("✅ Painel de hierarquia atualizado!", delete_after=5)

class TriagemModal(Modal):
    def __init__(self):
        super().__init__(title="Triagem")
        self.apelido_input = TextInput(label="Apelido", placeholder="Digite seu apelido")
        self.passaporte_input = TextInput(label="Passaporte", placeholder="Digite seu passaporte")
        self.add_item(self.apelido_input)
        self.add_item(self.passaporte_input)

    async def on_submit(self, interaction: discord.Interaction):
        apelido = self.apelido_input.value
        member = interaction.user
        guild = interaction.guild
        cargo_membro = guild.get_role(ID_CARGO_MEMBRO)
        if cargo_membro in member.roles:
            await interaction.response.send_message("Você já é cadastrado como membro.", ephemeral=True)
            return
        try:
            await member.edit(nick=apelido)
            await member.add_roles(cargo_membro)
            url = f"https://discord.com/channels/{guild.id}/{ID_CANAL_TICKET}"
            view = View()
            view.add_item(Button(label="🎫 Abrir Ticket", style=discord.ButtonStyle.blurple, url=url))
            await interaction.response.send_message(
                f"Cadastro realizado com sucesso!\nApelido definido como `{apelido}` ✅\n\nClique abaixo para abrir um **ticket** e continuar o processo.",
                ephemeral=True,
                view=view
            )
            canal_logs = guild.get_channel(ID_CANAL_LOGS)
            if canal_logs:
                await canal_logs.send(f"✅ `{apelido}` acabou de passar pela triagem.")
        except discord.Forbidden:
            await interaction.response.send_message("Não tenho permissão para alterar apelido ou cargo.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Erro ao processar a triagem: {e}", ephemeral=True)

class TriagemView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Iniciar Triagem", style=discord.ButtonStyle.green)
    async def triagem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TriagemModal()
        await interaction.response.send_modal(modal)

@bot.command()
@commands.has_role(ID_CARGO_HIERARQUIA)
async def enviartriagem(ctx):
    canal = bot.get_channel(ID_CANAL_TRIAGEM)
    if not canal:
        await ctx.send("Canal de triagem não encontrado.", delete_after=5)
        return
    mensagem_fixa = "Clique no botão abaixo para iniciar a triagem e registrar seu nome e passaporte."
    view = TriagemView()
    await canal.send(mensagem_fixa, view=view)
    await ctx.send("✅ Mensagem de triagem enviada.", delete_after=5)

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
        registrar_planilha(
            interaction.user.display_name,
            self.acao,
            self.tipo.upper(),
            abs(quantidade),
            self.obs.value or "Sem observações."
        )
        await atualizar_mensagem_estoque()
        canal_log = bot.get_channel(ID_CANAL_LOG_MUNICAO)
        if canal_log:
            if self.acao == "Editar":
                await canal_log.send(f"✏️ {interaction.user.display_name} alterou **{self.tipo.upper()}** de {estoque_atual} para {quantidade}\n📝 {self.obs.value or 'Sem observações.'}")
            else:
                await canal_log.send(f"{sinal} {interaction.user.display_name} {self.acao.lower()} {abs(quantidade)} de **{self.tipo.upper()}**\n📝 {self.obs.value or 'Sem observações.'}")

        await interaction.response.send_message("Registro salvo com sucesso!", ephemeral=True)

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
        super().__init__(timeout=None)
        self.add_item(TipoSelect(acao))

class EstoqueView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="➕ Adicionar Munição", style=discord.ButtonStyle.green)
    async def adicionar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Selecione o tipo de munição para adicionar:", view=TipoSelectView("Adicionar"), ephemeral=True)
    @discord.ui.button(label="➖ Retirar Munição", style=discord.ButtonStyle.red)
    async def retirar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Selecione o tipo de munição para retirar:", view=TipoSelectView("Retirar"), ephemeral=True)
    @discord.ui.button(label="✏️ Editar Munição", style=discord.ButtonStyle.blurple)
    async def editar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Selecione o tipo de munição para editar:", view=TipoSelectView("Editar"), ephemeral=True)

async def atualizar_mensagem_estoque():
    global mensagem_estoque_id
    canal = bot.get_channel(ID_CANAL_ESTOQUE)
    if not canal:
        return
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

@bot.event
async def on_ready():
    iniciar_db()
    await atualizar_mensagem_estoque()
    await atualizar_mensagem_painel()
    print(f"✅ Bot online como {bot.user}")
    canal = bot.get_channel(ID_CANAL_TRIAGEM)
    if canal:
        mensagem_fixa = "Clique no botão abaixo para iniciar a triagem e registrar seu nome e passaporte."
        view = TriagemView()
        await canal.send(mensagem_fixa, view=view)

@bot.command()
async def painelmunicao(ctx):
    await atualizar_mensagem_estoque()
    await ctx.send("Painel de munições iniciado no canal correto.")

if not os.getenv("DISCORD_TOKEN"):
    raise ValueError("A variável de ambiente DISCORD_TOKEN não está configurada!")

bot.run(os.getenv("DISCORD_TOKEN"))
