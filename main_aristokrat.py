import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
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
    return "🔱 Aristokrat Bot 7/24 Aktif ve Çalışıyor!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# ==========================================
#               AYARLAR
# ==========================================
TOKEN = os.environ.get("DISCORD_TOKEN") # Buraya şifreyi yazma, aynen böyle kalsın!
# Kayıt & Hoş Geldin Ayarları
KAYITSIZ_ROL_ID = 1488679958216839278
KAYITLI_ROL_ID = 1488679806152478872
HOSGELDIN_KANAL_ID = 1488671987432689887

# Destek (Ticket) Ayarları
DESTEK_KATEGORI_ID = 1488932448552353934  
YETKILI_ROL_ID = 1488679118857044119      

# Bilgi Komutu Ayarları (Beyaz Liste Roller)
BILGI_YETKILI_ROLLER = [
    1488677638049366076, 
    1488677820547731556, 
    1488678029684117746, 
    1488678146160197842
]

# ==========================================
#         DESTEK SİSTEMİ BUTONLARI
# ==========================================
class KapatButonu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Talebi Kapat", style=discord.ButtonStyle.red, emoji="🔒", custom_id="destek_kapat")
    async def destek_kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔒 Destek Talebi Sonlandırılıyor",
            description="Bu kanal **5 saniye** içerisinde kalıcı olarak silinecektir.\n\n*Aristokrat hizmetlerini tercih ettiğiniz için teşekkürler.*",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class DestekButonu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Destek Talebi Oluştur", style=discord.ButtonStyle.green, emoji="🛡️", custom_id="destek_ac")
    async def destek_ac(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        user = interaction.user
        yetkili_rol = guild.get_role(YETKILI_ROL_ID)
        kanal_adi = f"ticket-{user.name.lower()}"
        
        existing_channel = discord.utils.get(guild.channels, name=kanal_adi)
        if existing_channel:
            await interaction.followup.send(f"⚠️ Zaten aktif bir destek talebiniz bulunuyor: {existing_channel.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            yetkili_rol: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        try:
            category = guild.get_channel(DESTEK_KATEGORI_ID)
            target_category = category if isinstance(category, discord.CategoryChannel) else None
            
            ticket_channel = await guild.create_text_channel(name=kanal_adi, category=target_category, overwrites=overwrites)
            await interaction.followup.send(f"✅ Destek talebiniz oluşturuldu: {ticket_channel.mention}", ephemeral=True)
            
            embed = discord.Embed(
                title="🔱 Aristokrat Destek Birimi",
                description=f"Merhaba {user.mention}, talebiniz başarıyla yetkililerimize iletildi.",
                color=0x2f3136,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="👤 Kullanıcı", value=user.mention, inline=True)
            embed.add_field(name="🏛️ Departman", value="Genel Destek", inline=True)
            embed.add_field(name="📜 Talimat", value="Lütfen sorununuzu detaylıca buraya yazın.", inline=False)
            embed.set_footer(text="İşleminiz bittiğinde 'Talebi Kapat' butonuna basınız.")
            
            await ticket_channel.send(content=f"{user.mention} | {yetkili_rol.mention if yetkili_rol else ''}", embed=embed, view=KapatButonu())
            
        except Exception as e:
            await interaction.followup.send(f"❌ Bir hata oluştu: {e}", ephemeral=True)

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
        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} adet Slash komutu başarıyla senkronize edildi!")
        except Exception as e:
            print(f"❌ Senkronizasyon hatası: {e}")

bot = AristokratBot()

# ==========================================
#               SLASH KOMUTLARI
# ==========================================

# --- 1. KAYIT ---
@bot.tree.command(name="kayıt", description="Üyeyi kayıt eder (İsim | Yaş).")
@app_commands.describe(kullanici="Kayıt edilecek kişi", isim="İsmi", yas="Yaşı")
async def kayit(interaction: discord.Interaction, kullanici: discord.Member, isim: str, yas: int):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
    
    k_siz = interaction.guild.get_role(KAYITSIZ_ROL_ID)
    k_li = interaction.guild.get_role(KAYITLI_ROL_ID)
    try:
        if k_siz in kullanici.roles: await kullanici.remove_roles(k_siz)
        if k_li: await kullanici.add_roles(k_li)
        await kullanici.edit(nick=f"{isim} | {yas}")
        await interaction.response.send_message(f"✅ {kullanici.mention} başarıyla kayıt edildi.")
    except:
        await interaction.response.send_message("❌ Rol yetkisi hatası! Botun rolünü en üste taşı.", ephemeral=True)

# --- 2. MESAJ TEMİZLE ---
@bot.tree.command(name="mesajtemizle", description="Belirtilen sayıda mesajı temizler.")
@app_commands.describe(sayi="Kaç mesaj silinsin?")
async def temizle(interaction: discord.Interaction, sayi: int):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
    if sayi < 1 or sayi > 100:
        return await interaction.response.send_message("⚠️ 1 ile 100 arasında sayı girin.", ephemeral=True)
    
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=sayi)
    await interaction.followup.send(f"✅ {len(deleted)} adet mesaj silindi.", ephemeral=True)

