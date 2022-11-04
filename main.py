import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import openai
import sqlite3
from discord import FFmpegPCMAudio
from datetime import datetime
import gtts
from pytube import YouTube
import random
import string

load_dotenv(".env")

con = sqlite3.connect("zdiscorddata.db")

cur = con.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS sentmsg(user, text, date)")

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.all()
client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='*',intents =intents)

openai.api_key = os.getenv("OPENAI_API_KEY")


SongQ = []
OUTPUT_PATH =r"C:\Users\Henrik\Documents\PROGRAMMING Python\discord bot\dbot2\AUDIO"

def getVoiceClient(guildIn):
    voice_client: discord.VoiceClient = discord.utils.get(bot.voice_clients, guild=guildIn)
    return voice_client

def MakeAudioObject(nameSong):
    audio_source = discord.FFmpegPCMAudio(source = fr"{OUTPUT_PATH}\{nameSong}.mp3")
    return (audio_source)

def MakeAudioAndPlayOrQ(nameSong,ctx):
    audio = MakeAudioObject(nameSong)

    if (ctx.voice_client.is_playing()):
        print("is playing")
        SongQ.append(audio)
        return("added to q")
    else:
        print("IS NOT PLAYING")

        getVoiceClient(ctx.guild).play(audio, after=lambda x=None: check_q(ctx,ctx.message.guild.id))

        return(f"now playing")

def check_songs(songs,text):
    print(text)
    print(songs)
    print(len(songs))
    return

def check_q(ctx,id):
    voice = ctx.guild.voice_client
    source = SongQ.pop(0)
    player = voice.play(source)

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    print("Random string of length", length, "is:", result_str)

@bot.event
async def on_ready() -> None:
    print(f"Logged in")

#-----------------------------------
#---------- READ MESSAGES ----------
#-----------------------------------

@bot.event
async def on_message(message: discord.Message) -> None:

    if message.author == bot.user:
        return

    with open ("messages.txt", "a") as f:
        f.write(f"{message.author}   {message.content} \n")

    cur.execute("""INSERT INTO sentmsg(user, text, date) 
           VALUES (\"%s\",\"%s\",\"%s\")""" % (message.author, message.content,datetime.now()))

    con.commit()

    await bot.process_commands(message)

#----------------------------------
#--------- VOICE COMMANDS --------- 
#----------------------------------

@bot.command(pass_context=True)
async def enter(ctx, *args):
    if (ctx.author.voice):
        channel = ctx.message.author.voice.channel
        await channel.connect()
    else:
        await ctx.send(f"couldnt join with command {args}, are you in a voice channel?")

@bot.command(pass_context=True)
async def leave(ctx, *args):

    if (ctx.voice_client):
        await ctx.guild.voice_client.disconnect()
        await ctx.send(f"im gone")    
    else:
        await ctx.send(f"cant kick me if im not in a channel...") 

#Play music----

@bot.command(pass_context=True)
async def talk(ctx, *args):

    if (ctx.voice_client):
        textTalk =  " ".join(args)
        name = get_random_string(8)

        response = openai.Completion.create(
        model="text-davinci-002",
        prompt=f"The following is a conversation between a human and a helpful AI. \n Human : {args}",
        temperature=0.9,
        max_tokens = 64
        )

        resp = (response.choices[0].text)

        resp = resp.replace("GavGhan69 :","")

        embedVar = discord.Embed(title="AI says....", description=resp, color=0x00ff00)
        tts = gtts.gTTS(resp, lang='en', tld='co.za')
        tts.save(fr"{OUTPUT_PATH}\{name}.mp3")
        print("----------------saved!")

        (MakeAudioAndPlayOrQ(name,ctx))
        await ctx.send(embed = embedVar)

@bot.command(pass_context=True)
async def play(ctx, *args):

    check_songs(SongQ,"BEFORE")
    arg = " ".join(args)
    name = arg[-5:]

    voice_client = getVoiceClient(ctx.guild)

    if arg == "":
        if voice_client.is_paused():
                voice_client.resume()

    if arg != "":
        if (ctx.voice_client):

            name = arg[-5:]
            stream = YouTube(arg).streams.filter(only_audio=True)[0]
            stream.download(filename=f"{name}.mp3",output_path = OUTPUT_PATH)
            await ctx.send(MakeAudioAndPlayOrQ(name,ctx))
        else:
            await ctx.send("not in a voice call")
            
        check_songs(SongQ,"AFTER")

@bot.command(pass_context=True)
async def skip(ctx, *args):

    voice_client = getVoiceClient(ctx.guild)

    if (ctx.voice_client):

        check_songs(SongQ,"before skip")
        voice_client.stop()

        try:
            voice_client.play(SongQ[0], after=lambda x=None: check_q(ctx,ctx.message.guild.id))
        except Exception as e:
            print(f"{e} error doesnt wanna go")
            await ctx.send(f"Something went wrong oops, might have skipped a song 😅")

        if len(SongQ) != 1:
            SongQ.pop(0)

        if len(SongQ) == 0:
            print("End of Q!")

        check_songs(SongQ,"after skip")

    else:
        await ctx.send(f"cant skip im not in voice silly")

@bot.command(pass_context=True)
async def pause(ctx, *args):

    voice_client = getVoiceClient(ctx.guild)

    if voice_client.is_playing():
        voice_client.pause()
    else:
        await ctx.send("Cant pause with no audio")


#---------------------------------
#--------- TEXT COMMANDS --------- 
#---------------------------------

@bot.command(pass_context=True)
async def paint(ctx, *args):

    textR =  " ".join(args)
    name = textR[-3:]

    imgresponse = openai.Image.create(
    prompt = textR,
    n=1,
    size="1024x1024"
    )
    image_url = imgresponse['data'][0]['url']

    
    textresponse = openai.Completion.create(
    model="text-davinci-002",
    prompt=f"Create a breathtaking, descriptive title for a painting that is a {textR}",
    temperature=0.9,
    max_tokens = 64
    )
    title = (textresponse.choices[0].text)

    embed = discord.Embed(title=title, description="", color=0x00ff00) #creates embed
    embed.set_image(url=image_url)

    await ctx.send(embed=embed)
    
@bot.command()
async def r(ctx, textt) :

    for row in cur.execute("SELECT * FROM sentmsg"):
        if textt in row[1]:
            await ctx.send(row)

@bot.command()
async def make(ctx, *args):
    embedVar = discord.Embed(title=args[0], description=args[1::], color=0x00ff00)

    await ctx.send(embed = embedVar)

#VERY LAST-------------
bot.run(TOKEN)