import random
import datetime
import os
import uuid
import asyncio

import discord
from discord.ext import commands
from discord.ext import tasks

ESCAPE_CHAR= '!'

TOOL_NONE          = 0
TOOL_SCREWDRIVER   = 1
TOOL_WRENCH        = 2
TOOL_PLUNGER       = 3
TOOL_WELDER        = 4
TOOL_LOGICANALYZER = 5
TOOL_SEDATIVE      = 6
TOOL_CALCULATOR    = 7

TOOL_COST          = 100

class Item:
    def __init__(self, name, cost):

        self.id = uuid.uuid4()
        self.name = name
        self.cost = cost

gItemDossier = {
        TOOL_SCREWDRIVER :   Item("Screw Driver", TOOL_COST),
        TOOL_WRENCH :        Item("Wrench", TOOL_COST),
        TOOL_PLUNGER :       Item("Plunger", TOOL_COST),
        TOOL_WELDER :        Item("Welder", TOOL_COST),
        TOOL_LOGICANALYZER : Item("Logic Analyzer", TOOL_COST),
        TOOL_SEDATIVE :      Item("Sedative", TOOL_COST),
        TOOL_CALCULATOR :    Item("Calculator", TOOL_COST)
    }



class Container:
    def __init__(self, size, name):
        self.name = name
        self.size = size
        self.items = []

    def look_items(self):
        inv = f"{self.name} Inventory:\n"
        idx = 1
        if len(self.items) == 0:
            inv += f"\tEmpty\n"
        for i in self.items:
            inv += f"\t{idx}) {i.name}\n"
            idx += 1
        return inv

    def find(self, word):
        for i in self.items:
            if word.lower() in i.name.lower():
                return i
        return None

class Room:
    def __init__(self, id , description, exits):
        self.id = id
        self.description = description
        self.exits = exits
        self.cabinet = Container(10, "cabinet")

class Mission:
    def __init__(self, id, location, tool, duration, description, reason):
        self.id = id
        self.description = description
        self.reason = reason
        self.assigned_character = None
        self.start_time = 0
        self.duration_seconds = duration
        self.valid = False
        self.location = location
        self.tool = tool

class Character:
    def __init__(self, name, gold):
        self.valid=True
        self.name = name
        self.health = 100
        self.gold=gold
        self.location = 7
        self.inventory = Container(10, "backpack")
        self.xp = 0
        self.equipped_item = None
        self.hands = Container(2, "hands")

class Submarine:
    def __init__(self):
        self.hull = 100
        self.fuel = 100
        self.weapons = 100
        self.position = (0,0)
        self.rooms = [Room(0,"Empty",[]),       Room(1,"Upper Aft Cargo Room",[2]),  Room(2,"Upper Mid Room",[1,3,7]),  Room(3, "Sonar Room",[2,4]),             Room(4,"Crew Quarters",[3]), 
                      Room(5,"Engine Room",[]), Room(6,"Electrical Room",[4]),       Room(7,"Reactor Room",[2,6,8,12]), Room(8,"Command and Control Room",[7,9]),Room(9,"Weapons Room",[8]), 
                      Room(10,"Empty",[]),      Room(11,"Aft Ballast Room",[12]),    Room(12,"Airlock Room",[7,11,13]), Room(13, "Fore Ballast Room",[12]),      Room(14,"Empty",[]) ]
        """ Submarine rooms
              1  -  2  -  3  -  4
                    |
        5  -  3  -  4  -  6  -  7
                    |
              9  -  10 -  11    
        """
        self.rooms[7].cabinet.items.append(gItemDossier[TOOL_SCREWDRIVER])
        self.rooms[7].cabinet.items.append(gItemDossier[TOOL_WRENCH])
        self.rooms[7].cabinet.items.append(gItemDossier[TOOL_PLUNGER])
        self.rooms[7].cabinet.items.append(gItemDossier[TOOL_WELDER])
        self.rooms[7].cabinet.items.append(gItemDossier[TOOL_LOGICANALYZER])
        self.rooms[7].cabinet.items.append(gItemDossier[TOOL_SEDATIVE])


