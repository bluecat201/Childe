import discord
from discord import app_commands
from discord.ext import commands
import json
import random

class SlashEconomy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Example shop
    mainshop = [
        {"name": "Hodinky", "price": 100, "description": "Prostě hodinky"},
        {"name": "Laptop", "price": 1000, "description": "Laptop, co víc chceš vědět"},
        {"name": "PC", "price": 10000, "description": "Počítač na hraní her"}
    ]

    # Helper function for getting bank data
    async def get_bank_data(self):
        with open("mainbank.json", "r") as f:
            return json.load(f)

    # Helper function for creating accounts
    async def open_account(self, user: discord.User):
        users = await self.get_bank_data()
        if str(user.id) in users:
            return False
        else:
            users[str(user.id)] = {"wallet": 0, "bank": 0, "bag": []}
        with open("mainbank.json", "w") as f:
            json.dump(users, f)
        return True

    # Helper function for updating bank balances
    async def update_bank(self, user: discord.User, change=0, mode="wallet"):
        users = await self.get_bank_data()
        users[str(user.id)][mode] += change
        with open("mainbank.json", "w") as f:
            json.dump(users, f)
        return [users[str(user.id)]["wallet"], users[str(user.id)]["bank"]]

    #Balance
    @app_commands.command(name="balance", description="Ukáže stav tvého účtu")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        user = interaction.user if member is None else member
        await self.open_account(user)
        users = await self.get_bank_data()
        wallet_amt = users[str(user.id)]["wallet"]
        bank_amt = users[str(user.id)]["bank"]

        em = discord.Embed(title=f"{user.name}'s balance", color=discord.Color.red())
        em.add_field(name="Peněženka", value=wallet_amt)
        em.add_field(name="Banka", value=bank_amt)

        await interaction.response.send_message(embed=em)

    #Begging
    @app_commands.command(name="beg", description="Budeš žebrat o peníze")
    @app_commands.checks.cooldown(1, 3600)
    async def beg(self, interaction: discord.Interaction):
        await self.open_account(interaction.user)
        users = await self.get_bank_data()
        earnings = random.randrange(101)
        users[str(interaction.user.id)]["wallet"] += earnings

        with open("mainbank.json", "w") as f:
            json.dump(users, f)

        await interaction.response.send_message(f"Někdo ti dal {earnings} korun!!")

    #Withdraw
    @app_commands.command(name="withdraw", description="Vybereš si určité množství peněz z banky")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        await self.open_account(interaction.user)
        if amount <= 0:
            await interaction.response.send_message("Hodnota musí být kladná", ephemeral=True)
            return
        
        bal = await self.update_bank(interaction.user)
        if amount > bal[1]:
            await interaction.response.send_message("Nemáte tolik peněz v bance", ephemeral=True)
            return
        
        await self.update_bank(interaction.user, amount)
        await self.update_bank(interaction.user, -amount, "bank")
        await interaction.response.send_message(f"Vybral jsi {amount} peněz z banky")

    #Give
    @app_commands.command(name="give", description="Dáš někomu určité množství peněz")
    async def give(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        await self.open_account(interaction.user)
        await self.open_account(member)
        
        if amount <= 0:
            await interaction.response.send_message("Hodnota musí být kladná", ephemeral=True)
            return
        
        bal = await self.update_bank(interaction.user)
        if amount > bal[1]:
            await interaction.response.send_message("Nemáte tolik peněz v bance", ephemeral=True)
            return
        
        await self.update_bank(interaction.user, -amount, "bank")
        await self.update_bank(member, amount, "bank")
        
        await interaction.response.send_message(f"Dal jsi {amount} peněz {member.name}")

    #Rob
    @app_commands.command(name="rob", description="Pokus se někoho okrást")
    @app_commands.checks.cooldown(1, 60)
    async def rob(self, interaction: discord.Interaction, member: discord.Member):
        await self.open_account(interaction.user)
        await self.open_account(member)
        
        bal = await self.update_bank(member)
        if bal[0] < 100:
            await interaction.response.send_message("Nevyplatí se to, osoba nemá dostatek peněz", ephemeral=True)
            return
        
        earnings = random.randrange(0, bal[0])
        await self.update_bank(interaction.user, earnings)
        await self.update_bank(member, -earnings)
        
        await interaction.response.send_message(f"Kradl jsi a získal {earnings} peněz od {member.name}")

    #Deposit
    @app_commands.command(name="deposit", description="Ulož určité množství peněz do banky")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        await self.open_account(interaction.user)
        if amount < 0:
            await interaction.response.send_message("Hodnota nemůže být záporná", ephemeral=True)
            return

        bal = await self.update_bank(interaction.user)
        if amount > bal[0]:
            await interaction.response.send_message("Nemáte tolik peněz", ephemeral=True)
            return

        await self.update_bank(interaction.user, -amount)
        await self.update_bank(interaction.user, amount, "bank")

        await interaction.response.send_message(f"Uložil jsi {amount} peněz do banky")

    # Slots
    @app_commands.command(name="slots", description="Vsadit určité množství peněz na automaty")
    async def slots(self, interaction: discord.Interaction, amount: int):
        await self.open_account(interaction.user)
        
        if amount <= 0:
            await interaction.response.send_message("Hodnota musí být kladná", ephemeral=True)
            return
        
        bal = await self.update_bank(interaction.user)
        if amount > bal[0]:
            await interaction.response.send_message("Nemáte tolik peněz", ephemeral=True)
            return

        final = [random.choice(["X", "O", "Q"]) for _ in range(3)]
        await interaction.response.send_message(f"{final}")
        
        if final[0] == final[1] and final[1] == final[2]:
            await self.update_bank(interaction.user, 2 * amount)
            await interaction.response.send_message("Vyhrál jsi!")
        else:
            await self.update_bank(interaction.user, -amount)
            await interaction.response.send_message("Prohrál jsi.")

    # Shop
    @app_commands.command(name="shop", description="Podívej se co si můžeš koupit v obchodě")
    async def shop(self, interaction: discord.Interaction):
        em = discord.Embed(title="Shop")
        for item in self.mainshop:
            name = item["name"]
            price = item["price"]
            desc = item["description"]
            em.add_field(name=name, value=f"{price} | {desc}")
        await interaction.response.send_message(embed=em)

    # Buy
    @app_commands.command(name="buy", description="Kup si danou věc z obchodu")
    async def buy(self, interaction: discord.Interaction, item: str, amount: int = 1):
        await self.open_account(interaction.user)
        
        res = await self.buy_this(interaction.user, item, amount)
        if not res[0]:
            if res[1] == 1:
                await interaction.response.send_message("Tento předmět nemáme", ephemeral=True)
            elif res[1] == 2:
                await interaction.response.send_message(f"Nemáš dostatek peněz v peněžence aby si koupil {amount} {item}", ephemeral=True)
        else:
            await interaction.response.send_message(f"Koupil jsi {amount} {item}")

    # Bag
    @app_commands.command(name="bag", description="Podívej se co vlastníš")
    async def bag(self, interaction: discord.Interaction):
        await self.open_account(interaction.user)
        user = interaction.user
        users = await self.get_bank_data()
        bag = users.get(str(user.id), {}).get("bag", [])
        
        if not bag:
            await interaction.response.send_message("Máš prázdný batoh.", ephemeral=True)
            return
        
        em = discord.Embed(title="Bag")
        for item in bag:
            name = item["item"]
            amount = item["amount"]
            em.add_field(name=name, value=amount)
        await interaction.response.send_message(embed=em)

async def setup(bot: commands.Bot):
    await bot.add_cog(SlashEconomy(bot))