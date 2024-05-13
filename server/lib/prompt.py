import asyncio
from enum import Enum
import json
import threading
from typing import Literal, TypedDict, Union

from openai import Client, AsyncStream, NotGiven


class Model(Enum):
    GPT_35 = "gpt-3.5"
    GPT_35_TURBO = "gpt-3.5-turbo"

    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"


class Persona(Enum):
    NON_TECHNICAL = "non_technical"
    TECHNICAL = "technical"
    BUSINESS = "business"
    EXPERT = "expert"


class AnswerStyle(Enum):
    EXPLANATION = "explanation"
    STRUCTURED = "structured"


class Format(Enum):
    NO_FORMAT = "no_format"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"


class ToolCall(TypedDict):
    type: Literal["tool_call"]
    name: str
    args: dict


class AIResponse(TypedDict):
    type: Literal["ai_response"]
    content: str | None


PromptStreamChunk = Union[ToolCall, AIResponse]


class PromptStream:
    def __init__(self):
        self.data = []
        self.index = 0
        self.lock = threading.Lock()
        self.condition = threading.Condition(lock=self.lock)
        self.stream_open = True

    def __iter__(self):
        return self

    def __next__(self) -> PromptStreamChunk:
        with self.lock:
            while self.index >= len(self.data) and self.stream_open:
                self.condition.wait()
            if self.index >= len(self.data):
                raise StopIteration
            value = self.data[self.index]
            self.index += 1
            return value

    def add_data(self, data):
        with self.lock:
            self.data.append(data)
            self.condition.notify()

    def close_stream(self):
        with self.lock:
            self.stream_open = False
            self.condition.notify_all()


class PromptGeneratorAnswer:
    def __init__(self, content: str | None, messages: list) -> None:
        self.content = content
        self.messages = messages


