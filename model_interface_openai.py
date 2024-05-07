import json
from os import path
import os
import openai
from rich.prompt import Prompt
from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv
import os

load_dotenv()

# Init client libraries
console = Console()

# Init vertexai
client = openai.Client(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
messages = []


def print_user(message: str):
    console.print(f"[blue]» User[/blue]: {message}")


def print_model(message: str):
    console.print(f"[green]═ Model[/green]: ", end="")
    console.print(Markdown(message, inline_code_theme="manni"))


def print_system(message: str):
    console.print(f"[red]≡ System[/red]: {message}")


def get_response(prompt: str):
    messages.append({"role": "user", "content": prompt})

    stream = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=messages,
        stream=True,
    )

    chunks = []

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            chunks.append(chunk.choices[0].delta.content)
            os.system("cls" if os.name == "nt" else "clear")
            print_model("".join(chunks))

    messages.append({"role": "system", "content": "".join(chunks)})


def get_results():
    print_system("Where is the results file located?")

    result_file_location = Prompt.ask("[blue]» User", default="./result.json")
    result_file_path = path.join(os.getcwd(), result_file_location)

    if not path.exists(result_file_path):
        print_system("Please provide a valid file path.")
        return

    with open(result_file_path, "r") as file:
        results = json.load(file)
        print_system("Successfully loaded the results.")

    return results


def get_context():
    print_system("Please provide a short description of the context of the model.")

    context_information = Prompt.ask(
        "[blue]» User", default="Media Spendings and Sales data for an company"
    )

    return context_information


def run():
    print_system("Welcome to the model interface!")

    results = get_results()

    initial_prompt = f"""
      The following results are information regarding the results of an linear regression model.
      
      results: {json.dumps(results['metrics'])}
      context of the results: {results['context']}
      
      Explain the given results and context in a way that a non-technical person can understand it.
      Give the user a clear understand, what the models does, what factors are influencing the result and
      why the result may be interesting from a business perspective.
      
      Always follow the guidelines for the answers and the user information strictly!
      
      Information regarding your answer style:
        - Always focus on the business or marketing aspect and not the technical details.
        - Please use proper grammar.
        - Please be polite.
        - Please be concise.
        - Please be clear.
        - Please answer as simple as possible
        - Do not use any abbreviations.
        - Do not use any technical terms.
        - Keep your answer as short as possible!
        - Sturcture your answer for best readability with short sentencens
        - Explain your answer in a way that a non-technical person can understand it
        - Dont answer to questions that are not regarding the model.
        - Only refer to knowledge that is provided in the context. Do not make any assumptions.
        
      Information regarding the answer format:
        - Use the markdown to style your answer
        - Never center any text in markdown
        - Keep the styling simple, but precise with an clear visual structure
        - Dont use line breaks in markdown
        - Dont use headings in markdown such as ### or ##, ...
        - Print numbers as inline code
        - Always refer to the results and context in your answer
      
      Try to follow the following structure if you answer a question or explain something:
        - Start with a short introduction
        - Explain the main part
        - End with a conclusion
        - Give example questions, that the user may ask to get more information
      
      Information about the user, that is asking questions and that you are answering to:
        - The user is a non-technical person
        - The user is a business person
        - The user might have some marketing knowledge
        - The user is interested in the results of the model
        - The user is representing the company that the model was created for
        - Dont adress the user directly in your answers, always refer as "the company" or the company name if provided in the context
    """

    get_response(
        initial_prompt,
    )

    while True:
        question = Prompt.ask("[blue]» User")

        if question == "exit":
            print_system("Exiting the model interface. Goodbye!")
            break

        get_response(question)


if __name__ == "__main__":
    run()
