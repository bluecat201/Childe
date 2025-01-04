import asyncio
import discord
from discord.ext import commands
import json
import os

PREFIX_FILE = "prefixes.json"
WARNINGS_FILE = "warnings.json"

class Moderace(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Načítání warnů
        if os.path.exists(WARNINGS_FILE):
            with open(WARNINGS_FILE, "r") as f:
                self.warnings = json.load(f)
        else:
            self.warnings = {}

    #ban
    @commands.command(aliases=['Ban', 'BAN'], help="Zabanuješ uživatele")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.User = None, *, reason=None):
        if member is None:
            await ctx.send("Prosím zadejte ID#discriminator k banu")
        if member == ctx.author:
            await ctx.send("Nemůžeš zabanovat sám sebe")
        else:
            await member.ban(reason=reason)
            await ctx.send(f'{member.mention} byl zabanován z důvodu: {reason}.')

    #ban error
    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Omlouvám se ale pro použití tohoto commandu potřebuješ mít oprávnění **Zabanovat uživatele**.")

    #Kick
    @commands.command(aliases=['Kick','KICK'], help="Vyhodí uživatele ze serveru")
    @commands.has_permissions(kick_members=True) #oprávnění na kick?
    async def kick(self, ctx, member : discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} byl vyhozen z důvodu: {reason}.")

    #Nemá oprávnění na kick
    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Omlouvám se, ale pokud chcete použít tenhle command musíte mít oprávnění **vyhodit uživatele**.")

    #unmute
    @commands.command(aliases=['Unmute'], help="Odebereš mute uživately")
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member):
        guild = ctx.guild
        mutedRole = discord.utils.get(guild.roles, name="Muted")

        embed = discord.Embed(title="unmuted", description=f"{member.mention} was unmuted ", colour=discord.Colour.light_gray())
        await ctx.send(embed=embed)
        await member.send(f" Byl jsi unmutnut v: {guild.name}")
        await member.remove_roles(mutedRole)

    #mute
    @commands.command(aliases=['Mute'], help="Umlčíš uživatele")
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member=None, time=None,*,reason=None):
        if not member:
            await ctx.send("Musíte označit uživatele kterého chcete mutnout")
        elif not time:
            guild = ctx.guild
            mutedRole = discord.utils.get(guild.roles, name="Muted")

            if not mutedRole:
                mutedRole = await guild.create_role(name="Muted")

                for channel in guild.channels:
                    await channel.set_permissions(mutedRole, speak=False, send_messages=False, read_message_history=True, read_messages=False)
            if not reason:
                reason="No reason given"
            embed = discord.Embed(title="muted", description=f"{member.mention} was muted ", colour=discord.Colour.light_gray())
            embed.add_field(name="reason:", value=reason, inline=False)
            await ctx.send(embed=embed)
            await member.send(f" Byl jsi mutnut v: {guild.name} Důvod: {reason}")
            await member.add_roles(mutedRole, reason=reason)
        else:
            if not reason:
                reason="No reason given"
            #teď manipulace s časem mutu

            try:
                seconds = int(time[:-1]) #získá číslo z časového argumentu
                duration = time[-1] #získá jednotku času, s, m, h, d
                if duration == "s":
                    seconds = seconds*1
                elif duration == "m":
                    seconds = seconds * 60
                elif duration == "h":
                    seconds = seconds * 60 * 60
                elif duration == "d":
                    seconds = seconds * 86400
                else:
                    await ctx.send("Nesprávně zadaný čas")
                    return
            except Exception as e:
                print(e)
                await ctx.send("Nesprávně zadaný čas")
                return
            guild = ctx.guild
            Muted = discord.utils.get(guild.roles,name="Muted")
            if not Muted:
                Muted = await guild.create_role(name="Muted")
                for channel in guild.channels:
                    await channel.set_permissions(Muted, speak=False, send_message=False, read_message_history=True, read_messages=False)
            await member.add_roles(Muted, reason=reason)
            muted_embed = discord.Embed(title="Muted a user", description=f"{member.mention} Byl mutnut {ctx.author.mention} z důvodu *{reason}* na {time}")
            await ctx.send(embed=muted_embed)
            await member.send(f" Byl jsi mutnut v: {guild.name} z důvodu *{reason}* na dobu {seconds}")
            await asyncio.sleep(seconds)
            await member.remove_roles(Muted)
            unmute_embed = discord.Embed(title="Konec mutu",description=f"{member.mention} byl unmutnut")
            await ctx.send(embed=unmute_embed)
            await member.send(f" Byl jsi unmutnut v: {guild.name}")


    #Set prefix
    @commands.command(aliases=["Setprefix", "SETPREFIX"], help="Nastaví prefix bota")
    @commands.has_permissions(manage_messages=True)
    async def setprefix(self, ctx, *, prefix=None):
        if not prefix:
            return await ctx.send("Musíte zadat nový prefix.")

        guild_id = str(ctx.guild.id)  # Ukládáme ID jako string

        # Načíst existující prefixy
        if os.path.exists(PREFIX_FILE):
            with open(PREFIX_FILE, "r") as f:
                prefixes = json.load(f)
        else:
            prefixes = {}

        # Přepsání nebo přidání prefixu
        prefixes[guild_id] = prefix

        # Uložení zpět do souboru
        with open(PREFIX_FILE, "w") as f:
            json.dump(prefixes, f, indent=4)  # Použijte indentaci pro přehlednější JSON

        await ctx.send(f"Prefix nastaven na: {prefix}")
    
    #Set prefix error
    @setprefix.error
    async def setprefix_error(self,ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Omlouvám se, ale pro použití tohoto příkazu potřebuješ oprávnění: **Správa zpráv**.")

    #purge
    @commands.command(aliases=['Purge'], help="Vymaže určitý počet zpráv", pass_context=True)
    @commands.has_permissions(administrator=True)
    async def purge(self, ctx, limit: int):
            await ctx.message.delete()
            await ctx.channel.purge(limit=limit)
            await ctx.send('Vymazáno {}'.format(ctx.author.mention))

    @purge.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Nemůžeš tohle udělat")


    #sudo
    @commands.has_guild_permissions(administrator=True)
    @commands.command(aliases=['Sudo','SUDO'], help="Childe napíše tvoji zprávu")
    async def sudo(self, ctx, *, arg):
        await ctx.send(arg)
        await ctx.message.delete()

    #nemá oprávnění
    @sudo.error
    async def sudo_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Omlouvám se ale pro použití tohoto commandu potřebuješ mít opravnění **Administrator**.")

    #unban
    @commands.command(aliases=['ub','UNBAN','Unban'], help="Odebereš zákaz uživately")
    @commands.has_guild_permissions(ban_members=True) #má oprávnění na ban?
    @commands.bot_has_permissions(ban_members=True) #má bot oprávnění na ban?
    async def unban(self, ctx, member: discord.User = None, *, reason=None): 

        if reason is None:  #uživatel neuvedl důvod
            reason = f"{ctx.author.name}#{ctx.author.discriminator} Neuvedl žádný důvod"
        if member is None: #uživatel nezadal uživatele k unbanu
            await ctx.send("Prosím zadejte ID#discriminator k unbanu")
        x = len(reason)   
        if x > 460: # 460 = limit znaků na reason
            return await ctx.send('Důvod musí mít maximálně 460 znaků')
        else:
            await ctx.guild.unban(member, reason=reason)
            await ctx.send(f'{member} byl odbannut z důvodu: {reason}')
        
    #Nemá oprávnění/nebyl nalezen uživatel
    @unban.error
    async def unban_error(self, ctx, error): 
        if isinstance(error, commands.MemberNotFound): #nebyl nalezen uživatel k unbanu
                        await ctx.send("Žádný uživatel nebyl nalezen")
        elif isinstance(error, commands.BotMissingPermissions): #bot nemá oprávnění
                        await ctx.send("Bot nemá oprávnění zabanovat uživatele aby mohl použít tenhle command.")
        elif isinstance(error,commands.MissingPermissions): #uživatel nemá oprávnění
                        await ctx.send("Nemáš oprávnění zabanovat uživatele aby mohl použít tenhle command")

    #warn
    @commands.command(aliases=['Warn'], help="Varuje uživatele.")
    @commands.has_permissions(administrator=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        if not reason:
            return await ctx.send("Musíte uvést důvod.")
        
        guild_id = str(ctx.guild.id)
        member_id = str(member.id)
        
        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
        
        if member_id not in self.warnings[guild_id]:
            self.warnings[guild_id][member_id] = []

        self.warnings[guild_id][member_id].append({
            "reason": reason,
            "admin": ctx.author.id
        })

        with open(WARNINGS_FILE, "w") as f:
            json.dump(self.warnings, f)

        await ctx.send(f"{member.mention} byl varován. Důvod: {reason}")

    #warnings
    @commands.command(aliases=['Warnings'], help="Zobrazí varování uživatele.")
    @commands.has_permissions(administrator=True)
    async def warnings(self, ctx, member: discord.Member):
        guild_id = str(ctx.guild.id)
        member_id = str(member.id)

        if guild_id not in self.warnings or member_id not in self.warnings[guild_id]:
            return await ctx.send(f"{member.mention} nemá žádná varování.")

        embed = discord.Embed(title=f"Varování uživatele {member.name}", color=discord.Color.red())
        for idx, warning in enumerate(self.warnings[guild_id][member_id], 1):
            admin = ctx.guild.get_member(warning["admin"])
            admin_name = admin.name if admin else "Neznámý"
            embed.add_field(
                name=f"Varování {idx}",
                value=f"Důvod: {warning['reason']}\nAdmin: {admin_name}",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderace(bot))
