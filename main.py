import random
import threading 
#import asyncio
import datetime
import os

import discord
from discord.ext import commands
from discord.ext import tasks

ESCAPE_CHAR= '!'

class Character:
    def __init__(self, name, gold):
        self.valid=True
        self.name = name
        self.gold=gold
        self.position = (0,0)

class Submarine:
    def __init__(self):
        self.hull = 100
        self.fuel = 100
        self.weapons = 100
        self.position = (0,0)

class Mission:
    def __init__(self, id, duration, description, reason):
        self.id = id
        self.description = description
        self.reason = reason
        self.assigned_character = None
        self.start_time = 0
        self.duration_seconds = duration
        self.valid = False

class World:
    MISSION_DURATION = 30
    MAXIMUM_ONGOING_MISSIONS = 3
    def __init__(self):
        self.submarine = Submarine()
        self.characters = {}
        self.mission_id = 0
        self.bot = None
        self.missionboard = [Mission(0, self.MISSION_DURATION, "Engine Failure", "something got lodged in the intake"),
                             Mission(1, self.MISSION_DURATION, "Hull Damage", "we accidently brushed against a reef"),
                             Mission(2, self.MISSION_DURATION, "Electrical Malfunction", "ghosts are causing a ruckus"),
                             Mission(3, self.MISSION_DURATION, "Plumbing Disaster", "someone took a big dump and clogged the pipes"),
                             Mission(4, self.MISSION_DURATION, "Navigation Error", "there was an accidental conversion to metric system"),
                             Mission(5, self.MISSION_DURATION, "Stray Neutrino", "a stray neutrino wrecked some electronics"),
                             Mission(6, self.MISSION_DURATION, "Crew Altercation", "some crew got into an argument, and started boxing")]


    def bet(self, src, amt):
        str_result = ""
        gold = self.characters[src].gold
        if amt <= gold:
            outcome = True if random.random() > 0.45 else False
            if outcome == True:
                self.characters[src].gold = self.characters[src].gold + amt
                str_result = src + ' WON ' + str(amt) + ' gold.'
            else:
                self.characters[src].gold = self.characters[src].gold - amt
                str_result = src + ' LOST ' + str(amt) + ' gold.'
        else:
            str_result = src + " doesn't have enough gold."
        return str_result

    def give(self, src, dst, amt):
        str_result = ""
        src_gold = self.characters[src].gold
        if dst in self.characters:
            dst_gold = self.characters[dst].gold
            if src_gold >= amt:
                if src != dst:
                    self.characters[dst].gold = dst_gold + amt
                    self.characters[src].gold = src_gold - amt
                    str_result = src + " gave " + str(amt) + " gold to " + dst + "."
                else:
                    str_result = src + ", you can't give to yourself."
            else:
                str_result = src + ", you don't have enough gold."
        else:
            str_result = "Give to who?" 
        return str_result

class SubmarinerContext:
    def __init__(self):
        self.world = World()

class SubmarinerBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.submarinerContext = SubmarinerContext()        
        self.submarine_check.start()
        self.character_check.start()


    @tasks.loop(seconds=10)
    async def submarine_check(self):
        if not self.is_closed():
            num_valid = 0
            for m in self.submarinerContext.world.missionboard:
                if m.valid == True:
                    num_valid = num_valid + 1
            
            next_problem_index = 0
            if num_valid < World.MAXIMUM_ONGOING_MISSIONS:
                mission_board = self.submarinerContext.world.missionboard # load 1
                next_problem_index = random.randint(0, len(mission_board)-1)

                mission = mission_board[next_problem_index] #load 2
                if mission.valid == False:
                    mission.valid = True
                    mission.assigned_character = None
                    mission_board[next_problem_index] = mission #store 2
                    self.submarinerContext.world.missionboard = mission_board # store 1
                    num_valid = num_valid + 1                        
                    channel = self.get_channel(925887494128537692)  # channel ID goes here
                    await channel.send(f"```Uh oh, {mission.reason}.\nPlease run !diagnostics, and !repair the problem.```")                        
                    #break
                else:
                    print("already taken")
                #await asyncio.sleep(30)  # task runs every 30 seconds
    
    @tasks.loop(seconds=1)
    async def character_check(self):
        #pass
        if not self.is_closed():
            for m in range(0,len(self.submarinerContext.world.missionboard)):
                mission = self.submarinerContext.world.missionboard[m] #load
                if mission.valid == True:
                    if mission.assigned_character != None:
                        who = mission.assigned_character
                        if (datetime.datetime.now() - mission.start_time).total_seconds() > mission.duration_seconds:
                            mission.assigned_character = None
                            mission.valid = False
                            channel = self.get_channel(925887494128537692)  # channel ID goes here
                            await channel.send(f"`{who} completed their assignment.`")
                self.submarinerContext.world.missionboard[m] = mission #store
    
    @submarine_check.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in

    @character_check.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in+

