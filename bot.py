import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
from datetime import datetime

RUTBE_HIYERARSI = [
    ("OR-1 Sözleşmeli Er", 1, 0),
    ("OR-2 Onbaşı", 2, 0),
    ("OR-3 Uzman Onbaşı", 3, 0),
    ("OR-4 Çavuş", 4, 0),
    ("OR-5 Uzman Çavuş", 5, 0),
    ("OR-6 Astsubay Kıdemli Çavuş", 6, 0),
    ("OR-7 Astsubay Üstçavuş", 7, 0),
    ("OR-8 Astsubay Başçavuş", 8, 0),
    ("OR-9 Astsubay Kıdemli Başçavuş", 9, 0),
    ("OF-1/A Asteğmen", 15, 0),
    ("OF-1/B Teğmen", 16, 0),
    ("OF-1/C Üstteğmen", 17, 50297823),
    ("OF-2 Yüzbaşı", 18, 50297795),
    ("OF-3 Binbaşı", 22, 50297786),
    ("OF-4 Yarbay", 23, 50212710),
    ("OF-5 Albay", 24, 50297779),
    ("OF-6 Tuğgeneral", 25, 50297765),
    ("OF-7 Tümgeneral", 31, 106625975),
    ("OF-8 Korgeneral", 32, 109072153),
    ("OF-9 Orgeneral", 33, 94616758),
    ("OF-10 Mareşal", 255, 50212581),
    ("Genelkurmay", 34, 109072136),
    ("Genelkurmay Başkanı", 35, 94616597),
    ("Yüksek Askeri Şûra", 35, 109072096),
    ("Geliştirici Ekibi", 36, 109072091),
    ("Yönetim Kurulu", 39, 109072057),
    ("Yönetim Kurulu B. Yardımcısı", 40, 94616751),
    ("Yönetim Kurulu Başkanı", 41, 94616570),
    ("Baş Geliştirici", 42, 94616579),
    ("Başbakan", 43, 94616576),
    ("Yönetim Kurulu Başkan", 44, 50297941),
    ("Başkomutan Yaveri", 150, 94616564),
    ("Başkomutan", 151, 50297900),
]

RUTBE_LISTESI = [r[0] for r in RUTBE_HIYERARSI]
RUTBE_SEVIYE = {r[0]: r[1] for r in RUTBE_HIYERARSI}
RUTBE_ROBLOX_ID = {r[0]: r[2] for r in RUTBE_HIYERARSI}
ROBLOX_GROUP_ID = os.environ.get('ROBLOX_GROUP_ID', '8124822')
ROBLOX_COOKIE = os.environ.get('ROBLOX_COOKIE', '')
IZINLI_KANAL = "rütbe-işlem"
MIN_YETKILI_SEVIYE = 25

class RankBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.session = None
        self.csrf_token = None

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        await self.get_csrf_token()
        await self.tree.sync()

    async def get_csrf_token(self):
        if not ROBLOX_COOKIE:
            return
        try:
            headers = {"Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}"}
            async with self.session.post("https://auth.roblox.com/v2/logout", headers=headers) as resp:
                self.csrf_token = resp.headers.get("x-csrf-token")
        except:
            pass

    async def on_ready(self):
        print(f'{self.user} aktif!')

    async def get_roblox_user_id(self, username):
        try:
            async with self.session.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("data"):
                        return data["data"][0]["id"]
        except:
            pass
        return None

    async def get_user_rank_in_group(self, user_id):
        try:
            async with self.session.get(f"https://groups.roblox.com/v2/users/{user_id}/groups/roles") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for g in data.get("data", []):
                        if str(g.get("group", {}).get("id")) == ROBLOX_GROUP_ID:
                            return g.get("role", {}).get("name"), g.get("role", {}).get("rank")
        except:
            pass
        return None, None

    async def set_roblox_rank(self, user_id, role_id):
        if not ROBLOX_COOKIE or role_id == 0:
            return False, "Roblox'ta yok"
        if not self.csrf_token:
            await self.get_csrf_token()
        headers = {"Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}", "X-CSRF-TOKEN": self.csrf_token, "Content-Type": "application/json"}
        try:
            async with self.session.patch(f"https://groups.roblox.com/v1/groups/{ROBLOX_GROUP_ID}/users/{user_id}", headers=headers, json={"roleId": role_id}) as resp:
                if resp.status == 200:
                    return True, "Değiştirildi!"
                elif resp.status == 403:
                    self.csrf_token = resp.headers.get("x-csrf-token")
                    headers["X-CSRF-TOKEN"] = self.csrf_token
                    async with self.session.patch(f"https://groups.roblox.com/v1/groups/{ROBLOX_GROUP_ID}/users/{user_id}", headers=headers, json={"roleId": role_id}) as r:
                        return r.status == 200, "Değiştirildi!" if r.status == 200 else "Hata"
        except:
            pass
        return False, "Hata"

    async def get_user_groups(self, user_id):
        try:
            async with self.session.get(f"https://groups.roblox.com/v2/users/{user_id}/groups/roles") as resp:
                if resp.status == 200:
                    return (await resp.json()).get("data", [])
        except:
            pass
        return []

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()

