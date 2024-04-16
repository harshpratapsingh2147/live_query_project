from groq import Groq
from decouple import config


groq_api_key = config('GROQ_API_KEY')


def groq_api_call(prompt, query, temperature=0, max_tokens=1000):

    client = Groq(api_key=groq_api_key)
    completion = client.chat.completions.create(
        model="llama2-70b-4096",
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": query
            }
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1,
        stream=False,
        stop=None,
    )

    # for chunk in completion:
    #     print(chunk.choices[0].delta.content or "", end="")
    return completion.choices[0].message.content
