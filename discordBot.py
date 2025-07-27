import discord
from discord.ext import commands
from discord import app_commands
from discord import PermissionOverwrite
from config import TOKEN, GUILD_ID

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

creators = {}

group = app_commands.Group(name="group", description="Manage your group")

async def checkOwnerOfGroup(interaction,category):
    if creators.get(interaction.user.id) != category.id and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not own this group or lack admin permissions.", ephemeral=True)
        return False
    else:
        return True
    

@group.command(name="delete", description="Delete a group")
@app_commands.describe(
    group_id="Category ID",
)
async def deleteGroup(interaction: discord.Interaction, group_id: str | None = None):
    guild = interaction.guild

    # Find the category by ID
    if group_id is not None and group_id != "":
        category = guild.get_channel(int(group_id))
    else:
        category = interaction.channel.category

    
    if category is None:
        return

    # Check if user owns this category
    if not await checkOwnerOfGroup(interaction, category):
        return

    # Delete category (this deletes all channels inside too)
    for channel in category.channels:
        await channel.delete()
    # then delete the category itself
    await category.delete()



@group.command(name="create", description="Create a group")
@app_commands.describe(
    group_name="Group name",
    user1="User 1",
    user2="User 2",
    user3="User 3",
    user4="User 4",
    user5="User 5",
)
async def createGroup(
    interaction: discord.Interaction,
    group_name: str,
    user1: discord.User = None,
    user2: discord.User = None,
    user3: discord.User = None,
    user4: discord.User = None,
    user5: discord.User = None,
    ):
    if interaction.user.id in creators:
        await interaction.response.send_message("Max group limit reached", ephemeral=True)
        return


    guild = interaction.guild

    #category creation
    category = await guild.create_category_channel(group_name, position=len(guild.categories))
    #set permissions immediately so its hidden
    everyone_permission = discord.PermissionOverwrite()
    everyone_permission.view_channel = False
    await category.set_permissions(category.guild.default_role, overwrite=everyone_permission)

    #add category to the user

    creators[interaction.user.id] = category.id

    #channel creation
    general = await guild.create_text_channel('general', category=category)
    await guild.create_voice_channel('vc', category=category)

    #specific people permissions
    specific_permissions = discord.PermissionOverwrite()
    specific_permissions.view_channel = True

    for user in [interaction.user,user1, user2, user3, user4, user5]:
        if user is not None:
            await general.send(f"<:Join:{1398863403635834981}> {interaction.user.name} added {user.name} to the group.")
            await category.set_permissions(user, overwrite=specific_permissions)







#create a update nest
update = app_commands.Group(name="update", description="Update a group's settings")

#member adding/removing
@update.command(name="remove", description="Remove a member from this group")
@app_commands.describe(
    user="User to be removed",
)
async def removeMember(
    interaction: discord.Interaction,
    user: discord.User,
):
    category = interaction.channel.category
    if not await checkOwnerOfGroup(interaction, category):
        return
    overwrite = category.overwrites_for(user)
    if overwrite.is_empty():
        await interaction.response.send_message(f"{user.name} is not a member of this group.", ephemeral=True)
        return
    await category.set_permissions(user, overwrite=None)
    await interaction.response.send_message("Task completed", ephemeral=True)
    await interaction.channel.send(f"<:Leave:{1398863367388790847}> {interaction.user.name} removed {user.name} from the group.")
    


@update.command(name="add", description="Add a member to this group")
@app_commands.describe(
    user="User to be added",
)
async def addMember(
    interaction: discord.Interaction,
    user: discord.User,
):
    category = interaction.channel.category
    if not await checkOwnerOfGroup(interaction, category):
        return
    permissions = discord.PermissionOverwrite()
    permissions.view_channel=True
    await category.set_permissions(user, overwrite=permissions)
    await interaction.response.send_message("Task completed", ephemeral=True)
    await interaction.channel.send(f"<:Join:{1398863403635834981}> {interaction.user.name} added {user.name} to the group.")
    
    
#group locking/unlocking
@update.command(name="lock", description="Locks the group preventing any messages from being sent")
async def lockGroup(
    interaction = discord.Interaction,
):
    category = interaction.channel.category
    if not await checkOwnerOfGroup(interaction, category):
        await interaction.response.send_message("Lacking permission", ephemeral=True)
        return
    
    permissions = discord.PermissionOverwrite()
    permissions.view_channel=False
    permissions.send_messages=False
    await category.set_permissions(category.guild.default_role, overwrite=permissions)
    await interaction.channel.send(f"<:Lock:{1398873767622475816}> {interaction.user.name} locked this group")

@update.command(name="unlock", description="Unlocks the group allowing messages to be sent")
async def unlockGroup(
    interaction = discord.Interaction,
):
    category = interaction.channel.category
    if not await checkOwnerOfGroup(interaction, category):
        await interaction.response.send_message("Lacking permission", ephemeral=True)
        return
    
    permissions = discord.PermissionOverwrite()
    permissions.view_channel=False
    permissions.send_messages=True
    await category.set_permissions(category.guild.default_role, overwrite=permissions)
    await interaction.channel.send(f"<:Lock:{1398873767622475816}> {interaction.user.name} unlocked this group")


@update.command(name="name", description="Changes the group name")
@app_commands.describe(
    group_name = "Name"
)
async def nameGroup(
    interaction: discord.Interaction,
    group_name: str,
):
    category = interaction.channel.category
    if not await checkOwnerOfGroup(interaction, category):
        return
    await category.edit(name=group_name)
    await interaction.response.send_message(f"Group renamed to `{group_name}`", ephemeral=True)








# add update to the main group
group.add_command(update)

bot.tree.add_command(group, guild=discord.Object(id=GUILD_ID))
@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f'Logged in as {bot.user}!')



#required stuff blabla
@bot.event
async def on_guild_channel_delete(channel):
    if isinstance(channel, discord.CategoryChannel):
        # Check if this category ID is stored in creators
        to_remove = [user_id for user_id, cat_id in creators.items() if cat_id == channel.id]
        for user_id in to_remove:
            del creators[user_id]
            print(f"Removed user {user_id} from creators because category {channel.id} was deleted.")





bot.run(TOKEN)