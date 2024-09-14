import asyncio
from discord.errors import HTTPException


class Error:
    def __init__(self) -> None:
        pass

    async def crosspost(message, retries=3):
        """
        Safely crossposts a message, with rate limit handling.
        :param message: The discord message to crosspost.
        :param retries: Number of retries allowed in case of rate limiting.
        """
        for attempt in range(retries):
            try:
                # Try publishing the message
                await message.publish()
                return # Exit when the message has successfully been published
            
            except HTTPException as e:
                if e.status == 429:
                    retry_after = e.retry_after if hasattr(e, 'retry_after') else 500 # Default to 500 seconds if not provided
                    print(f'Rate limit hit! Retrying in {retry_after:.2f} seconds...', flush=True)
                    await asyncio.sleep(retry_after) # Wait for the rate limit to reset

                else:
                    #If another HTTP Exception is thrown reraise it
                    raise

            except Exception as e:
                print(f"An Error occurred while trying to publish a message: {e}", flush=True)
                break
        
        print(f"Failed to publish message after {retries} attempts", flush=True)
