from timeit import timeit
from openai import AsyncClient, AsyncStream
from dotenv import load_dotenv
import os
import asyncio

from prompt_gen import Format, Model, Persona, PromptGenerator

load_dotenv("../.env")

client = AsyncClient(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


async def run_prompt():
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "What is the capital of the United States?"}
        ],
    )
    return response.choices[0].message.content


async def main():
    prompt = PromptGenerator(
        "What is the r-squared value in an linear regression model?",
        model=Model.GPT_35_TURBO,
        persona=Persona.EXPERT,
        format=Format.NO_FORMAT,
        stream=False,
    )

    answer = await prompt.execute_prompt(client)
    if isinstance(answer, AsyncStream):
        async for response in answer:
            print(response.choices[0].delta.content)
    else:
        print(answer.content)


def run():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()


print(timeit(run, number=1))
