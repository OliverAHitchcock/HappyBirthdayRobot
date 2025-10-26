import asyncio

async def run_command(command: str) -> str:
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    stdout, stderr = await process.communicate()
    
async def loopy():
    while True:
        print('running...')
        await asyncio.sleep(1)

async def main():
    task = asyncio.create_task(loopy())
    await task

if __name__ == '__main__':
    asyncio.run(main())