class PromptGenerator:
    def __init__(
        self,
        prompt: str,
        response_structure: str | dict | None = None,
        messages: list = [],
        model: Model = Model.GPT_35_TURBO,
        persona: Persona | None = None,
        answerStyle: AnswerStyle | None = None,
        format: Format | None = None,
        tools: list = [],
        functions: dict = {},
        plain: bool = False,
    ) -> None:
        self.prompt = prompt
        self.response_structure = response_structure
        self.messages = messages
        self.model = model
        self.persona = persona
        self.answerStyle = answerStyle
        self.format = format
        self.tools = tools
        self.functions = functions
        self.plain = plain

        self.client = None
        self.stream = PromptStream()
        self.image_bytes = []

    def run(self, api_key: str, imagesBytes: list = []):
        prompt_thread = threading.Thread(
            target=self._execute_prompt,
            args=(
                api_key,
                imagesBytes,
            ),
        )
        prompt_thread.start()

        return self.stream

    def _execute_prompt(self, api_key: str, imagesBytes: list):

        client = Client(
            api_key=api_key,
        )

        if len(imagesBytes) > 0 and (
            self.model != Model.GPT_4_TURBO or self.model != Model.GPT_4
        ):
            raise ValueError(
                "Images are only supported for GPT-4 model. Please use GPT-4 model."
            )

        prompt = self._generate_prompt()

        content = []
        content.append({"type": "text", "text": prompt})

        for image in imagesBytes:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image}"},
                }
            )

        self.messages.append({"role": "user", "content": content})

        self._run_prompt(client, self.stream)

        self.stream.close_stream()

    def _run_prompt(self, client: Client, stream: PromptStream):
        response = client.chat.completions.create(
            model=self.model.value,
            messages=self.messages,
            tools=self.tools if len(self.tools) > 0 else NotGiven(),
            response_format={
                "type": "json_object" if self.format == Format.JSON else "text"
            },
            stream=True,
        )

        function_calls = {}
        message = None

        for chunk in response:
            delta = chunk.choices[0].delta

            if delta.tool_calls:
                if delta.role:
                    self.messages.append(delta)
                    tool_calls = delta.tool_calls
                    function_calls = {
                        tool_call.index: {
                            "id": tool_call.id,
                            "name": tool_call.function.name,
                            "args": tool_call.function.arguments,
                        }
                        for tool_call in tool_calls
                        if tool_call.function
                    }
                else:
                    for tool_call in delta.tool_calls:

                        if tool_call.index in function_calls.keys():
                            if (
                                tool_call.function == None
                                or tool_call.function.arguments == None
                            ):
                                continue
                            if (
                                function_calls[tool_call.index] == None
                                or function_calls[tool_call.index]["args"] == None
                            ):
                                function_calls[tool_call.index][
                                    "args"
                                ] = tool_call.function.arguments
                            else:
                                function_calls[tool_call.index]["args"] += tool_call.function.arguments  # type: ignore

            if chunk.choices[0].finish_reason == "tool_calls":
                break

            if delta.tool_calls == None:
                self.stream.add_data(
                    {
                        "type": "ai_response",
                        "content": delta.content,
                    }
                )

        if len(function_calls.keys()) > 0:
            for index in function_calls:

                func_call = function_calls[index]

                name = func_call["name"] if func_call["name"] else ""
                args = json.loads(func_call["args"] if func_call["args"] else "{}")
                call_id = func_call["id"] if func_call["id"] else ""

                self.stream.add_data({"type": "tool_call", "name": name, "args": args})

                tool_response = self._handle_tool_call(name, args)

                self.messages.append(
                    {
                        "tool_call_id": call_id,
                        "role": "tool",
                        "name": name,
                        "content": json.dumps(tool_response),
                    }
                )
            self._run_prompt(client, stream)
        else:
            return

    def _handle_tool_call(self, name: str, args: dict):
        if name in self.functions:
            return self.functions[name](**args)
        return None

    def _generate_prompt(self):

        # User Profile
        user_profile = self._get_user_profile()

        # Answer Style
        answer_style = self._get_answer_style()

        # Response Structure
        response_structure = (
            f"""Response Structure: {self.response_structure}"""
            if self.response_structure
            else ""
        )

        # Answer Format
        answer_format = self._get_format()

        language = (
            f"""
            Language Style:
            - The answer should always be appropriate for the user profile.
            - Use words, that are suited for the user profile. Prefer simple words over technical jargon.
            - Do not answer directly to the user. Instead, provide a general answer that is easy to understand.
            - Do not mention the user profile itself in the answer. The answer should be general.
            - Use professional language, that is appropriate for the user profile.
        """
            if self.plain == False
            else ""
        )

        return f"""
    
            {self.prompt}
            
            {language}
    
            {response_structure}
            
            Answer Style:
            {answer_style}
            
            Answer Format:
            {answer_format}
            - Return the html code directly, if you created if with an function or tool call.
    
            User Profile:
            {user_profile}
        """

    def _get_user_profile(self):
        if self.persona == None:
            return f"""
                - The user profile is not defined.
            """
        if self.persona == Persona.NON_TECHNICAL:
            return f"""
                - The user is a non-technical person.
                - The user is not familiar with technical jargon.
                - The user is not familiar with statistical concepts, terms, methods or abbreviations.
                - The user is not familiar with machine learning or artificial intelligence.
                - The user is not familiar with programming languages.
                - The user is not familiar with data science.
                - The user might be familiar with basic concepts of marketing, sales, or business.
            """
        elif self.persona == Persona.TECHNICAL:
            return f"""
                - The user is a technical person.
                - The user is familiar with technical jargon.
                - The user is familiar with statistical concepts, terms, methods or abbreviations.
                - The user is familiar with machine learning or artificial intelligence.
                - The user is familiar with programming languages.
                - The user is familiar with data science.
                - The user might be familiar with basic concepts of marketing, sales, or business.
            """
        elif self.persona == Persona.BUSINESS:
            return f"""
                - The user is a business person.
                - The user is not familiar with technical jargon.
                - The user is not familiar with statistical concepts, terms, methods or abbreviations.
                - The user is not familiar with machine learning or artificial intelligence.
                - The user is not familiar with programming languages.
                - The user is not familiar with data science.
                - The user is familiar with concepts of marketing, sales, or business.
                - The user is familiar with financial concepts.
                - The user understands technical, statistical and ai concepts better when explained in simple terms.
                - The user preferes examples from real life scenarios, for technical, statistical and ai concepts.
            """
        elif self.persona == Persona.EXPERT:
            return f"""
                - The user is an expert in the field.
                - The user is familiar with technical jargon.
                - The user is familiar with statistical concepts, terms, methods or abbreviations.
                - The user is familiar with machine learning or artificial intelligence.
                - The user is familiar with programming languages.
                - The user is familiar with data science.
                - The user is familiar with concepts of marketing, sales, or business.
            """
        else:
            return "Unknown user profile"

    def _get_answer_style(self):
        if self.answerStyle == None:
            return f"""
                - The Answer Style is not defined.
            """
        if self.answerStyle == AnswerStyle.EXPLANATION:
            return f"""
                - The answer should be an explanation.
                - The explanation should contain an introduction, body and conclusion.
                - The explanation should be visualized with examples, if possible and appropriate.
            """
        elif self.answerStyle == AnswerStyle.STRUCTURED:
            return f"""
                - The answer should be structured.
                - The answer should fill in the blanks of the previously provided structure.
            """
        else:
            return "Unknown answer style"

    def _get_format(self):
        if self.format == None:
            return f"""
                - The Format is not defined.
            """
        if self.format == Format.NO_FORMAT:
            return f"""
                - The answer should be in plain text.
            """
        elif self.format == Format.JSON:
            return f"""
                - The answer should be in JSON format.
            """
        elif self.format == Format.HTML:
            return f"""
                - Do not use markdown!
                - Do not wrap the html in an markdown code block!
                - The answer should be in HTML format.
                - Wrap numbers in <code> tags.
                - Wrap code in <code> tags.
                - Wrap code blocks in <pre> tags.
                - Use h3, h4, h5, h6 tags for headings.
                - Use <ul> and <li> tags for lists.
                - Use <a> tags for links.
                - Use <strong> tags for bold text.
                - Use <em> tags for italic text.
                - Use <blockquote> tags for quotes.
                - Do not use other HTML tags.
            """
        elif self.format == Format.MARKDOWN:
            return f"""
                - The answer should be in Markdown format.
            """
        else:
            return "Unknown format"