class World:


    MISSION_DURATION   = 30
    MAXIMUM_ONGOING_MISSIONS = 3
    
    def __init__(self):
        self.submarine = Submarine()
        self.characters = {}
        self.mission_id = 0
        self.bot = None
        self.missionboard = [Mission(0, 3, TOOL_WRENCH, self.MISSION_DURATION, "Engine Failure", "something got lodged in the intake"),
                             Mission(1, -1,TOOL_WELDER, self.MISSION_DURATION, "Hull Damage", "we accidently brushed against a reef"),
                             Mission(2, 6, TOOL_LOGICANALYZER, self.MISSION_DURATION, "Electrical Malfunction", "ghosts are causing a ruckus"),
                             Mission(3, 1, TOOL_PLUNGER, self.MISSION_DURATION, "Plumbing Disaster", "someone took a big dump and clogged the pipes"),
                             Mission(4, 8, TOOL_CALCULATOR, self.MISSION_DURATION, "Navigation Error", "there was an accidental conversion to metric system"),
                             Mission(5, 6, TOOL_SCREWDRIVER, self.MISSION_DURATION, "Stray Neutrino", "a stray neutrino wrecked some electronics"),
                             Mission(6, 4, TOOL_SEDATIVE, self.MISSION_DURATION, "Crew Altercation", "some crew got into an argument, and started throwing punches")]
    
    def find_mission(self, name):
        for i in self.missionboard:
            if name.lower() in i.description.lower():
                return i
        return None

    def bet(self, src, amt):
        str_result = ""
        gold = self.characters[src].gold
        if amt <= gold:
            outcome = True if random.random() > 0.45 else False
            if outcome == True:
                self.characters[src].gold = self.characters[src].gold + amt
                str_result = f"```{src} WON {str(amt)} gold.```"
            else:
                self.characters[src].gold = self.characters[src].gold - amt
                str_result = f"```{src} LOST {str(amt)} gold.```"
        else:
            str_result = f"```{src} doesn't have enough gold.```"
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

    def diagnostics(self):
        board_str = ""
        job_id = 1
        for mission in self.missionboard:
            if mission.valid == False:
                continue
            board_str += f"{job_id}) {mission.description}\n"
            if mission.assigned_character != None:
                remaining_time = mission.duration_seconds - (datetime.datetime.now() - mission.start_time).total_seconds()
                board_str += f"\t* {mission.assigned_character} is assigned ({int(remaining_time)} seconds remaining)\n"
            job_id = job_id + 1
        if board_str != "":
            board_str = f"```{board_str}```"
        return board_str

    def repair(self, src, what):
        result_str = ""
        create_character_if_not_exists(self.characters, src)
        mychar = self.characters[src]
        already_assigned = False
        for m in range(0,len(self.missionboard)):
            if self.missionboard[m].assigned_character == src:
                already_assigned = True
                break;
        if already_assigned == False:
            #for m in range(0,len(self.missionboard)):
            mission = self.find_mission(what)
            if mission != None:
                if mission.valid == True:
                    #this is the selected mission
                    # if mission.tool == mychar.equipped_item and mission.tool != -1:
                    mission.assigned_character = src
                    mission.start_time = datetime.datetime.now()
                    result_str = f"```You are now assigned to '{mission.description}'```"
                    # else:
                    #     result_str = f"```You do not have a {mission.tool} equipped.```"
                else:
                    result_str = "```You didn't specify a valid mission```"
            else:
                result_str = "```You didn't specify a valid mission```"
        else:
            result_str = "```You are already assigned to a mission```"
        return result_str
    
    def look_inventory(self, who):
        inventory =""
        create_character_if_not_exists(self.characters, who)
        mychar = self.characters[who]
        inv = mychar.inventory.look_items()
        result_str = f"```{inv}```"
        return result_str

    def look_cabinet(self, src):
        inventory =""
        create_character_if_not_exists(self.characters, src)
        mychar = self.characters[src]
        myroom = self.submarine.rooms[mychar.location]
        inv = myroom.cabinet.look_items()
        result_str = f"```{inv}```"
        return result_str

    def look_hands(self, who):
        inventory =""
        create_character_if_not_exists(self.characters, who)
        mychar = self.characters[who]
        inv = mychar.hands.look_items()
        result_str = f"```{inv}```"
        return result_str

    def move(self, who, where):
        result_str =""
        create_character_if_not_exists(self.characters, who)
        mychar = self.characters[who]
        myroom = self.submarine.rooms[mychar.location]
        if where in myroom.exits:
            mychar.location = where
            destination_room_description = self.submarine.rooms[mychar.location].description
            result_str = f"```You moved to the {destination_room_description}```"
        else:
            result_str = f"```Move where?```"
        return result_str

    def look_room(self, who):
        str_result =""
        create_character_if_not_exists(self.characters, who)
        mychar = self.characters[who]
        myroom = self.submarine.rooms[mychar.location]
        exits = ""
        for e in myroom.exits:
            exits += f"\t{self.submarine.rooms[e].id}) {self.submarine.rooms[e].description}\n"
        str_result = f"You are in the {myroom.description}\n"
        if len(myroom.cabinet.items) > 0:
            str_result += f"You notice a {myroom.cabinet.name}.\n"
        str_result += f"You can move to:\n{exits}"   
        str_result = f"```{str_result}```" 
        return str_result

    def move_from_cabinet_to_inventory(self,who, what):
        str_result =""
        create_character_if_not_exists(self.characters, who)
        mychar = self.characters[who]
        myroom = self.submarine.rooms[mychar.location]
      
        item = myroom.cabinet.find(what)
        if item != None:
            mychar.inventory.items.append(item)
            myroom.cabinet.items.remove(item)
            str_result = f"```You grabbed a {item.name} from a {myroom.cabinet.name}```"
        else:
            str_result = f"```Get what?```"
        return str_result

    def move_from_inventory_to_hands(self,who, what):
        str_result =""
        create_character_if_not_exists(self.characters, who)
        mychar = self.characters[who]
        myroom = self.submarine.rooms[mychar.location]
      
        item = mychar.inventory.find(what)
        if item != None:
            mychar.hands.items.append(item)
            mychar.inventory.items.remove(item)
            str_result = f"```You wielded a {item.name} from a {mychar.inventory.name}```"
        else:
            str_result = f"```Wield what?```"
        return str_result

    def move_from_hands_to_inventory(self,who, what):
        str_result =""
        create_character_if_not_exists(self.characters, who)
        mychar = self.characters[who]
        myroom = self.submarine.rooms[mychar.location]
      
        item = mychar.hands.find(what)
        if item != None:
            mychar.inventory.items.append(item)
            mychar.hands.items.remove(item)
            str_result = f"```You unwielded a {item.name}```"
        else:
            str_result = f"```Unwield what?```"
        return str_result

    def move_from_inventory_to_cabinet(self, who, what):
        str_result =""
        create_character_if_not_exists(self.characters, who)
        mychar = self.characters[who]
        myroom = self.submarine.rooms[mychar.location]
      
        item = mychar.inventory.find(what)
        if item != None:
            myroom.cabinet.items.append(item)
            mychar.inventory.items.remove(item)
            str_result = f"```You put a {item.name} into a {myroom.cabinet.name}```"
        else:
            str_result = f"```Put what?```"
        return str_result

    def get_sonar_snap(self):
        pass
