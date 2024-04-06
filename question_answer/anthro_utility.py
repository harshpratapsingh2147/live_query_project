import anthropic
from decouple import config

anthropic_api_key = config('ANTHRO_API_KEY')


def anthropic_api_call(prompt, query, temperature=0, max_tokens=1000):

    client = anthropic.Anthropic(
        api_key=anthropic_api_key,
    )

    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=max_tokens,
        temperature=temperature,
        system=prompt,
        messages=[
            {
                "role": "user",
                "content": query
            }
        ]
    )
    return message.content[0].text
