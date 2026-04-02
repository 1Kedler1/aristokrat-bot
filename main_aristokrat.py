import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import time
import os
from flask import Flask
from threading import Thread

# ==========================================
#               7/24 SİSTEMİ
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🔱 Aristokrat Online ve Her Şey Hazır!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ==========================================
#               AYARLAR
# ==========================================
TOKEN = os.environ.get("DISCORD_TOKEN")
KAYITSIZ_ROL_ID = 1488679958216839278
KAYITLI_ROL_ID = 1488679806152478872
HOSGELDIN_KANAL_ID = 1488671987432689887
KAYIT_KANAL_ID = 1488907101307797685
KURALLAR_KANAL_ID = 1488699145043837038
DESTEK_KATEGORI_ID = 1488932448552353934

# ==========================================
#               VIEWS (BUTONLAR)
# ==========================================
class KapatButonu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Talebi Kapat", style=discord.ButtonStyle.red, emoji="🔒", custom_id="t_kapat")
    async def kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Kanal 3 saniye içinde siliniyor...")
        await asyncio.sleep(3)
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
        await ticket.send(f"🔱 Merhaba {user.mention}, yetkililer seninle ilgilenecek.", view=KapatButonu())

# ==========================================
#               ANA BOT SINIFI
# ==========================================
class AristokratBot(commands.Bot):
    def __init__(self):
        # BURASI KRİTİK: Tüm yetkileri açıyoruz
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)
        self.start_time = time.time()

    async def setup_hook(self):
        self.add_view(DestekButonu())
        self.add_view(KapatButonu())

bot = AristokratBot()

# --- HOŞ GELDİN VE OTOMATİK ROL OLAYI ---
@bot.event
async def on_member_join(member):
    # 1. Kayıtsız Rolünü Ver
    try:
        rol = member.guild.get_role(KAYITSIZ_ROL_ID)
        if rol:
            await member.add_roles(rol)
            print(f"✅ {member.name} için Kayıtsız rolü verildi.")
    except Exception as e:
        print(f"❌ Rol verilirken hata oluştu: {e}")

    # 2. Hoş Geldin Mesajını At
    channel = bot.get_channel(HOSGELDIN_KANAL_ID)
    if channel:
        olusturma_ts = int(member.created_at.timestamp())
        uye_sayisi = member.guild.member_count
        
        mesaj = (
            f"Merhabalar {member.mention}, aramıza hoşgeldin. Seninle beraber sunucumuz **{uye_sayisi}** üye sayısına ulaştı. 🎉\n\n"
            f"Hesabın <t:{olusturma_ts}:f> tarihinde <t:{olusturma_ts}:R> oluşturulmuş!\n\n"
            f"Sunucuya erişebilmek için <#{KAYIT_KANAL_ID}> odalarında kayıt olup ismini ve yaşını belirtmen gerekmektedir!\n\n"
            f"<#{KURALLAR_KANAL_ID}> kanalından sunucu kurallarımızı okumayı ihmal etme!"
        )
        await channel.send(mesaj)

@bot.event
async def on_ready():
    print(f'🔱 {bot.user.name} SİSTEME GİRİŞ YAPTI!')
    await bot.tree.sync()
    print("✅ Slash komutları ve Hoş Geldin sistemi aktif.")

# ==========================================
#               KOMUTLAR
# ==========================================
@bot.tree.command(name="kayıt", description="Üyeyi kayıt eder.")
async def kayit(interaction: discord.Interaction, kullanici: discord.Member, isim: str, yas: int):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
    
    kayitsiz = interaction.guild.get_role(KAYITSIZ_ROL_ID)
    kayitli = interaction.guild.get_role(KAYITLI_ROL_ID)
    
    try:
        if kayitsiz in kullanici.roles:
            await kullanici.remove_roles(kayitsiz)
        await kullanici.add_roles(kayitli)
        await kullanici.edit(nick=f"{isim} | {yas}")
        await interaction.response.send_message(f"✅ {kullanici.mention} başarıyla kayıt edildi!")
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="destek-kur", description="Destek butonunu atar.")
async def dkur(interaction: discord.Interaction):
    embed = discord.Embed(title="🔱 Destek Sistemi", description="Talep açmak için butona tıkla.", color=0x2ECC71)
    await interaction.channel.send(embed=embed, view=DestekButonu())
    await interaction.response.send_message("✅ Kuruldu.", ephemeral=True)

if __name__ == "__main__":
    Thread(target=run_server).start()
    if TOKEN:
        bot.run(TOKEN)