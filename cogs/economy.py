import discord
from discord.ext import commands
import json
import random
from discord.ext.commands import CommandOnCooldown


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
        with open("mainbank.json", "r") as f:
            return json.load(f)

    # Helper function for creating accounts
    async def open_account(self, user):
        users = await self.get_bank_data()
        if str(user.id) in users:
            return False
        else:
            users[str(user.id)] = {"wallet": 0, "bank": 0, "bag": []}
        with open("mainbank.json", "w") as f:
            json.dump(users, f)
        return True

    # Helper function for updating bank balances
    async def update_bank(self, user, change=0, mode="wallet"):
        users = await self.get_bank_data()
        users[str(user.id)][mode] += change
        with open("mainbank.json", "w") as f:
            json.dump(users, f)
        return [users[str(user.id)]["wallet"], users[str(user.id)]["bank"]]

    # Helper function for buying items
    async def buy_this(self, user, item_name, amount):
        item_name = item_name.lower()
        name_ = None
        for item in self.mainshop:
            name = item["name"].lower()
            if name == item_name:
                name_ = name
                price = item["price"]
                break
        if name_ is None:
            return [False, 1]
        cost = price * amount
        users = await self.get_bank_data()
        bal = await self.update_bank(user)
        if bal[0] < cost:
            return [False, 2]
        try:
            index = 0
            t = None
            for thing in users[str(user.id)]["bag"]:
                n = thing["item"]
                if n == item_name:
                    old_amt = thing["amount"]
                    new_amt = old_amt + amount
                    users[str(user.id)]["bag"][index]["amount"] = new_amt
                    t = 1
                    break
                index += 1
            if t is None:
                obj = {"item": item_name, "amount": amount}
                users[str(user.id)]["bag"].append(obj)
        except KeyError:
            obj = {"item": item_name, "amount": amount}
            users[str(user.id)]["bag"] = [obj]
        with open("mainbank.json", "w") as f:
            json.dump(users, f)
        await self.update_bank(user, -cost, "wallet")
        return [True, "Worked"]


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
            users = await self.get_bank_data()
            user = ctx.author
            earnings = random.randrange(101)
            await ctx.send(f"Somebody give you {earnings} money!!")
            users[str(user.id)]["wallet"] += earnings
            with open("mainbank.json", "w") as f:
                json.dump(users, f)
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
        if amount < 0:
            await ctx.send("The value cannot be negative")
            return
        final = [random.choice(["X", "O", "Q"]) for _ in range(3)]
        await ctx.send(str(final))
        if final[0] == final[1] and final[1] == final[2]:
            await self.update_bank(ctx.author, 3 * amount)
            await ctx.send("You won")
        else:
            await self.update_bank(ctx.author, -amount)
            await ctx.send("You lose")

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
        users = await self.get_bank_data()
        bag = users.get(str(user.id), {}).get("bag", [])
        em = discord.Embed(title="Bag")
        for item in bag:
            name = item["item"]
            amount = item["amount"]
            em.add_field(name=name, value=amount)
        await ctx.send(embed=em)

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))