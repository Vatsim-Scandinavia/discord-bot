# messages.py

async def get_description(bot, ctx):
    """Get the description of the event from a message."""
    try:
        await ctx.send('Staffing message? **FYI this command expires in 5 minutes**')
        message = await bot.wait_for('message', timeout=300, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

        if len(message.content) < 1:
            await ctx.send('Setup cancelled. No message was provided.')
            raise ValueError

        return message.content
    except Exception as e:
        await ctx.send(f'Error getting the Staffing message - {e}')
        raise e

async def get_interval(bot, ctx):
    """Get the week interval of the event."""
    try:
        await ctx.send('Week interval? **FYI this command expires in 5 minutes**')
        message = await bot.wait_for('message', timeout=300, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

        if len(message.content) < 1:
            await ctx.send('Setup cancelled. No message was provided.')
            raise ValueError

        if int(message.content) not in range(1, 5):
            await ctx.send('The interval must be between 1 to 4')
            raise ValueError

        return message.content
    except Exception as e:
        await ctx.send(f'Error getting the Staffing message - {e}')
        raise e

async def get_restriction(bot, ctx):
    """Get the booking restriction of the event."""
    try:
        await ctx.send('Should the event have booking restriction? Allowed ansers: `Yes` or `No` **FYI this command expires in 5 minutes**')
        message = await bot.wait_for('message', timeout=300, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

        if len(message.content) < 1:
            await ctx.send('Setup cancelled. No message was provided.')
            raise ValueError

        if 'yes' in message.content.lower() or 'no' in message.content.lower():
            return message.content.lower()
        else:
            await ctx.send('Only the options `Yes` or `No` is available')
            raise ValueError
            
    except Exception as e:
        await ctx.send(f'Error getting the Staffing message - {e}')
        raise e

async def setup_section(bot, ctx, num: int):
    """Get the title for positions of the event."""
    try:
        await ctx.send(f'Section title nr. {num}? **FYI this command expires in 1 minute**')
        message = await bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

        if len(message.content) < 1:
            await ctx.send('Setup cancelled. No message was provided.')
            raise ValueError

        return message.content

    except Exception as e:
        await ctx.send(f'Error getting the third section title - {e}')
        raise e

async def get_howmanypositions(bot, ctx, type):
    """Get how many positions of the event."""
    try:
        await ctx.send(f'How many {type} positions? **FYI this command expires in 1 minute**')
        message = await bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

        if len(message.content) < 1:
            await ctx.send('Setup cancelled. No message was provided.')
            raise ValueError

        return message.content
    except Exception as e:
        await ctx.send(f'Error getting amount of positions - {e}')
        raise e

async def section_type(bot, ctx):
    """Get what type of section to update."""
    try:
        await ctx.send(f'Which section would you like to update?**FYI this command expires in 1 minute** \nAvailable sections is: `1, 2 or 3`')
        message = await bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

        if len(message.content) < 1:
            await ctx.send('Setup cancelled. No message was provided.')
            raise ValueError

        if int(message.content) not in range(1, 4):
            await ctx.send('The section must be between 1 to 3')
            raise ValueError

        return message.content

    except Exception as e:
        await ctx.send(f'Error getting the section title - {e}')
        raise e

async def get_start_or_end_time(bot, ctx, time):
    """Get the start or end time."""
    try:
        await ctx.send(f'Does this position have a specified {time}? If yes, then insert below (format: `HH:MM`), otherwise type `No`! **FYI this command expires in 1 minute**')

        message = await bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

        if len(message.content) < 1:
            await ctx.send('Setup cancelled. No message was provided.')
            raise ValueError       

        if 'no' in message.content.lower():
            return None

        return message.content
    
    except Exception as e:
        await ctx.send(f'Error getting the {time} - {e}')
        raise e

async def get_local_booking(bot, ctx):
    try:
        await ctx.send(f'Is this positions a local position? Allowed ansers: `Yes` or `No` **FYI this command expires in 1 minutes**')

        message = await bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

        if 'yes' in message.content.lower() or 'no' in message.content.lower():
            return True if message.content.lower() == 'yes' else False
        else:
            await ctx.send('Only the options `Yes` or `No` is available')
            raise ValueError
            
    except Exception as e:
        await ctx.send(f'Error getting the local booking option - {e}')
        raise e

async def get_confirmation(bot, ctx, title):
    try:
        await ctx.send(f'To confirm you want to delete staffing {title} type `{title}` in the chat. If you want to cancel the deletion type `CANCEL` in the chat. **FYI this command expires in 1 minute**')
        message = await bot.wait_for('message', timeout=60, check=lambda message: message.author == ctx.author and ctx.channel == message.channel)

        if len(message.content) < 1:
            await ctx.send('Deletion cancelled. No message was provided.')
            raise ValueError

        return message.content
    except Exception as e:
        await ctx.send(f'Error getting message - {e}')
