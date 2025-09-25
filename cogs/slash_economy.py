import discord
from discord import app_commands
from discord.ext import commands
import json
import random
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
        return await db_helpers.get_all_bank_data()

    async def open_account(self, user: discord.User):
        return await db_helpers.create_bank_account(str(user.id))

    async def update_bank(self, user: discord.User, change=0, mode="wallet"):
        return await db_helpers.update_bank_balance(str(user.id), change, mode)

    #Balance
    @app_commands.command(name="balance", description="It will show the status of your account")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        user = interaction.user if member is None else member
        await self.open_account(user)
        bank_data = await db_helpers.get_bank_data(str(user.id))
        wallet_amt = bank_data["wallet"]
        bank_amt = bank_data["bank"]

        em = discord.Embed(title=f"{user.name}'s balance", color=discord.Color.red())
        em.add_field(name="Wallet", value=wallet_amt)
        em.add_field(name="Bank", value=bank_amt)

        await interaction.response.send_message(embed=em)

    #Begging
    @app_commands.command(name="beg", description="You will beg for money")
    @app_commands.checks.cooldown(1, 3600)
    async def beg(self, interaction: discord.Interaction):
        await self.open_account(interaction.user)
        users = await self.get_bank_data()
        earnings = random.randrange(101)
        users[str(interaction.user.id)]["wallet"] += earnings

        with open("mainbank.json", "w") as f:
            json.dump(users, f)

        await interaction.response.send_message(f"Somebody give you {earnings} money!!")

    #Withdraw
    @app_commands.command(name="withdraw", description="You withdraw a certain amount of money from the bank")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        await self.open_account(interaction.user)
        if amount <= 0:
            await interaction.response.send_message("The value cannot be negative", ephemeral=True)
            return
        
        bal = await self.update_bank(interaction.user)
        if amount > bal[1]:
            await interaction.response.send_message("You don't have that much money in the bank", ephemeral=True)
            return
        
        await self.update_bank(interaction.user, amount)
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
        
        bal = await self.update_bank(interaction.user)
        if amount > bal[1]:
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

        final = [random.choice(["X", "O", "Q"]) for _ in range(3)]
        await interaction.response.send_message(f"{final}")
        
        if final[0] == final[1] and final[1] == final[2]:
            await self.update_bank(interaction.user, 3 * amount)
            await interaction.response.send_message("You won!")
        else:
            await self.update_bank(interaction.user, -amount)
            await interaction.response.send_message("You lose.")

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
        users = await self.get_bank_data()
        bag = users.get(str(user.id), {}).get("bag", [])
        
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