# ----------------------------------- Bot Interface Begin---------------------
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
                else:
                    print("already taken")

    @tasks.loop(seconds=1)
    async def character_check(self):
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
                            await channel.send(f"`{who} rectified the problem '{mission.description}'.`")
    
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


def create_character_if_not_exists(characters, name):
    print (f"Create {name}?")
    for n in characters:
        if n == name:
            print("Character Exists")
            return True
    characters[name] = Character(name, 1000)
    print("CREATED Character")
    return False

@bot.command()
async def sonar(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    str_result = ""
    #str_result = ctx.bot.submarinerContext.world.get_sonar_snap()
    f = discord.File("C:\\Users\\Daniel\\source\\repos\\DeepWater\\sonar_shot.jpg")
    await ctx.message.channel.send(content=str_result, file=f)

@bot.command()
async def reactor(ctx):
    pass

@bot.command()
async def cargo(ctx):
    pass

@bot.command()
async def engines(ctx):
    pass

@bot.command()
async def weapons(ctx):
    pass


@bot.command()
async def money(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    gold = ctx.bot.submarinerContext.world.characters[myname].gold
    await ctx.message.channel.send(f"```{myname} has {str(gold)} gold.```")    

@bot.command()
async def give(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    pieces = ctx.message.content.split(' ')
    if len(pieces) == 3:                    
        str_result = ctx.bot.submarinerContext.world.give(myname, str(pieces[2]), int(pieces[1]))
        await ctx.message.channel.send(str_result)
    else:
        await ctx.message.channel.send(f"'{myname}, what did you say?'")

@bot.command()
async def bet(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    pieces = ctx.message.content.split(' ')
    if len(pieces) == 2:
        str_result = ctx.bot.submarinerContext.world.bet(myname, int(pieces[1]))
        await ctx.message.channel.send(str_result)
    else:
        await ctx.message.channel.send(f"'{myname}, what did you say?'")

@bot.command()
async def diagnostics(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    str_result = ctx.bot.submarinerContext.world.diagnostics()
    if str_result != "":
        await ctx.message.channel.send(str_result)



@bot.command()
async def repair(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    pieces = ctx.message.content.split(' ')
    if len(pieces) == 2:
        str_result = ctx.bot.submarinerContext.world.repair(myname, pieces[1])
        await ctx.message.channel.send(str_result)
    else:
        await ctx.message.channel.send(f"'{myname}, what did you say?'")  


@bot.command()
async def inventory(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    str_result = ctx.bot.submarinerContext.world.look_inventory(myname)
    if str_result != "":
        await ctx.message.channel.send(str_result)

@bot.command()
async def stats(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    mychar = ctx.bot.submarinerContext.world.characters[myname]
    myroom = ctx.bot.submarinerContext.world.submarine.rooms[mychar.location]    
    await ctx.message.channel.send(f"```Name: {myname}\nHealth: {mychar.health}\nLocation: {myroom.description}\nGold: {mychar.gold}```")

@bot.command()
async def look(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    str_result = ctx.bot.submarinerContext.world.look_room(myname)
    if str_result != "":
        await ctx.message.channel.send(str_result)

@bot.command()
async def move(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    pieces = ctx.message.content.split(' ')
    if len(pieces) == 2:
        str_result = ctx.bot.submarinerContext.world.move(myname, int(pieces[1]))
        await ctx.message.channel.send(str_result)
        await look(ctx)
    else:
        await ctx.message.channel.send(f"'{myname}, what did you say?'")


@bot.command()
async def cabinet(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    str_result = ctx.bot.submarinerContext.world.look_cabinet(myname)
    if str_result != "":
        await ctx.message.channel.send(str_result)

def get_item_from_cabinet(room, item_index):
    if len(room.cabinet) >= item_index:
        if item_index >= 0:
            item = room.cabinet[item_index]
            return item
    return None

@bot.command()
async def get(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    str_result = ""
    pieces = ctx.message.content.split(' ')    
    if len(pieces) >= 2:
         str_result = ctx.bot.submarinerContext.world.move_from_cabinet_to_inventory(myname, pieces[1])
    await ctx.message.channel.send(str_result)

@bot.command()
async def put(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    str_result = ""
    pieces = ctx.message.content.split(' ')    
    if len(pieces) >= 2:
         str_result = ctx.bot.submarinerContext.world.move_from_inventory_to_cabinet(myname, pieces[1])
    await ctx.message.channel.send(str_result)

@bot.command()
async def equipped(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    str_result = ctx.bot.submarinerContext.world.look_hands(myname)
    if str_result != "":
        await ctx.message.channel.send(str_result)

@bot.command()
async def equip(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    str_result = ""
    pieces = ctx.message.content.split(' ')    
    if len(pieces) >= 2:
         str_result = ctx.bot.submarinerContext.world.move_from_inventory_to_hands(myname, pieces[1])
    else:
        str_result = f"```equip what?```"
    await ctx.message.channel.send(str_result)


@bot.command()
async def unequip(ctx):
    myname = ctx.message.author.name.lower()
    create_character_if_not_exists(ctx.bot.submarinerContext.world.characters, myname)
    str_result = ""
    pieces = ctx.message.content.split(' ')    
    if len(pieces) >= 2:
        str_result = ctx.bot.submarinerContext.world.move_from_hands_to_inventory(myname, pieces[1])
    else:
        str_result = f"```Unequip what?```"
    await ctx.message.channel.send(str_result)


if "DISCORD_BOT_TOKEN" in os.environ:
    token = os.environ["DISCORD_BOT_TOKEN"]
    bot.run(token)