bot = RankBot()

def get_seviye(rutbe):
    return RUTBE_SEVIYE.get(rutbe, 0)

def get_rutbe_by_index(index):
    if 0 <= index < len(RUTBE_HIYERARSI):
        return RUTBE_HIYERARSI[index]
    return None

def find_rutbe_index(rutbe_name):
    for i, r in enumerate(RUTBE_HIYERARSI):
        if r[0] == rutbe_name:
            return i
    return -1

def kullanici_seviye(member):
    return max([get_seviye(r.name) for r in member.roles], default=0)

def check_channel(interaction):
    if interaction.channel.name != IZINLI_KANAL:
        return False, f"❌ Sadece **#{IZINLI_KANAL}** kanalında!"
    return True, ""

def check_permission(user_seviye, hedef_seviye):
    if user_seviye < MIN_YETKILI_SEVIYE:
        return False, "❌ En az **OF-6 Tuğgeneral** olmalısınız!"
    if hedef_seviye >= user_seviye:
        return False, "❌ Kendinizden yüksek/eşit rütbe veremezsiniz!"
    return True, ""

async def rutbe_autocomplete(interaction, current):
    return [app_commands.Choice(name=r, value=r) for r in RUTBE_LISTESI if current.lower() in r.lower()][:25]

@bot.tree.command(name="rütbe-terfi", description="Kullanıcıyı 1 rütbe yükselt")
@app_commands.describe(kullanici="Roblox adı", sebep="Sebep")
async def rutbe_terfi(interaction: discord.Interaction, kullanici: str, sebep: str):
    ok, msg = check_channel(interaction)
    if not ok:
        return await interaction.response.send_message(msg, ephemeral=True)
    
    await interaction.response.defer()
    
    roblox_id = await bot.get_roblox_user_id(kullanici)
    if not roblox_id:
        return await interaction.followup.send("❌ Kullanıcı bulunamadı!")
    
    current_rank, _ = await bot.get_user_rank_in_group(roblox_id)
    if not current_rank:
        return await interaction.followup.send("❌ Kullanıcı grupta değil!")
    
    current_index = find_rutbe_index(current_rank)
    if current_index == -1:
        return await interaction.followup.send(f"❌ Mevcut rütbe bulunamadı: {current_rank}")
    
    new_index = current_index + 1
    if new_index >= len(RUTBE_HIYERARSI):
        return await interaction.followup.send("❌ Zaten en yüksek rütbede!")
    
    new_rank = RUTBE_HIYERARSI[new_index]
    
    ok, msg = check_permission(kullanici_seviye(interaction.user), new_rank[1])
    if not ok:
        return await interaction.followup.send(msg)
    
    success, roblox_msg = await bot.set_roblox_rank(roblox_id, new_rank[2])
    roblox_status = f"✅ {roblox_msg}" if success else f"⚠️ {roblox_msg}"
    
    embed = discord.Embed(title="⬆️ TERFİ", color=0xC5A059, timestamp=datetime.now())
    embed.add_field(name="👤 Kullanıcı", value=kullanici, inline=True)
    embed.add_field(name="📊 Eski Rütbe", value=current_rank, inline=True)
    embed.add_field(name="🎖️ Yeni Rütbe", value=new_rank[0], inline=True)
    embed.add_field(name="📝 Sebep", value=sebep, inline=False)
    embed.add_field(name="🎮 Roblox", value=roblox_status, inline=False)
    embed.set_footer(text=f"Yapan: {interaction.user.display_name}")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="rütbe-tenzil", description="Kullanıcıyı 1 rütbe düşür")
