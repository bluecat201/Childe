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
    @commands.command(aliases=['Ban', 'BAN'], help="Ban user")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.User = None, *, reason=None):
        if member is None:
            await ctx.send("Please enter ID#discriminator to ban")
        if member == ctx.author:
            await ctx.send("You can't ban yourself")
        else:
            await member.ban(reason=reason)
            await ctx.send(f'{member.mention} was banned for a reason: {reason}.')

    #ban error
    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("I'm sorry, but to use this command you need to have **Ban user** permission.")

    #Kick
    @commands.command(aliases=['Kick','KICK'], help="Kicks the user off the server")
    @commands.has_permissions(kick_members=True) #oprávnění na kick?
    async def kick(self, ctx, member : discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} was kicked for cause: {reason}.")

    #Nemá oprávnění na kick
    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("I'm sorry, but if you want to use this command you must have permission to **kick user**.")

    #unmute
    @commands.command(aliases=['Unmute'], help="You remove mute from user")
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member):
        guild = ctx.guild
        mutedRole = discord.utils.get(guild.roles, name="Muted")

        embed = discord.Embed(title="unmuted", description=f"{member.mention} was unmuted ", colour=discord.Colour.light_gray())
        await ctx.send(embed=embed)
        await member.send(f"You were unmutted in: {guild.name}")
        await member.remove_roles(mutedRole)

    #mute
    @commands.command(aliases=['Mute'], help="You will mute user")
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member=None, time=None,*,reason=None):
        if not member:
            await ctx.send("You must mark the user you want to mute")
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
            await member.send(f" You were muted in: {guild.name} Reason: {reason}")
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
                    await ctx.send("Incorrectly entered time")
                    return
            except Exception as e:
                print(e)
                await ctx.send("Incorrectly entered time")
                return
            guild = ctx.guild
            Muted = discord.utils.get(guild.roles,name="Muted")
            if not Muted:
                Muted = await guild.create_role(name="Muted")
                for channel in guild.channels:
                    await channel.set_permissions(Muted, speak=False, send_message=False, read_message_history=True, read_messages=False)
            await member.add_roles(Muted, reason=reason)
            muted_embed = discord.Embed(title="Muted a user", description=f"{member.mention} was muted by {ctx.author.mention} z důvodu *{reason}* na {time}")
            await ctx.send(embed=muted_embed)
            await member.send(f" You were muted in: {guild.name} for *{reason}* for {seconds}")
            await asyncio.sleep(seconds)
            await member.remove_roles(Muted)
            unmute_embed = discord.Embed(title="End of mute",description=f"{member.mention} was unmuted")
            await ctx.send(embed=unmute_embed)
            await member.send(f"You were unmuted in: {guild.name}")


    #Set prefix
    @commands.command(aliases=["Setprefix", "SETPREFIX"], help="Set prefix of bot")
    @commands.has_permissions(manage_messages=True)
    async def setprefix(self, ctx, *, prefix=None):
        if not prefix:
            return await ctx.send("You must enter a new prefix.")

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

        await ctx.send(f"Prefix set to: {prefix}")
    
    #Set prefix error
    @setprefix.error
    async def setprefix_error(self,ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Sorry, but you need permission to use this command: **Manage messages**.")

    #purge
    @commands.command(aliases=['Purge'], help="Deletes a certain number of messages", pass_context=True)
    @commands.has_permissions(administrator=True)
    async def purge(self, ctx, limit: int):
            await ctx.message.delete()
            await ctx.channel.purge(limit=limit)
            await ctx.send('Deleted {}'.format(ctx.author.mention))

    @purge.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You can't do this")


    #sudo
    @commands.has_guild_permissions(administrator=True)
    @commands.command(aliases=['Sudo','SUDO'], help="Childe will write your message")
    async def sudo(self, ctx, *, arg):
        await ctx.send(arg)
        await ctx.message.delete()

    #nemá oprávnění
    @sudo.error
    async def sudo_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Sorry, but to use this command you need **Administrator** privileges.")

    #unban
    @commands.command(aliases=['ub','UNBAN','Unban'], help="You unban users")
    @commands.has_guild_permissions(ban_members=True) #má oprávnění na ban?
    @commands.bot_has_permissions(ban_members=True) #má bot oprávnění na ban?
    async def unban(self, ctx, member: discord.User = None, *, reason=None): 

        if reason is None:  #uživatel neuvedl důvod
            reason = f"{ctx.author.name}#{ctx.author.discriminator} gave no reason"
        if member is None: #uživatel nezadal uživatele k unbanu
            await ctx.send("Please enter ID#discriminator to unban")
        x = len(reason)   
        if x > 460: # 460 = limit znaků na reason
            return await ctx.send('The reason must be a maximum of 460 characters')
        else:
            await ctx.guild.unban(member, reason=reason)
            await ctx.send(f'{member} was unbanned for reason: {reason}')
        
    #Nemá oprávnění/nebyl nalezen uživatel
    @unban.error
    async def unban_error(self, ctx, error): 
        if isinstance(error, commands.MemberNotFound): #nebyl nalezen uživatel k unbanu
                        await ctx.send("No user found")
        elif isinstance(error, commands.BotMissingPermissions): #bot nemá oprávnění
                        await ctx.send("The bot does not have permission to ban users to use this command.")
        elif isinstance(error,commands.MissingPermissions): #uživatel nemá oprávnění
                        await ctx.send("You do not have permission to ban users from using this command")

    #warn
    @commands.command(aliases=['Warn'], help="Warns the user.")
    @commands.has_permissions(administrator=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        if not reason:
            return await ctx.send("You must provide a reason.")
        
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

        await ctx.send(f"{member.mention} was warned. Reason: {reason}")

    #warnings
    @commands.command(aliases=['Warnings'], help="Displays a warning to the user.")
    @commands.has_permissions(administrator=True)
    async def warnings(self, ctx, member: discord.Member):
        guild_id = str(ctx.guild.id)
        member_id = str(member.id)

        if guild_id not in self.warnings or member_id not in self.warnings[guild_id]:
            return await ctx.send(f"{member.mention} has no warnings.")

        embed = discord.Embed(title=f"User warning {member.name}", color=discord.Color.red())
        for idx, warning in enumerate(self.warnings[guild_id][member_id], 1):
            admin = ctx.guild.get_member(warning["admin"])
            admin_name = admin.name if admin else "Unknow"
            embed.add_field(
                name=f"Warnings {idx}",
                value=f"Reason: {warning['reason']}\nAdmin: {admin_name}",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderace(bot))
