import asyncio
import discord
import logging
from discord import app_commands, Client, Intents, Interaction, ButtonStyle
from discord.ui import View, Button

from datetime import datetime

from config import Config

from db import DB

discord.utils.setup_logging(level=logging.INFO)

class ConfirmationView(View):
    def __init__(self, bid_amount: int):
        super().__init__(timeout=None)

        self.bid_amount = bid_amount

        self.yes_button = Button(label='Yes', style=ButtonStyle.green)
        self.yes_button.callback = self.yes
        self.add_item(self.yes_button)

        self.no_button = Button(label='No', style=ButtonStyle.red)
        self.no_button.callback = self.no
        self.add_item(self.no_button)

    async def yes(self, interaction: Interaction):
        await self.disable_buttons(interaction)

        await interaction.response.defer(thinking=True)

        auction = DB().get_current_auction()
        if auction is None:
            await interaction.followup.send("There is no auction happening right now.")
            return

        DB().make_bid(auction_id=auction.id, user_id=interaction.user.id, amount=self.bid_amount)

        await interaction.followup.send(f"Auction bid confirmed for **${self.bid_amount:,.2f}**.")

    async def no(self, interaction: Interaction):
        await self.disable_buttons(interaction)
        await interaction.response.send_message("Bid cancelled.")

    async def disable_buttons(self, interaction: Interaction):
        self.yes_button.disabled = True
        self.no_button.disabled = True

        await interaction.message.edit(view=self)


class RevokeBidView(View):
    def __init__(self):
        super().__init__()

        self.revoke_button = Button(label='Revoke Bid', style=ButtonStyle.red)
        self.revoke_button.callback = self.revoke_bid
        self.add_item(self.revoke_button)

    async def revoke_bid(self, interaction: Interaction):
        self.revoke_button.disabled = True
        await interaction.message.edit(view=self)

        await interaction.response.defer(thinking=True)

        auction = DB().get_current_auction()
        if auction is None:
            await interaction.followup.send("There is no auction happening right now.")
            return

        bid = DB().get_bid(auction_id=auction.id, user_id=interaction.user.id)
        if bid is None:
            await interaction.followup.send("You do not have a bid in this auction?! Please reach out to Joel#0006, something is broken.")
            return

        if bid.revoked:
            await interaction.followup.send("You have already revoked this bid.")
            return

        DB().revoke_bid(bid_id=bid.id)

        await interaction.followup.send("Your bid has been revoked. You will not be able to place another bid in this auction.")



intents = Intents.default()
intents.message_content = False
intents.presences = True
intents.members = True

client = Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    logging.info(f"Logged in as {client.user} (ID: {client.user.id})")

@tree.command()
@app_commands.describe(amount="Your bid amount (in US Dollars)")
async def bid(interaction: Interaction, amount: int):
    """
    Place a bid for the current private coaching auction.
    """

    auction = DB().get_current_auction()
    if auction is None:
        await interaction.response.send_message("There is no auction happening right now. Please try again later.")
        return

    start_date_ts = int(datetime.combine(auction.start_date, datetime.min.time()).timestamp())
    end_date_ts = int(datetime.combine(auction.end_date, datetime.min.time()).timestamp())

    current_bid = DB().get_bid(auction_id=auction.id, user_id=interaction.user.id)
    if current_bid is not None:
        if current_bid.revoked:
            await interaction.response.send_message("Your bid for this auction was revoked. You cannot place a new bid in this auction.")
            return

        await interaction.response.send_message(f"""
You have already placed a bid in this auction for **${current_bid.amount:,.2f}**.

Bidding will end <t:{end_date_ts}:D>.

You can revoke your bid with the button below.

**NOTE: Once you revoke your bid, you cannot place a new bid in this auction.**
""", view=RevokeBidView())
        return

    confirmation_message = f"""
You are submitting a bid for Woohoojin's Private Coaching Auction.

This auction is open from **<t:{start_date_ts}:D>** until **<t:{end_date_ts}:D>**.

Your bid amount has been marked as: **${amount:,.2f}**.

PLEASE NOTE:

**1. You can only bid ONCE per auction.**
**2. Upon confirmation, you cannot change your bid amount.**
**3. If you win the auction, you will be required to provide proof of funds or a 10% deposit.**

Would you like you confirm your auction bid for **${amount:,.2f}**?
"""
    await interaction.response.send_message(confirmation_message, view=ConfirmationView(bid_amount=amount))


async def main():
    async with client:
        await client.start(Config["Discord"]["Token"])

if __name__ == "__main__":
    asyncio.run(main())
