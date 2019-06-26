import discord
import sqlite3
from discord.ext import commands
from random import randint
from Globals import *

class BadWord(Exception):
    pass

class DM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['DM', 'Dm', 'msg', 'MSG'])
    async def dm(self, ctx):
        if type(ctx.channel) != discord.DMChannel:
            await ctx.send(f'!dm can only be used in a DM with me!')
            await ctx.message.delete()
        else:
            try:
                conn = sqlite3.connect('anon.db')
                c = conn.cursor()
                args = ctx.message.content.split(' ')
                server_id = ctx.message.guild
                user, message = args[1], ' '.join(args[2:])
                words = list(c.execute(f'SELECT words FROM guildFilters WHERE server_id ={server_id}').fetchall())
                for word in words:
                    if message.find(word):
                        raise BadWord

                        

                # checks if user id was supplied
                if user.isdigit():
                    user = discord.utils.get(self.bot.users, id=user)
                else:
                    # nope, user is a string. check if it includes a discriminator for accuracy
                    # remove any @ if there is one..
                    if user[0] == '@':
                        user = user.replace('@', '')
                    if '#' in user:
                        user = discord.utils.get(
                            self.bot.users, name=user[:-5], discriminator=user[-4:])
                    else:
                        # searching for a user just with a name is inaccurate.
                        raise AttributeError

                # check if user has anonymous messaging enabled
                try:
                    user_setting = c.execute(
                        f'SELECT allow_anon_messages FROM userOptions WHERE user_id={user.id}').fetchone()[0]
                except TypeError:
                    user_setting = 0

                if user_setting is 1:
                    receiver = user.id
                    anon_sender = ctx.author.id
                    message_id = 1

                    # generates thread_id and checks if it exists
                    while True:
                        try:
                            thread_id = ''.join((str(randint(0, 9))
                                                 for _ in range(thread_id_maximum)))
                            c.execute(
                                f'SELECT receiver FROM threads WHERE thread_id={thread_id}')
                            # if no rows exist, break out of regen loop
                            thread_data = c.fetchone()[0]
                        except TypeError:
                            break

                    # insert data
                    thread_data = (thread_id, anon_sender, receiver)
                    message_data = (thread_id, message_id,
                                    anon_sender, message)
                    c.execute(
                        'INSERT INTO threads VALUES (null,?,?,?)', thread_data)
                    c.execute(
                        'INSERT INTO messages VALUES (?,?,?,?)', message_data)
                    conn.commit()

                    embed = discord.Embed(
                        title='Anonymous message received!', color=0x267d28,
                        description=f'Reply with `!reply {thread_id} <msg>`')
                    embed.add_field(
                        name='Thread ID:', value=thread_id, inline=True)
                    embed.add_field(
                        name='Message:', value=message, inline=True)
                    await user.send(embed=embed)
                    await ctx.send(f'Sent! :mailbox_with_mail:\nThread ID: {thread_id}')
                else:
                    await ctx.send(f'{user.name} is not accepting anonymous messages at this time.')
            except AttributeError:
                await ctx.send(f'A user with that name could not be found. Names are case specific.')
            except BadWord:
                await ctx.send(f'blah blah your message has bad word: {bad_word}')
            conn.close()


def setup(bot):
    bot.add_cog(DM(bot))
