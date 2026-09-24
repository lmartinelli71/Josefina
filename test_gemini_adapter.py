import asyncio

from backend.adapters.outbound.gemini_adapter import GeminiAdapter


async def main():
    adapter = GeminiAdapter()

    result = await adapter.translate_text(
        "Good morning everyone",
        "Spanish",
    )

    print("TRADUCCIÓN:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())