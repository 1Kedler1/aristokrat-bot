import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import time
import os
from flask import Flask
from threading import Thread

# ==========================================
#               7/24 AKTİF TUTMA
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🔱 Aristokrat Sade Sürüm Aktif!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ==========================================
#               AYARLAR (ID'LER)
# ==========================================
TOKEN = os.environ.get("DISCORD_TOKEN")
KAYITSIZ_ROL_ID = 1488679958216839278
KAYITLI_ROL_ID = 1488679806152478872
HOSGELDIN_KANAL_ID = 1488671987432689887
KAYIT_KANAL_ID = 1488907101307797685
KURALLAR_KANAL_ID = 1488699145043837038
DESTEK_KATEGORI_ID = 1488932448552353934

# ==========================================
#               DESTEK SİSTEMİ BUTONLARI
# ==========================================

class KapatButonu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Talebi Kapat", style=discord.ButtonStyle.red, emoji="🔒", custom_id="t_kapat")
    async def kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Kanal 5 saniye içinde siliniyor...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class DestekButonu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Destek Talebi Oluştur", style=discord.ButtonStyle.green, emoji="🛡️", custom_id="t_ac")
    async def ac(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        kanal_adi = f"ticket-{user.name.lower()}"
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        ticket = await guild.create_text_channel(name=kanal_adi, category=guild.get_channel(DESTEK_KATEGORI_ID), overwrites=overwrites)
        await interaction.response.send_message(f"✅ Destek kanalı açıldı: {ticket.mention}", ephemeral=True)
        await ticket.send(f"🔱 Merhaba {user.mention}, yetkililer kısa süre içinde burada olacaktır.", view=KapatButonu())

# ==========================================
#               ANA BOT SINIFI
# ==========================================
class AristokratBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        self.add_view(DestekButonu())
        self.add_view(KapatButonu())

bot = AristokratBot()

# --- HOŞ GELDİN MESAJI VE OTOMATİK ROL ---
@bot.event
async def on_member_join(member):
    # 1. Kayıtsız Rolü Ver
    rol = member.guild.get_role(KAYITSIZ_ROL_ID)
    if rol:
        try:
            await member.add_roles(rol)
        except:
            print("❌ Rol verme yetkim yok, bot rolünü en üste taşı!")

    # 2. Hoş Geldin Mesajı
    channel = bot.get_channel(HOSGELDIN_KANAL_ID)
    if channel:
        ts = int(member.created_at.timestamp())
        mesaj = (
            f"Merhabalar {member.mention}, aramıza hoşgeldin. Seninle beraber sunucumuz **{member.guild.member_count}** üye sayısına ulaştı. 🎉\n\n"
            f"Hesabın <t:{ts}:f> tarihinde <t:{ts}:R> oluşturulmuş!\n\n"
            f"Sunucuya erişebilmek için <#{KAYIT_KANAL_ID}> odalarında kayıt olup ismini ve yaşını belirtmen gerekmektedir!\n\n"
            f"<#{KURALLAR_KANAL_ID}> kanalından sunucu kurallarımızı okumayı ihmal etme!"
        )
        await channel.send(mesaj)

@bot.event
async def on_ready():
    print(f'🔱 {bot.user.name} SADE SÜRÜM AKTİF!')
    await bot.tree.sync()

# ==========================================
#               KOMUTLAR
# ==========================================

@bot.tree.command(name="kayıt", description="Üyeyi kayıt eder.")
async def kayit(interaction: discord.Interaction, kullanici: discord.Member, isim: str, yas: int):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
    
    try:
        kayitsiz = interaction.guild.get_role(KAYITSIZ_ROL_ID)
        kayitli = interaction.guild.get_role(KAYITLI_ROL_ID)
        
        if kayitsiz in kullanici.roles:
            await kullanici.remove_roles(kayitsiz)
        await kullanici.add_roles(kayitli)
        await kullanici.edit(nick=f"{isim} | {yas}")
        await interaction.response.send_message(f"✅ {kullanici.mention} başarıyla kayıt edildi!", ephemeral=False)
    except Exception as e:
        await interaction.response.send_message(f"❌ Kayıt hatası: {e}", ephemeral=True)

@bot.tree.command(name="destek-kur", description="Destek sistemini kurar.")
async def dkur(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
    
    embed = discord.Embed(title="🔱 Destek Sistemi", description="Aşağıdaki butona basarak destek talebi oluşturabilirsin.", color=0x3498DB)
    await interaction.channel.send(embed=embed, view=DestekButonu())
    await interaction.response.send_message("✅ Destek butonu oluşturuldu.", ephemeral=True)

if __name__ == "__main__":
    Thread(target=run_server).start()
    if TOKEN:
        bot.run(TOKEN)