# --- 3. ROL VER & ROL AL ---
@bot.tree.command(name="rolver", description="Bir üyeye rol verir.")
async def rolver(interaction: discord.Interaction, kullanici: discord.Member, rol: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
    try:
        await kullanici.add_roles(rol)
        await interaction.response.send_message(f"✅ {kullanici.mention} kullanıcısına {rol.mention} verildi.")
    except:
        await interaction.response.send_message("❌ Yetki hatası!", ephemeral=True)

@bot.tree.command(name="rolal", description="Bir üyeden rol alır.")
async def rolal(interaction: discord.Interaction, kullanici: discord.Member, rol: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        return await interaction.response.send_message("❌ Yetkin yok!", ephemeral=True)
    try:
        await kullanici.remove_roles(rol)
        await interaction.response.send_message(f"✅ {kullanici.mention} kullanıcısından {rol.mention} alındı.")
    except:
        await interaction.response.send_message("❌ Yetki hatası!", ephemeral=True)

# --- 4. CEZA KOMUTLARI (Mute, Kick, Ban) ---
@bot.tree.command(name="mute", description="Kullanıcıyı belirli bir süre susturur.")
async def mute(interaction: discord.Interaction, kullanici: discord.Member, dakika: int):
    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message("❌ Üyeleri susturma yetkiniz yok!", ephemeral=True)
    try:
        await kullanici.timeout(timedelta(minutes=dakika), reason=f"{interaction.user} susturdu.")
        await interaction.response.send_message(f"🤐 {kullanici.mention} **{dakika}** dakika susturuldu.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="kick", description="Kullanıcıyı sunucudan atar.")
async def kick(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Belirtilmedi"):
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message("❌ Üyeleri atma yetkiniz yok!", ephemeral=True)
    try:
        await kullanici.kick(reason=sebep)
        await interaction.response.send_message(f"👢 {kullanici.mention} atıldı. Sebep: **{sebep}**")
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

@bot.tree.command(name="ban", description="Kullanıcıyı sunucudan yasaklar.")
async def ban(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Belirtilmedi"):
    if not interaction.user.guild_permissions.ban_members:
        return await interaction.response.send_message("❌ Üyeleri yasaklama yetkiniz yok!", ephemeral=True)
    try:
        await kullanici.ban(reason=sebep)
        await interaction.response.send_message(f"🔨 {kullanici.mention} banlandı. Sebep: **{sebep}**")
    except Exception as e:
        await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

# --- 5. DESTEK KURULUM KOMUTU ---
@bot.tree.command(name="destek-kur", description="Aristokrat Destek Sistemini kurar.")
async def destek_kur(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sadece yöneticiler kullanabilir!", ephemeral=True)

    embed = discord.Embed(
        title="🔱 Aristokrat İletişim Merkezi",
        description="Sunucumuzla ilgili her türlü sorun veya önerinizi buradan iletebilirsiniz.\n\n**🛡️ Güvenli Destek:** Sadece siz ve yetkililer görür.",
        color=discord.Color.gold()
    )
    await interaction.channel.send(embed=embed, view=DestekButonu())
    await interaction.response.send_message("✅ Destek sistemi aktif edildi.", ephemeral=True)

# --- 6. BİLGİ KOMUTU ---
@bot.tree.command(name="bilgi", description="Sunucu ve sistem teknik verilerini gösterir.")
async def bilgi(interaction: discord.Interaction):
    user_roles = [role.id for role in interaction.user.roles]
    is_authorized = any(role_id in BILGI_YETKILI_ROLLER for role_id in user_roles)
    
    if not interaction.user.guild_permissions.administrator and not is_authorized:
        return await interaction.response.send_message("❌ Bu gizli bilgilere erişim yetkiniz yok!", ephemeral=True)

    guild = interaction.guild
    toplam_uye = guild.member_count
    bot_sayisi = len([m for m in guild.members if m.bot])
    
    uptime_seconds = int(round(time.time() - bot.start_time))
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    embed = discord.Embed(title=f"🔱 {guild.name} | Sistem Raporu", color=0x00ffcc, timestamp=datetime.now())
    embed.add_field(name="👥 Nüfus", value=f"**Toplam:** {toplam_uye}\n**Üye:** {toplam_uye - bot_sayisi}\n**Bot:** {bot_sayisi}", inline=True)
    embed.add_field(name="⚙️ Teknik", value=f"**Ping:** {round(bot.latency * 1000)}ms\n**Uptime:** {hours}s {minutes}dk\n**Kanal:** {len(guild.channels)}", inline=True)
    if guild.icon: embed.set_thumbnail(url=guild.icon.url)
    
    await interaction.response.send_message(embed=embed)

# ==========================================
#               EVENTLER (OLAYLAR)
# ==========================================
@bot.event
async def on_member_join(member):
    rol = member.guild.get_role(KAYITSIZ_ROL_ID)
    if rol:
        try: await member.add_roles(rol)
        except: pass

    channel = bot.get_channel(HOSGELDIN_KANAL_ID)
    if channel:
        u = int(member.created_at.timestamp())
        mesaj = (
            f"Merhabalar {member.mention}, aramıza hoşgeldin. Seninle beraber sunucumuz "
            f"**{member.guild.member_count}** üye sayısına ulaştı. 🎉\n\n"
            f"Hesabın <t:{u}:f> tarihinde <t:{u}:R> oluşturulmuş!\n\n"
            f"Sunucuya erişebilmek için <#1488907101307797685> odalarında kayıt olup ismini ve "
            f"yaşını belirtmen gerekmektedir!\n\n"
            f"<#1488699145043837038> kanalından sunucu kurallarımızı okumayı ihmal etme!"
        )
        await channel.send(mesaj)

@bot.event
async def on_ready():
    print(f'------------------------------')
    print(f'🔱 {bot.user.name} İMPARATORLUĞU YÖNETMEYE HAZIR!')
    print(f'Tüm Sistemler (Kayıt, Moderasyon, Destek, Bilgi) Tek Dosyada Aktif.')
    print(f'------------------------------')

# ==========================================
#          RENDER & 7/24 ÇALIŞTIRMA
# ==========================================
if __name__ == "__main__":
    # Render'ın portunu yakala (Yoksa 10000 kullan)
    port = int(os.environ.get("PORT", 10000))
    
    # Flask sunucusunu botla çakışmaması için ayrı kolda başlat
    def run_flask():
        app.run(host='0.0.0.0', port=port)

    # Web sunucusunu başlat (Arka planda)
    Thread(target=run_flask).start()
    
    # Botu ana kolda başlat
    if TOKEN:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"❌ Bot giriş yaparken hata oluştu: {e}")
    else:
        print("❌ HATA: DISCORD_TOKEN bulunamadı! Render panelinde 'Environment Variables' kısmını kontrol et.")