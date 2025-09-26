import discord
from discord import app_commands
from discord.ext import commands
import json
import random
import asyncio
from db_helpers import db_helpers

class SlashEconomy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Example shop
    mainshop = [
        {"name": "Watches", "price": 100, "description": "Just watches"},
        {"name": "Notebook", "price": 1000, "description": "Notebook, what else do you want to know?"},
        {"name": "PC", "price": 10000, "description": "PC for playing games"}
    ]

    # Helper functions now use database
    async def get_bank_data(self):
        return await db_helpers.get_bank_data()

    async def open_account(self, user: discord.User):
        return await db_helpers.open_account(user)

    async def update_bank(self, user: discord.User, change=0, mode="wallet"):
        return await db_helpers.update_bank(user, change, mode)

    #Balance
    @app_commands.command(name="balance", description="It will show the status of your account")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        user = interaction.user if member is None else member
        await self.open_account(user)
        wallet_amt, bank_amt = await db_helpers.get_user_balance(user)

        em = discord.Embed(title=f"{user.name}'s balance", color=discord.Color.red())
        em.add_field(name="Wallet", value=wallet_amt)
        em.add_field(name="Bank", value=bank_amt)

        await interaction.response.send_message(embed=em)

    #Begging
    @app_commands.command(name="beg", description="You will beg for money")
    @app_commands.checks.cooldown(1, 3600)
    async def beg(self, interaction: discord.Interaction):
        await self.open_account(interaction.user)
        earnings = random.randrange(101)
        await self.update_bank(interaction.user, earnings, "wallet")

        await interaction.response.send_message(f"Somebody give you {earnings} money!!")

    #Withdraw
    @app_commands.command(name="withdraw", description="You withdraw a certain amount of money from the bank")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        await self.open_account(interaction.user)
        if amount <= 0:
            await interaction.response.send_message("The value cannot be negative", ephemeral=True)
            return
        
        wallet_amt, bank_amt = await db_helpers.get_user_balance(interaction.user)
        if amount > bank_amt:
            await interaction.response.send_message("You don't have that much money in the bank", ephemeral=True)
            return
        
        await self.update_bank(interaction.user, amount, "wallet")
        await self.update_bank(interaction.user, -amount, "bank")
        await interaction.response.send_message(f"You have withdrawn {amount} of money")

    #Give
    @app_commands.command(name="give", description="You give someone a certain amount of money")
    async def give(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        await self.open_account(interaction.user)
        await self.open_account(member)
        
        if amount <= 0:
            await interaction.response.send_message("The value cannot be negative", ephemeral=True)
            return
        
        wallet_amt, bank_amt = await db_helpers.get_user_balance(interaction.user)
        if amount > bank_amt:
            await interaction.response.send_message("You don't have that much money", ephemeral=True)
            return
        
        await self.update_bank(interaction.user, -amount, "bank")
        await self.update_bank(member, amount, "bank")
        
        await interaction.response.send_message(f"You give {amount} money to {member.name}")

    #Rob
    @app_commands.command(name="rob", description="Try to rob someone")
    @app_commands.checks.cooldown(1, 60)
    async def rob(self, interaction: discord.Interaction, member: discord.Member):
        await self.open_account(interaction.user)
        await self.open_account(member)
        
        bal = await self.update_bank(member)
        if bal[0] < 100:
            await interaction.response.send_message("It's not worth it", ephemeral=True)
            return
        
        earnings = random.randrange(0, bal[0])
        await self.update_bank(interaction.user, earnings)
        await self.update_bank(member, -earnings)
        
        await interaction.response.send_message(f"You stole and got {earnings} of money")

    #Deposit
    @app_commands.command(name="deposit", description="Deposit a certain amount of money in the bank")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        await self.open_account(interaction.user)
        if amount < 0:
            await interaction.response.send_message("The value cannot be negative", ephemeral=True)
            return

        bal = await self.update_bank(interaction.user)
        if amount > bal[0]:
            await interaction.response.send_message("You don't have that much money", ephemeral=True)
            return

        await self.update_bank(interaction.user, -amount)
        await self.update_bank(interaction.user, amount, "bank")

        await interaction.response.send_message(f"You have deposited {amount} of money")

    # Slots
    @app_commands.command(name="slots", description="Bet a certain amount of money on slots")
    async def slots(self, interaction: discord.Interaction, amount: int):
        await self.open_account(interaction.user)
        
        if amount <= 0:
            await interaction.response.send_message("The value cannot be negative", ephemeral=True)
            return
        
        bal = await self.update_bank(interaction.user)
        if amount > bal[0]:
            await interaction.response.send_message("You don't have that much money", ephemeral=True)
            return

        # Slot machine emojis (reduced for better odds)
        emojis = ["🍒", "🍋", "🍊", "💎"]
        
        # Create initial embed
        embed = discord.Embed(title="🎰 Slot Machine", color=0xFFD700)
        embed.add_field(name="Bet Amount", value=f"💰 {amount:,} coins", inline=False)
        embed.add_field(name="Rolling...", value="🎰 | 🎰 | 🎰", inline=False)
        embed.set_footer(text=f"Good luck, {interaction.user.display_name}!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
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
            await self.update_bank(interaction.user, winnings)
            embed.color = 0x00FF00  # Green for win
            embed.set_field_at(1, name="🎉 JACKPOT! 🎉", value=f"{final[0]} | {final[1]} | {final[2]}", inline=False)
            embed.add_field(name="Result", value=f"🎊 You won **{winnings:,}** coins! (3x multiplier)", inline=False)
        else:
            await self.update_bank(interaction.user, -amount)
            embed.color = 0xFF0000  # Red for loss
            embed.set_field_at(1, name="💥 No Match", value=f"{final[0]} | {final[1]} | {final[2]}", inline=False)
            embed.add_field(name="Result", value=f"😢 You lost **{amount:,}** coins. Better luck next time!", inline=False)
        
        # Show new balance
        new_bal = await self.update_bank(interaction.user)
        embed.add_field(name="New Balance", value=f"💰 {new_bal[0]:,} coins", inline=False)
        
        await message.edit(embed=embed)

    # Shop
    @app_commands.command(name="shop", description="See what you can buy in the store")
    async def shop(self, interaction: discord.Interaction):
        em = discord.Embed(title="Shop")
        for item in self.mainshop:
            name = item["name"]
            price = item["price"]
            desc = item["description"]
            em.add_field(name=name, value=f"{price} | {desc}")
        await interaction.response.send_message(embed=em)

    # Buy
    @app_commands.command(name="buy", description="Buy the item from the store")
    async def buy(self, interaction: discord.Interaction, item: str, amount: int = 1):
        await self.open_account(interaction.user)
        
        res = await self.buy_this(interaction.user, item, amount)
        if not res[0]:
            if res[1] == 1:
                await interaction.response.send_message("We do not have this item", ephemeral=True)
            elif res[1] == 2:
                await interaction.response.send_message(f"You don't have enough money in your wallet to buy {amount} {item}", ephemeral=True)
        else:
            await interaction.response.send_message(f"You bought {amount} {item}")

    # Bag
    @app_commands.command(name="bag", description="Look what you own")
    async def bag(self, interaction: discord.Interaction):
        await self.open_account(interaction.user)
        user = interaction.user
        bag = await db_helpers.get_user_bag(user)
        
        if not bag:
            await interaction.response.send_message("You have empty bag.", ephemeral=True)
            return
        
        em = discord.Embed(title="Bag")
        for item in bag:
            name = item["item"]
            amount = item["amount"]
            em.add_field(name=name, value=amount)
        await interaction.response.send_message(embed=em)

async def setup(bot: commands.Bot):
    await bot.add_cog(SlashEconomy(bot))
