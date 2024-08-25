import discord
from discord import app_commands
import google.generativeai as genai
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT')

mode = False
channelid = None

def chat_loop():
    genai.configure(api_key=GOOGLE_API_KEY)

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 0,
        "max_output_tokens": 8192,
    }

    safety_settings = [
        {
            "category": "HARM_CATEGORY_DANGEROUS",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        },
    ]

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",
        safety_settings=safety_settings,
        generation_config=generation_config,
        system_instruction=SYSTEM_PROMPT,
    )

    convo = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    "hello ",
                ],
            },
            {
                "role": "model",
                "parts": [
                    "hi \n",
                ],
            }
        ]
    )

    return convo

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
genai_model = chat_loop()

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')

@client.tree.command(description="starts listing to every single message in the chat")
async def on(interaction: discord.Interaction):
    global mode, channelid
    mode = True
    channelid = interaction.channel_id
    await interaction.response.send_message("```listening on autopilot```")
    await interaction.followup.send(f"```for this channel ID: {channelid}```")

@client.tree.command(description="turns off auto listener")
async def off(interaction: discord.Interaction):
    global mode
    mode = False
    await interaction.response.send_message("```exit```")
    await interaction.followup.send("listening on pings now")

@client.event
async def on_message(message, convo=genai_model):
    global mode, channelid
    if message.author == client.user:
        return

    if mode and message.channel.id == channelid:
        user_input = message.content.strip()
        user_name = message.author.nick or message.author.name

        async with message.channel.typing():
            convo.send_message(f"{user_name}: {user_input}")
            await asyncio.sleep(2)
            model_response = convo.last.text
            await message.channel.send(model_response)

    if not mode and message.content.startswith(f"<@{client.user.id}>"):
        user_input = message.content.strip()
        user_name = message.author.nick or message.author.name

        async with message.channel.typing():
            convo.send_message(f"{user_name}: {user_input}")
            await asyncio.sleep(1.5)
            model_response = convo.last.text
            await message.channel.send(model_response)

client.run(DISCORD_TOKEN)
