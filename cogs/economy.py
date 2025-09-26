import discord
from discord.ext import commands
import json
import random
import asyncio
from discord.ext.commands import CommandOnCooldown
from db_helpers import db_helpers


class Economy(commands.Cog, name="Economy"):
    def __init__(self, bot):
        self.bot = bot

    # Example shop
    mainshop = [
        {"name": "Watches", "price": 100, "description": "Just watches"},
        {"name": "Notebook", "price": 1000, "description": "Notebook, what else do you want to know?"},
        {"name": "PC", "price": 10000, "description": "PC for playing games"}
    ]

    # Helper function for getting bank data
    async def get_bank_data(self):
        return await db_helpers.get_bank_data()

    # Helper function for creating accounts
    async def open_account(self, user):
        return await db_helpers.open_account(user)

    # Helper function for updating bank balances
    async def update_bank(self, user, change=0, mode="wallet"):
        return await db_helpers.update_bank(user, change, mode)

    # Helper function for buying items
    async def buy_this(self, user, item_name, amount):
        item_name = item_name.lower()
        name_ = None
        price = 0
        for item in self.mainshop:
            name = item["name"].lower()
            if name == item_name:
                name_ = name
                price = item["price"]
                break
        if name_ is None:
            return [False, 1]
        
        cost = price * amount
        bal = await self.update_bank(user)
        if bal[0] < cost:
            return [False, 2]
        
        # Use database helper to buy item
        success = await db_helpers.buy_item(user, item_name, amount, price)
        return [success, "Worked" if success else "Failed"]


    #Balance
    @commands.command(aliases=['bal'], help="It will show the status of your account")
    async def balance(self, ctx, member: discord.Member = None):
        await self.open_account(ctx.author if member is None else member)
        user = ctx.author if member is None else member
        users = await self.get_bank_data()
        wallet_amt = users[str(user.id)]["wallet"]
        bank_amt = users[str(user.id)]["bank"]
        em = discord.Embed(title=f"{user.name}'s balance", color=discord.Color.red())
        em.add_field(name="Wallet", value=wallet_amt)
        em.add_field(name="Bank", value=bank_amt)
        await ctx.send(embed=em)

    #Begging
    @commands.command(aliases=['BEG', 'Beg'], help="You will beg for money")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def beg(self, ctx):
        try:
            await self.open_account(ctx.author)
            user = ctx.author
            earnings = random.randrange(101)
            await ctx.send(f"Somebody give you {earnings} money!!")
            await self.update_bank(user, earnings, "wallet")
        except CommandOnCooldown as e:
            remaining_time = round(e.retry_after)  # Get the remaining time in seconds
            minutes, seconds = divmod(remaining_time, 60)
            await ctx.send(f"You still must to wait {minutes} minute and {seconds} seconds before you can beg again.")

    #withdraw
    @commands.command(aliases=['with'], help="You withdraw a certain amount of money from the bank")
    async def withdraw(self, ctx, amount: int = None):
        await self.open_account(ctx.author)
        if amount is None:
            await ctx.send("Please enter the quantity")
            return
        bal = await self.update_bank(ctx.author)
        if amount > bal[1]:
            await ctx.send("You don't have that much money in the bank")
            return
        if amount < 0:
            await ctx.send("The value cannot be negative")
            return
        await self.update_bank(ctx.author, amount)
        await self.update_bank(ctx.author, -amount, "bank")
        await ctx.send(f"You have withdrawn {amount} of money")

    # Give command
    @commands.command(aliases=['Give', 'GIVE'], help="You give someone a certain amount of money")
    async def give(self, ctx, member: discord.Member, amount: int = None):
        await self.open_account(ctx.author)
        await self.open_account(member)
        if amount is None:
            await ctx.send("Please enter the quantity")
            return
        bal = await self.update_bank(ctx.author)
        if amount > bal[1]:
            await ctx.send("You don't have that much money")
            return
        if amount < 0:
            await ctx.send("The value cannot be negative")
            return
        await self.update_bank(ctx.author, -amount, "bank")
        await self.update_bank(member, amount, "bank")
        await ctx.send(f"You give {amount} money")

    # Rob command
    @commands.command(aliases=['ROB', 'Rob'], help="Try to rob someone")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def rob(self, ctx, member: discord.Member):
        try:
            await self.open_account(ctx.author)
            await self.open_account(member)
            bal = await self.update_bank(member)
            if bal[0] < 100:
                await ctx.send("It's not worth it")
                return
            earnings = random.randrange(0, bal[0])
            await self.update_bank(ctx.author, earnings)
            await self.update_bank(member, -earnings)
            await ctx.send(f"You stole and got {earnings} of money")
        except CommandOnCooldown as e:
            remaining_time = round(e.retry_after)  # Získá zbývající čas v sekundách
            minutes, seconds = divmod(remaining_time, 60)
            await ctx.send(f"You still have to wait {minutes} minutes and {seconds} seconds before you can steal again.")
    
    # Deposit command
    @commands.command(aliases=['dep'], help="Deposit a certain amount of money in the bank")
    async def deposit(self, ctx, amount: int = None):
        await self.open_account(ctx.author)
        if amount is None:
            await ctx.send("Please enter the quantity")
            return
        bal = await self.update_bank(ctx.author)
        if amount > bal[0]:
            await ctx.send("You don't have that much money")
            return
        if amount < 0:
            await ctx.send("The value cannot be negative")
            return
        await self.update_bank(ctx.author, -amount)
        await self.update_bank(ctx.author, amount, "bank")
        await ctx.send(f"You have deposited {amount} of money")

    # Slots command
    @commands.command(aliases=['Slots'], help="Bet a certain amount of money on slots")
    async def slots(self, ctx, amount: int = None):
        await self.open_account(ctx.author)
        if amount is None:
            await ctx.send("Please enter the quantity")
            return
        bal = await self.update_bank(ctx.author)
        if amount > bal[0]:
            await ctx.send("You don't have that much money")
            return
        if amount <= 0:
            await ctx.send("The value cannot be negative")
            return

        # Slot machine emojis (reduced for better odds)
        emojis = ["🍒", "🍋", "🍊", "💎"]
        
        # Create initial embed
        embed = discord.Embed(title="🎰 Slot Machine", color=0xFFD700)
        embed.add_field(name="Bet Amount", value=f"💰 {amount:,} coins", inline=False)
        embed.add_field(name="Rolling...", value="🎰 | 🎰 | 🎰", inline=False)
        embed.set_footer(text=f"Good luck, {ctx.author.display_name}!")
        
        message = await ctx.send(embed=embed)
        
        # Simulate rolling animation
        for i in range(8):  # 8 rolls for animation
            rolling_result = [random.choice(emojis) for _ in range(3)]
            embed.set_field_at(1, name="Rolling...", value=f"{rolling_result[0]} | {rolling_result[1]} | {rolling_result[2]}", inline=False)
            await message.edit(embed=embed)
            await asyncio.sleep(0.5)
        
        # Final result
        final = [random.choice(emojis) for _ in range(3)]
        
        # Check if won
        if final[0] == final[1] == final[2]:
            winnings = 3 * amount
            await self.update_bank(ctx.author, winnings)
            embed.color = 0x00FF00  # Green for win
            embed.set_field_at(1, name="🎉 JACKPOT! 🎉", value=f"{final[0]} | {final[1]} | {final[2]}", inline=False)
            embed.add_field(name="Result", value=f"🎊 You won **{winnings:,}** coins! (3x multiplier)", inline=False)
        else:
            await self.update_bank(ctx.author, -amount)
            embed.color = 0xFF0000  # Red for loss
            embed.set_field_at(1, name="💥 No Match", value=f"{final[0]} | {final[1]} | {final[2]}", inline=False)
            embed.add_field(name="Result", value=f"😢 You lost **{amount:,}** coins. Better luck next time!", inline=False)
        
        # Show new balance
        new_bal = await self.update_bank(ctx.author)
        embed.add_field(name="New Balance", value=f"💰 {new_bal[0]:,} coins", inline=False)
        
        await message.edit(embed=embed)

    # Shop command
    @commands.command(aliases=['Shop'],help="See what you can buy in the store")
    async def shop(self, ctx):
        em = discord.Embed(title="Shop")
        for item in self.mainshop:
            name = item["name"]
            price = item["price"]
            desc = item["description"]
            em.add_field(name=name, value=f"{price} | {desc}")
        await ctx.send(embed=em)

    # Buy command
    @commands.command(aliases=['Buy'], help="Buy the item from the store")
    async def buy(self, ctx, item: str, amount: int = 1):
        await self.open_account(ctx.author)
        res = await self.buy_this(ctx.author, item, amount)
        if not res[0]:
            if res[1] == 1:
                await ctx.send("We do not have this item")
            elif res[1] == 2:
                await ctx.send(f"You don't have enough money in your wallet to buy {amount} {item}")
        else:
            await ctx.send(f"You bought {amount} {item}")

    # Bag command
    @commands.command(aliases=['Bag'],help="Look what you own")
    async def bag(self, ctx):
        await self.open_account(ctx.author)
        user = ctx.author
        bag = await db_helpers.get_user_bag(user)
        em = discord.Embed(title="Bag")
        for item in bag:
            name = item["item"]
            amount = item["amount"]
            em.add_field(name=name, value=amount)
        await ctx.send(embed=em)

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))