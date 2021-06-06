Usage
=====

Example usage of the library. Please see the  :ref:`reference` for details.

.. code-example
.. code-block:: python

    import pyyaledoorman
    import aiohttp
    import asyncio
    import pyyaledoorman


    async def main():
        async with aiohttp.ClientSession() as session:
            client = pyyaledoorman.Client(
                "username",
                "password",
                session=session,
            )
            assert await client.login() == True
            await client.update_devices()

            for device in client.devices:
                print(device.name)
                await device.disable_autolock()
                await device.unlock(pincode="123456")


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
.. code-example-end