import os
import discord
import random
from discord import app_commands
from discord.ui import View

# Monster data
monsters = {
    "Ghazt": {
        "image": "https://media.discordapp.net/attachments/1354151223409901700/1354151962589003786/Untitled421_20250220170540.png",
        "emoji": "<:Ghazt:1354497826985480213>"
    },
    "Grumpyre": {
        "image": "https://media.discordapp.net/attachments/1354151223409901700/1354151963171885227/Untitled422_20250223155434.png",
        "emoji": "<:Grumpyre:1354498036012810365>"
    }
}

# In-memory storage for caught monsters
caught_monsters = {}

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# Commands

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await tree.sync()

# Slash command to configure the channel
@tree.command(name="config-channel", description="Configure where monsters will spawn.")
async def config_channel(interaction: discord.Interaction, channel_id: str):
    # Only allow the specific admin user to configure channel
    if interaction.user.id == 1034541436315652126 or interaction.user.guild_permissions.administrator:
        # Store the channel id in your config (e.g., in a file or database)
        await interaction.response.send_message(f"Monsters will spawn in <#{channel_id}>!")
    else:
        await interaction.response.send_message("You need to be an admin to use this command.")

# Slash command to claim a random monster
@tree.command(name="claim", description="Claim a random monster!")
async def claim_monster(interaction: discord.Interaction):
    monster = random.choice(list(monsters.keys()))
    caught_monsters[interaction.user.id] = caught_monsters.get(interaction.user.id, [])
    caught_monsters[interaction.user.id].append(monster)
    await interaction.response.send_message(f"Congratulations {interaction.user.mention}, you have claimed a {monster}!")

# Slash command to show monster collection
@tree.command(name="monster-completion", description="Check your monster collection.")
async def monster_completion(interaction: discord.Interaction):
    collected = caught_monsters.get(interaction.user.id, [])
    not_collected = [monster for monster in monsters.keys() if monster not in collected]

    embed = discord.Embed(title="Monster Completion", description="Monsters you've collected:", color=discord.Color.green())
    embed.add_field(name="Collected Monsters", value=", ".join(collected) if collected else "None", inline=False)
    embed.add_field(name="Monsters Left to Catch", value=", ".join(not_collected) if not_collected else "None", inline=False)
    await interaction.response.send_message(embed=embed)

# Function to spawn monsters randomly
async def spawn_monster(channel):
    monster_name = random.choice(list(monsters.keys()))
    monster = monsters[monster_name]
    image_url = monster["image"]

    # Send the message with the monster's image and button
    message = await channel.send(
        content=f"A Wild {monster_name} Appeared!",
        embed=discord.Embed(image=image_url),
        view=MonsterCatchButton(monster_name)
    )

    # Wait for 1 minute to see if anyone catches the monster
    await asyncio.sleep(60)
    if message:
        await message.edit(content=f"The {monster_name} has disappeared!")

# Button for catching the monster
class MonsterCatchButton(View):
    def __init__(self, monster_name):
        super().__init__(timeout=60)
        self.monster_name = monster_name

    @discord.ui.button(label="Catch Monster", style=discord.ButtonStyle.green)
    async def catch(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Show a form to input the monster name
        await interaction.response.send_message(f"Please type the correct name of the {self.monster_name} to catch it.")

        def check(msg):
            return msg.author == interaction.user and msg.content.lower() == self.monster_name.lower()

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            await interaction.channel.send(f"{interaction.user} caught the {self.monster_name}!")
            button.disabled = True
            await interaction.message.edit(view=self)
        except asyncio.TimeoutError:
            await interaction.channel.send(f"Too slow! The {self.monster_name} escaped!")

# Spawn monsters every 15-20 minutes in the configured channel
async def spawn_monsters_periodically():
    await bot.wait_until_ready()
    channel_id = "YOUR_CHANNEL_ID"  # Replace with your configured channel
    channel = bot.get_channel(int(channel_id))

    while True:
        await spawn_monster(channel)
        await asyncio.sleep(random.randint(900, 1200))  # Random sleep between 15 and 20 minutes

@bot.event
async def setup_hook():
    bot.loop.create_task(spawn_monsters_periodically())

# Ensure the bot token is retrieved correctly
TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

# Ensure your token is valid and correctly set
bot.run(TOKEN)