bot = SubmarinerBot(command_prefix=ESCAPE_CHAR)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

@bot.command()
async def create(ctx):
    myname = ctx.message.author.name.lower()
    ctx.bot.submarinerContext.world.characters[myname] = Character(myname, 1000)
    await ctx.message.channel.send(f"`{myname} is born.`")

@bot.command()
async def money(ctx):
    myname = ctx.message.author.name.lower()
    gold = ctx.bot.submarinerContext.world.characters[myname].gold
    await ctx.message.channel.send(f"{myname} has {str(gold)} gold.`")    

@bot.command()
async def give(ctx):
    myname = ctx.message.author.name.lower()
    pieces = ctx.message.content.split(' ')
    if len(pieces) == 3:                    
        str_result = ctx.bot.submarinerContext.world.give(myname, str(pieces[2]), int(pieces[1]))
        await ctx.message.channel.send(str_result)
    else:
        await ctx.message.channel.send(f"'{myname}, what did you say?'")

@bot.command()
async def bet(ctx):
    myname = ctx.message.author.name.lower()
    pieces = ctx.message.content.split(' ')
    if len(pieces) == 2:
        str_result = ctx.bot.submarinerContext.world.bet(myname, int(pieces[1]))
        await ctx.message.channel.send(str_result)
    else:
        await ctx.message.channel.send(f"'{myname}, what did you say?'")

@bot.command()
async def diagnostics(ctx):
    board_str = ""
    job_id = 1
    for mission in ctx.bot.submarinerContext.world.missionboard:
        if mission.valid == False:
            continue
        board_str += f"{job_id}) {mission.description}\n"
        if mission.assigned_character != None:
            remaining_time = mission.duration_seconds - (datetime.datetime.now() - mission.start_time).total_seconds()
            board_str += f"\t* {mission.assigned_character} is assigned ({int(remaining_time)} seconds remaining)\n"
        job_id = job_id + 1
    if board_str != "":
        board_str = f"```{board_str}```"
        await ctx.message.channel.send(board_str)

@bot.command()
async def repair(ctx):
    myname = ctx.message.author.name.lower()
    pieces = ctx.message.content.split(' ')
    if len(pieces) == 2:
        job_id = int(pieces[1])
        job_index = 0
        board_str = ""
        #if ctx.bot.submarinerContext.world.characters[myname].busy == False:
        for m in range(0,len(ctx.bot.submarinerContext.world.missionboard)):
            mission = ctx.bot.submarinerContext.world.missionboard[m] #load
            if mission.valid == True:
                if mission.assigned_character == myname:
                    await ctx.message.channel.send("You are already assigned to a job.")
                    break
                if job_id == job_index+1:
                    #this is the selected mission
                    mission.assigned_character = myname
                    mission.start_time = datetime.datetime.now()
                    ctx.bot.submarinerContext.world.missionboard[m] = mission # store
                    await ctx.message.channel.send(f"`You are now assigned to '{mission.description}'`")
                    break
                job_index = job_index + 1
        #else:
        #    await ctx.message.channel.send("You are already assigned to a job.")
    else:
        await ctx.message.channel.send(f"'{myname}, what did you say?'")
@bot.command()
async def radar(ctx):
    pass

@bot.command()
async def ride(ctx):
    await ctx.message.channel.send("You are such a joker")


if "DISCORD_BOT_TOKEN" in os.environ:
    token = os.environ["DISCORD_BOT_TOKEN"]
    bot.run(token)