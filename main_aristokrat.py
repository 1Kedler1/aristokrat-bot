import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import random
import time
import os
from flask import Flask
from threading import Thread

# ==========================================
#               7/24 AKTİF TUTMA SİSTEMİ
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "🔱 Aristokrat Bot 7/24 Aktif ve Tek Dosya Üzerinden Çalışıyor!"

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
DESTEK_KATEGORI_ID = 1488932448552353934  
YETKILI_ROL_ID = 1488679118857044119      
BILGI_YETKILI_ROLLER = [1488677638049366076, 1488677820547731556, 1488678029684117746, 1488678146160197842]

# ==========================================
#         YARDIMCI GÖRÜNÜMLER (VIEWS)
# ==========================================

# 1. Çekiliş Katıl Butonu
class CekilisKatilView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.katilanlar = []

    @discord.ui.button(label="Katıl!", style=discord.ButtonStyle.blurple, emoji="🎉", custom_id="cekilis_katil")
    async def katil(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.katilanlar:
            return await interaction.response.send_message("⚠️ Zaten çekilişe katıldın!", ephemeral=True)
        self.katilanlar.append(interaction.user.id)
        await interaction.response.send_message(f"✅ Çekilişe başarıyla katıldın! Katılımcı: {len(self.katilanlar)}", ephemeral=True)

# 2. Destek Kapatma Butonu
class KapatButonu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Talebi Kapat", style=discord.ButtonStyle.red, emoji="🔒", custom_id="destek_kapat")
    async def destek_kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Kanal 5 saniye içinde siliniyor...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# 3. Destek Açma Butonu
class DestekButonu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Destek Talebi Oluştur", style=discord.ButtonStyle.green, emoji="🛡️", custom_id="destek_ac")
    async def destek_ac(self, interaction: discord.Interaction, button: discord.ui.Button):
        try: await interaction.response.defer(ephemeral=True)
        except: pass
        
        guild = interaction.guild
        user = interaction.user
        kanal_adi = f"ticket-{user.name.lower()}"
        
        if discord.utils.get(guild.channels, name=kanal_adi):
            return await interaction.followup.send(f"⚠️ Zaten aktif bir talebin var: {kanal_adi}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        cat = guild.get_channel(DESTEK_KATEGORI_ID)
        ticket = await guild.create_text_channel(name=kanal_adi, category=cat, overwrites=overwrites)
        await interaction.followup.send(f"✅ Destek kanalı açıldı: {ticket.mention}", ephemeral=True)
        await ticket.send(f"🔱 Merhaba {user.mention}, yetkililer yakında seninle ilgilenecek.", view=KapatButonu())

# ==========================================
#               ANA BOT SINIFI
# ==========================================
class AristokratBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.start_time = time.time()

    async def setup_hook(self):
        self.add_view(DestekButonu())
        self.add_view(KapatButonu())
        self.add_view(CekilisKatilView())

bot = AristokratBot()

# ==========================================
#               SLASH KOMUTLARI
# ==========================================

# --- Çekiliş Komutu ---
@bot.tree.command(name="çekiliş", description="Çekiliş başlatır.")
@app_commands.describe(odul="Ödül nedir?", sure="Kaç dakika sürsün?")
async def cekilis(interaction: discord.Interaction, odul: str, sure: int):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
    
    sure_sn = sure * 60
    bitis = int(time.time() + sure_sn)
    view = CekilisKatilView()
    
    embed = discord.Embed(title="🎊 ÇEKİLİŞ BAŞLADI!", description=f"**Ödül:** `{odul}`\n**Bitiş:** <t:{bitis}:R>", color=0xFFD700)
    msg = await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ Çekiliş başlatıldı.", ephemeral=True)
    
    await asyncio.sleep(sure_sn)
    
    if not view.katilanlar:
        return await interaction.channel.send(f"❌ `{odul}` çekilişi katılımcı olmadığı için iptal edildi.")
    
    kazanan = interaction.guild.get_member(random.choice(view.katilanlar))
    await msg.edit(view=None)
    await interaction.channel.send(f"🎊 Tebrikler {kazanan.mention}! **{odul}** kazandın!")

# --- Kelime Yarışı ---
@bot.tree.command(name="kelime-yarışı", description="Hızlı yazma etkinliği.")
async def kelime(interaction: discord.Interaction):
    liste = ["Aristokrat", "İmparatorluk", "Discord", "Yazılım", "Askeri", "Minecraft"]
    hedef = random.choice(liste)
    await interaction.response.send_message(f"🎮 İlk yazan kazanır: **`{hedef}`**")
    
    def check(m): return m.channel == interaction.channel and m.content.lower() == hedef.lower() and not m.author.bot
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        await interaction.channel.send(f"🏆 {msg.author.mention} kazandı!")
    except:
        await interaction.channel.send(f"⏰ Kimse yazamadı, kelime: `{hedef}` idi.")

# --- Kayıt Sistemi ---
@bot.tree.command(name="kayıt", description="Üyeyi kayıt eder.")
async def kayit(interaction: discord.Interaction, kullanici: discord.Member, isim: str, yas: int):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
    
    try:
        await kullanici.remove_roles(interaction.guild.get_role(KAYITSIZ_ROL_ID))
        await kullanici.add_roles(interaction.guild.get_role(KAYITLI_ROL_ID))
        await kullanici.edit(nick=f"{isim} | {yas}")
        await interaction.response.send_message(f"✅ {kullanici.mention} başarıyla kaydedildi.")
    except:
        await interaction.response.send_message("❌ Rol/Yetki hatası!", ephemeral=True)

# --- Diğer Komutlar ---
@bot.tree.command(name="destek-kur", description="Destek sistemini kurar.")
async def dkur(interaction: discord.Interaction):
    await interaction.channel.send(embed=discord.Embed(title="🔱 Destek", description="Butona basarak talep açabilirsin.", color=0x2ECC71), view=DestekButonu())
    await interaction.response.send_message("✅ Kuruldu.", ephemeral=True)

@bot.tree.command(name="bilgi", description="Sistem raporu.")
async def bilgi(interaction: discord.Interaction):
    uptime = int(time.time() - bot.start_time)
    await interaction.response.send_message(f"🔱 Ping: {round(bot.latency * 1000)}ms | Aktiflik: {uptime}sn")

@bot.tree.command(name="mesajtemizle", description="Mesajları siler.")
async def temizle(interaction: discord.Interaction, sayi: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=sayi)
    await interaction.followup.send(f"✅ {len(deleted)} mesaj temizlendi.", ephemeral=True)

# ==========================================
#               OLAYLAR (EVENTS)
# ==========================================
@bot.event
async def on_ready():
    print(f'------------------------------')
    print(f'🔱 {bot.user.name} AKTİF!')
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} ADET KOMUT SENKRONİZE EDİLDİ!")
    except Exception as e:
        print(f"❌ HATA: {e}")
    print(f'------------------------------')

if __name__ == "__main__":
    Thread(target=run_server).start()
    if TOKEN:
        bot.run(TOKEN)