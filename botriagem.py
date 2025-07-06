import discord
from discord.ext import commands
from discord.ui import Button, View
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

ID_CANAL_TRIAGEM = 1361050940383428838
ID_CARGO_MEMBRO = 1360956462180077669

class TriagemView(View):
    def __init__(self):
        super().__init__(timeout=None)  # sem timeout para o botão ficar fixo

    @discord.ui.button(label="Iniciar Triagem", style=discord.ButtonStyle.green)
    async def triagem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"{interaction.user.mention}, por favor, digite seu **nome completo**.", ephemeral=True
        )

        def check_nome(m):
            return m.author == interaction.user and m.channel.id == ID_CANAL_TRIAGEM

        try:
            nome_msg = await bot.wait_for("message", check=check_nome, timeout=60)
        except:
            await interaction.followup.send("Tempo esgotado para enviar o nome.", ephemeral=True)
            return

        await interaction.followup.send(
            f"{interaction.user.mention}, agora digite seu **passaporte (apenas números)**.", ephemeral=True
        )

        def check_passaporte(m):
            return m.author == interaction.user and m.channel.id == ID_CANAL_TRIAGEM

        try:
            passaporte_msg = await bot.wait_for("message", check=check_passaporte, timeout=60)
        except:
            await interaction.followup.send("Tempo esgotado para enviar o passaporte.", ephemeral=True)
            return

        nome = nome_msg.content.strip()
        passaporte = passaporte_msg.content.strip()

        if not passaporte.isdigit():
            await interaction.followup.send("Passaporte inválido. Deve conter apenas números.", ephemeral=True)
            return

        apelido = f"{nome} #{passaporte}"

        member = interaction.guild.get_member(interaction.user.id)
        try:
            await member.edit(nick=apelido)
            cargo = interaction.guild.get_role(ID_CARGO_MEMBRO)
            if cargo:
                await member.add_roles(cargo)
                await interaction.followup.send(f"{interaction.user.mention}, você foi promovido a **Membro**!\nApelido definido como `{apelido}` ✅", ephemeral=True)
            else:
                await interaction.followup.send("Cargo de membro não encontrado.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("Não tenho permissão para alterar apelido ou cargo.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Erro ao processar: {e}", ephemeral=True)


@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

    canal = bot.get_channel(ID_CANAL_TRIAGEM)
    if canal:
        # Envia a mensagem com o botão apenas uma vez (ou quando bot iniciar)
        mensagem_fixa = "Clique no botão abaixo para iniciar a triagem e registrar seu nome e passaporte."
        view = TriagemView()
        await canal.send(mensagem_fixa, view=view)

bot.run(os.getenv("DISCORD_TOKEN"))
