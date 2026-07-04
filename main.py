
"""
Social Media Finder Pro v3.0
Geliştirici: @developer
Discord: developer#1234

Açıklama: Discord üzerinden kullanıcı adı girerek tüm sosyal medya platformlarında profil araması yapar.
"""

import discord
from discord.ext import commands
import requests
import sqlite3
from datetime import datetime
import asyncio
import json
import os

# ----------------------------------------------
# KONFIGÜRASYON
# ----------------------------------------------

TOKEN = "MTUyMzA2MDM0NzQ3NTMyOTExNA.G1BFJM.A8m2pGJkY-jA8wlvWwcn4sluqUD_iLBSJyIgLs"
VERSION = "3.0"
AUTHOR = "@developer"

# ----------------------------------------------
# VERİTABANI
# ----------------------------------------------

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('data.db')
        self.cursor = self.conn.cursor()
        self._init_db()
    
    def _init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                username TEXT,
                platform TEXT,
                date TEXT
            )
        ''')
        self.conn.commit()
    
    def log_search(self, user_id, username, platform):
        self.cursor.execute(
            'INSERT INTO searches (user_id, username, platform, date) VALUES (?, ?, ?, ?)',
            (user_id, username, platform, datetime.now().isoformat())
        )
        self.conn.commit()
    
    def get_stats(self):
        total = self.cursor.execute('SELECT COUNT(*) FROM searches').fetchone()[0]
        return total

# ----------------------------------------------
# TARAYICI
# ----------------------------------------------

class SocialScanner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.sites = {
            'Instagram': 'https://instagram.com/{}',
            'Twitter': 'https://twitter.com/{}',
            'TikTok': 'https://tiktok.com/@{}',
            'YouTube': 'https://youtube.com/@{}',
            'Reddit': 'https://reddit.com/user/{}',
            'GitHub': 'https://github.com/{}',
            'Pinterest': 'https://pinterest.com/{}',
            'Spotify': 'https://open.spotify.com/user/{}',
            'Twitch': 'https://twitch.tv/{}',
            'Telegram': 'https://t.me/{}',
            'Tumblr': 'https://{}.tumblr.com',
            'Medium': 'https://medium.com/@{}',
            'SoundCloud': 'https://soundcloud.com/{}',
            'Vimeo': 'https://vimeo.com/{}',
            'Dribbble': 'https://dribbble.com/{}',
            'Behance': 'https://behance.net/{}',
            'Snapchat': 'https://snapchat.com/add/{}',
            'Flickr': 'https://flickr.com/people/{}',
            'DeviantArt': 'https://deviantart.com/{}'
        }
    
    def scan(self, username):
        results = []
        
        for name, url in self.sites.items():
            try:
                r = self.session.get(url.format(username), timeout=5)
                if r.status_code == 200:
                    results.append({
                        'platform': name,
                        'url': url.format(username),
                        'details': self._get_details(name, username)
                    })
            except:
                pass
        
        return results
    
    def _get_details(self, platform, username):
        """Platforma özel detaylar"""
        details = {}
        
        try:
            if platform == 'GitHub':
                r = self.session.get(f'https://api.github.com/users/{username}')
                if r.status_code == 200:
                    data = r.json()
                    details = {
                        'İsim': data.get('name', '-'),
                        'Bio': data.get('bio', '-')[:80],
                        'Konum': data.get('location', '-'),
                        'Takipçi': data.get('followers', 0),
                        'Takip': data.get('following', 0),
                        'Repo': data.get('public_repos', 0)
                    }
            
            elif platform == 'Reddit':
                r = self.session.get(
                    f'https://www.reddit.com/user/{username}/about.json',
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                if r.status_code == 200:
                    data = r.json().get('data', {})
                    details = {
                        'Karma': data.get('total_karma', 0),
                        'Post Karma': data.get('post_karma', 0),
                        'Yorum Karma': data.get('comment_karma', 0),
                        'Üyelik': datetime.fromtimestamp(data.get('created_utc', 0)).strftime('%Y-%m-%d')
                    }
            
            elif platform == 'Instagram':
                try:
                    r = self.session.get(
                        f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}',
                        headers={'X-IG-App-ID': '936619743392459'}
                    )
                    if r.status_code == 200:
                        user = r.json().get('data', {}).get('user', {})
                        details = {
                            'İsim': user.get('full_name', '-'),
                            'Bio': user.get('biography', '-')[:80],
                            'Takipçi': user.get('edge_followed_by', {}).get('count', 0),
                            'Takip': user.get('edge_follow', {}).get('count', 0),
                            'Gönderi': user.get('edge_owner_to_timeline_media', {}).get('count', 0)
                        }
                except:
                    pass
            
            else:
                details = {'Durum': 'Aktif'}
                
        except:
            details = {'Bilgi': 'Detay alınamadı'}
        
        return details

# ----------------------------------------------
# DISCORD BOT
# ----------------------------------------------

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
db = Database()
scanner = SocialScanner()
start_time = datetime.now()

@bot.event
async def on_ready():
    print(f'✅ {bot.user} giriş yaptı | {len(bot.guilds)} sunucu')
    await bot.change_presence(activity=discord.Game(name='!ara | 19+ platform'))

# ----------------------------------------------
# KOMUTLAR
# ----------------------------------------------

@bot.command(name='ara')
async def cmd_search(ctx, *, username: str):
    """Kullanıcı adı ile tüm platformlarda ara"""
    
    mesaj = await ctx.send(f'🔍 **{username}** aranıyor...')
    
    bulunan = scanner.scan(username)
    
    if not bulunan:
        embed = discord.Embed(
            title='❌ Bulunamadı',
            description=f'**{username}** hiçbir platformda yok.',
            color=0xff0000
        )
        await mesaj.edit(content=None, embed=embed)
        return
    
    embed = discord.Embed(
        title=f'👤 {username}',
        description=f'**{len(bulunan)}** platformda hesap bulundu',
        color=0x00ff00
    )
    
    liste = ''
    for i, b in enumerate(bulunan, 1):
        liste += f'**{i}.** {b["platform"]}\n'
    
    embed.add_field(name='📌 Platformlar', value=liste, inline=False)
    embed.add_field(
        name='📝 Seçim Yap',
        value='Hangisini görmek istediğini **numara** olarak yaz',
        inline=False
    )
    embed.set_footer(text=f'{ctx.author.name} | 30 saniyen var')
    
    await mesaj.edit(content=None, embed=embed)
    
    def kontrol(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
    
    try:
        secim = await bot.wait_for('message', timeout=30, check=kontrol)
        sayi = int(secim.content)
        
        if 1 <= sayi <= len(bulunan):
            secilen = bulunan[sayi - 1]
            await _detay_goster(ctx, username, secilen, bulunan)
            db.log_search(str(ctx.author.id), username, secilen['platform'])
        else:
            await ctx.send(f'❌ 1-{len(bulunan)} arası sayı gir.')
            
    except asyncio.TimeoutError:
        await ctx.send(f'⏰ Zaman doldu. Tekrar: `!ara {username}`')

async def _detay_goster(ctx, username, secilen, tumu):
    embed = discord.Embed(
        title=f'📊 {secilen["platform"]}',
        description=f'@{username}',
        color=0x3498db
    )
    
    embed.add_field(name='🔗 URL', value=secilen['url'], inline=False)
    
    detaylar = secilen.get('details', {})
    if detaylar:
        metin = ''
        for key, value in detaylar.items():
            if value and str(value) != '-':
                metin += f'**{key}:** {value}\n'
        if metin:
            embed.add_field(name='📋 Detaylar', value=metin, inline=False)
    
    diger = [p for p in tumu if p['platform'] != secilen['platform']]
    if diger:
        liste = '\n'.join([f'• {p["platform"]}' for p in diger[:5]])
        if len(diger) > 5:
            liste += f'\n*+{len(diger)-5} platform*'
        embed.add_field(name='📌 Diğer Platformlar', value=liste, inline=False)
    
    embed.set_footer(text='✅ Detay gönderildi')
    await ctx.send(embed=embed)

@bot.command(name='detay')
async def cmd_detail(ctx, username: str, platform: str = None):
    """Direkt detay göster"""
    
    await ctx.send(f'📊 **{username}** taranıyor...')
    
    bulunan = scanner.scan(username)
    
    if not bulunan:
        await ctx.send(f'❌ {username} bulunamadı.')
        return
    
    if platform:
        hedef = next((p for p in bulunan if p['platform'].lower() == platform.lower()), None)
        if not hedef:
            liste = '\n'.join([f'• {p["platform"]}' for p in bulunan])
            await ctx.send(f'❌ {platform} bulunamadı.\n\n**Bulunanlar:**\n{liste}')
            return
        await _detay_goster(ctx, username, hedef, bulunan)
    else:
        await _detay_goster(ctx, username, bulunan[0], bulunan)

@bot.command(name='platformlar')
async def cmd_platforms(ctx):
    """Tüm platformları listele"""
    
    platformlar = list(scanner.sites.keys())
    
    embed = discord.Embed(
        title='🌐 Platformlar',
        description=f'Toplam **{len(platformlar)}** platform',
        color=0x3498db
    )
    
    for i in range(0, len(platformlar), 10):
        grup = platformlar[i:i+10]
        embed.add_field(
            name=f'Grup {i//10 + 1}',
            value='\n'.join([f'• {p}' for p in grup]),
            inline=True
        )
    
    await ctx.send(embed=embed)

@bot.command(name='istatistik')
async def cmd_stats(ctx):
    """Bot istatistikleri"""
    
    toplam_arama = db.get_stats()
    uptime = str(datetime.now() - start_time).split('.')[0]
    
    embed = discord.Embed(
        title='📊 İstatistikler',
        color=0x3498db
    )
    
    embed.add_field(name='🏠 Sunucu', value=len(bot.guilds), inline=True)
    embed.add_field(name='👥 Kullanıcı', value=len(bot.users), inline=True)
    embed.add_field(name='⏱️ Çalışma', value=uptime, inline=True)
    embed.add_field(name='🔍 Arama', value=toplam_arama, inline=True)
    embed.add_field(name='📱 Platform', value=len(scanner.sites), inline=True)
    embed.add_field(name='📌 Versiyon', value='3.0', inline=True)
    
    embed.set_footer(text='Social Media Finder Pro')
    await ctx.send(embed=embed)

@bot.command(name='yardim')
async def cmd_help(ctx):
    """Yardım menüsü"""
    
    embed = discord.Embed(
        title='🆘 Yardım',
        description='Kullanıcı adı ile tüm platformlarda ara',
        color=0x3498db
    )
    
    embed.add_field(
        name='🎯 Komutlar',
        value=(
            '`!ara <kullanıcı>` - Tüm platformlarda ara\n'
            '`!detay <kullanıcı> [platform]` - Detay göster\n'
            '`!platformlar` - Tüm platformlar\n'
            '`!istatistik` - Bot istatistikleri\n'
            '`!yardim` - Bu menü'
        ),
        inline=False
    )
    
    embed.add_field(
        name='📝 Örnek',
        value=(
            '`!ara ahmet` → Bulunanları listeler, seçim yaparsın\n'
            '`!detay ahmet instagram` → Direkt Instagram detayı'
        ),
        inline=False
    )
    
    embed.add_field(
        name='👨‍💻 Geliştirici',
        value='@developer',
        inline=False
    )
    
    embed.set_footer(text='Social Media Finder Pro v3.0')
    await ctx.send(embed=embed)

# ----------------------------------------------
# HATA YAKALAMA
# ----------------------------------------------

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Eksik bilgi. Örnek: `!ara ahmet123`')
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send('❌ Bilinmeyen komut. `!yardim` yaz.')
    else:
        await ctx.send(f'❌ Hata: {str(error)[:80]}')

# ----------------------------------------------
# BAŞLAT
# ----------------------------------------------

if __name__ == '__main__':
    print('\n' + '='*50)
    print('  SOCIAL MEDIA FINDER PRO v3.0')
    print('  Geliştirici: @developer')
    print('='*50 + '\n')
    
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f'Hata: {e}')
        input('Enter tuşuna bas...')
