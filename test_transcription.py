import asyncio

from backend.adapters.outbound.gemini_adapter import GeminiAdapter


async def main():
    adapter = GeminiAdapter()

    result = await adapter.transcribe_file("english.wav")

    print("TRANSCRIPCIÓN:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())