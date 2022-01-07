import random
import threading 
import math
import datetime
import os

import discord
from discord.ext import commands
from discord.ext import tasks
from discord.ext.commands.context import P

ESCAPE_CHAR= '!'

class Item:
    def __init__(self, id, name, cost):
        self.id = id
        self.name = name
        self.cost = cost
class Location:
    def __init__(self, id , description, exits):
        self.id = id
        self.description = description
        self.exits = exits
        self.cabinet = []

class Character:
    def __init__(self, name, gold):
        self.valid=True
        self.name = name
        self.health = 100
        self.gold=gold
        self.location = 4
        self.inventory = []
class Submarine:
    def __init__(self):
        self.hull = 100
        self.fuel = 100
        self.weapons = 100
        self.position = (0,0)
        self.layout = [Location(0,"Upper Aft Cargo Room",[1]), Location(1,"Upper Mid Room",[0,2,4]), Location(2, "Sonar Room",[1]),
                       Location(3,"Engine Room",[4]), Location(4,"Reactor Room",[1,3,5,7]), Location(5,"Command and Control Room",[4]),
                       Location(6,"Aft Ballast Room",[7]), Location(7,"Airlock Room",[4,6,8]), Location(8, "Fore Ballast Room",[7])]
        """ Submarine Layout
        0 - 1 - 2
            |
        3 - 4 - 5
            |
        6 - 7 - 8
        """
        self.layout[0].cabinet.append(Item(0, "Screw Driver", 100))
        self.layout[0].cabinet.append(Item(1, "Wrench", 100))
        self.layout[0].cabinet.append(Item(2, "Plunger", 100))
        self.layout[0].cabinet.append(Item(3, "Welder", 100))
        self.layout[0].cabinet.append(Item(4, "Logic Analyzer", 100))
        self.layout[0].cabinet.append(Item(5, "Sedative", 100))
        self.layout[0].cabinet.append(Item(6, "Channel Locks", 100))

class Mission:
    def __init__(self, id, duration, description, reason, location, tool):
        self.id = id
        self.description = description
        self.reason = reason
        self.assigned_character = None
        self.start_time = 0
        self.duration_seconds = duration
        self.valid = False
        self.location = location
        self.tool = tool
class World:
    MISSION_DURATION = 30
    MAXIMUM_ONGOING_MISSIONS = 3
    def __init__(self):
        self.submarine = Submarine()
        self.characters = {}
        self.mission_id = 0
        self.bot = None
        self.missionboard = [Mission(0, self.MISSION_DURATION, "Engine Failure", "something got lodged in the intake",3,1),
                             Mission(1, self.MISSION_DURATION, "Hull Damage", "we accidently brushed against a reef",-1,3),
                             Mission(2, self.MISSION_DURATION, "Electrical Malfunction", "ghosts are causing a ruckus",4,0),
                             Mission(3, self.MISSION_DURATION, "Plumbing Disaster", "someone took a big dump and clogged the pipes",1, 6),
                             Mission(4, self.MISSION_DURATION, "Navigation Error", "there was an accidental conversion to metric system",5, 4),
                             Mission(5, self.MISSION_DURATION, "Stray Neutrino", "a stray neutrino wrecked some electronics",5,4),
                             Mission(6, self.MISSION_DURATION, "Crew Altercation", "some crew got into an argument, and started boxing",4, 5)]
        


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

@bot.command()
async def stats(ctx):
    myname = ctx.message.author.name.lower()
    mychar = ctx.bot.submarinerContext.world.characters[myname]
    health =mychar.health
    gold = mychar.gold
    description = ctx.bot.submarinerContext.world.submarine.layout[mychar.location].description
    inventory =""
    for i in mychar.inventory:
        inventory += f"{i.name}\n"
    # if inventory != "":
    #     inventory = f"```{inventory}```"
    await ctx.message.channel.send(f"```Name: {myname}\nHealth: {health}\nLocation: {description}\nGold: {gold}\nInventory: {inventory}```")

@bot.command()
async def look(ctx):
    myname = ctx.message.author.name.lower()
    mychar = ctx.bot.submarinerContext.world.characters[myname]
    myloc = ctx.bot.submarinerContext.world.submarine.layout[mychar.location]


    exits = ""
    for e in myloc.exits:
        exits += f"\t{ctx.bot.submarinerContext.world.submarine.layout[e].id}) {ctx.bot.submarinerContext.world.submarine.layout[e].description}\n"
    str_result = f"You are in the {myloc.description}\n"
    if len(myloc.cabinet) > 0:
        str_result += f"There is a cabinet here\n"
    str_result += f"You can move to:\n{exits}"
    
    await ctx.message.channel.send(str_result)

@bot.command()
async def move(ctx):
    pieces = ctx.message.content.split(' ')
    if len(pieces) == 2:    
        myname = ctx.message.author.name.lower()
        mychar = ctx.bot.submarinerContext.world.characters[myname] #load
        myloc = ctx.bot.submarinerContext.world.submarine.layout[mychar.location]
        if int(pieces[1]) in myloc.exits:
            mychar.location = int(pieces[1])
            ctx.bot.submarinerContext.world.characters[myname] = mychar #store
            destination_room_description = ctx.bot.submarinerContext.world.submarine.layout[mychar.location].description
            await ctx.message.channel.send(f"```You moved to the {destination_room_description}```")

@bot.command()
async def cabinet(ctx):
    myname = ctx.message.author.name.lower()
    mychar = ctx.bot.submarinerContext.world.characters[myname] #load
    str_cabinet = ""
    item_index = 1
    for i in ctx.bot.submarinerContext.world.submarine.layout[mychar.location].cabinet:
        str_cabinet += f"{item_index}) {i.name}\n"
        item_index += 1
    if str_cabinet != "":
        str_cabinet = f"```Items inside the cabinet:\n{str_cabinet}```"
        await ctx.message.channel.send(str_cabinet)
    else:
        await ctx.message.channel.send(f"```There isn't anything in the cabinet```")

@bot.command()
async def get(ctx):
    myname = ctx.message.author.name.lower()
    mychar = ctx.bot.submarinerContext.world.characters[myname] #load
    myloc = ctx.bot.submarinerContext.world.submarine.layout[mychar.location]
    pieces = ctx.message.content.split(' ')
    if len(pieces) == 2:  
        item = myloc.cabinet[int(pieces[1])]
        mychar.inventory.append(item)

@bot.command()
async def equip(ctx):
    pass

if "DISCORD_BOT_TOKEN" in os.environ:
    token = os.environ["DISCORD_BOT_TOKEN"]
    bot.run(token)