@app_commands.describe(kullanici="Roblox adı", sebep="Sebep")
async def rutbe_tenzil(interaction: discord.Interaction, kullanici: str, sebep: str):
    ok, msg = check_channel(interaction)
    if not ok:
        return await interaction.response.send_message(msg, ephemeral=True)
    
    await interaction.response.defer()
    
    roblox_id = await bot.get_roblox_user_id(kullanici)
    if not roblox_id:
        return await interaction.followup.send("❌ Kullanıcı bulunamadı!")
    
    current_rank, _ = await bot.get_user_rank_in_group(roblox_id)
    if not current_rank:
        return await interaction.followup.send("❌ Kullanıcı grupta değil!")
    
    current_index = find_rutbe_index(current_rank)
    if current_index == -1:
        return await interaction.followup.send(f"❌ Mevcut rütbe bulunamadı: {current_rank}")
    
    new_index = current_index - 1
    if new_index < 0:
        return await interaction.followup.send("❌ Zaten en düşük rütbede!")
    
    new_rank = RUTBE_HIYERARSI[new_index]
    
    ok, msg = check_permission(kullanici_seviye(interaction.user), get_seviye(current_rank))
    if not ok:
        return await interaction.followup.send(msg)
    
    success, roblox_msg = await bot.set_roblox_rank(roblox_id, new_rank[2])
    roblox_status = f"✅ {roblox_msg}" if success else f"⚠️ {roblox_msg}"
    
    embed = discord.Embed(title="⬇️ TENZİL", color=0x601117, timestamp=datetime.now())
    embed.add_field(name="👤 Kullanıcı", value=kullanici, inline=True)
    embed.add_field(name="📊 Eski Rütbe", value=current_rank, inline=True)
    embed.add_field(name="🎖️ Yeni Rütbe", value=new_rank[0], inline=True)
    embed.add_field(name="📝 Sebep", value=sebep, inline=False)
    embed.add_field(name="🎮 Roblox", value=roblox_status, inline=False)
    embed.set_footer(text=f"Yapan: {interaction.user.display_name}")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="rütbe-değiştir", description="Rütbe değiştir")
@app_commands.describe(kullanici="Roblox adı", rutbe="Yeni rütbe", sebep="Sebep")
@app_commands.autocomplete(rutbe=rutbe_autocomplete)
async def rutbe_degistir(interaction: discord.Interaction, kullanici: str, rutbe: str, sebep: str):
    ok, msg = check_channel(interaction)
    if not ok:
        return await interaction.response.send_message(msg, ephemeral=True)
    ok, msg = check_permission(kullanici_seviye(interaction.user), get_seviye(rutbe))
    if not ok:
        return await interaction.response.send_message(msg, ephemeral=True)
    await interaction.response.defer()
    roblox_id = await bot.get_roblox_user_id(kullanici)
    if roblox_id:
        success, roblox_msg = await bot.set_roblox_rank(roblox_id, RUTBE_ROBLOX_ID.get(rutbe, 0))
        roblox_status = f"✅ {roblox_msg}" if success else f"⚠️ {roblox_msg}"
    else:
        roblox_status = "⚠️ Kullanıcı bulunamadı"
    embed = discord.Embed(title="🔄 DEĞİŞİKLİK", color=0x3E6D47, timestamp=datetime.now())
    embed.add_field(name="👤 Kullanıcı", value=kullanici, inline=True)
    embed.add_field(name="🎖️ Rütbe", value=rutbe, inline=True)
    embed.add_field(name="📝 Sebep", value=sebep, inline=False)
    embed.add_field(name="🎮 Roblox", value=roblox_status, inline=False)
    embed.set_footer(text=f"Yapan: {interaction.user.display_name}")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="grup-listele", description="Kullanıcının gruplarını listele")
@app_commands.describe(kullanici_adi="Roblox adı")
async def grup_listele(interaction: discord.Interaction, kullanici_adi: str):
    ok, msg = check_channel(interaction)
    if not ok:
        return await interaction.response.send_message(msg, ephemeral=True)
    await interaction.response.defer()
    user_id = await bot.get_roblox_user_id(kullanici_adi)
    if not user_id:
        return await interaction.followup.send(f"❌ **{kullanici_adi}** bulunamadı!")
    groups = await bot.get_user_groups(user_id)
    if not groups:
        return await interaction.followup.send(f"ℹ️ Grup yok.")
    embed = discord.Embed(title=f"📋 {kullanici_adi}", color=0x3E6D47)
    for g in groups[:10]:
        group, role = g.get("group", {}), g.get("role", {})
        prefix = "⭐" if str(group.get("id")) == ROBLOX_GROUP_ID else "🏢"
        embed.add_field(name=f"{prefix} {group.get('name')}", value=f"Rütbe: {role.get('name')}", inline=True)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="bot-durum", description="Bot durumu")
async def bot_durum(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 Bot", color=0x3E6D47)
    embed.add_field(name="Durum", value="✅ Aktif", inline=True)
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
