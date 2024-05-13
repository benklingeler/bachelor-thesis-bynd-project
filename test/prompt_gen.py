from enum import Enum

from openai import AsyncClient, AsyncStream


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
        persona: Persona = Persona.NON_TECHNICAL,
        answerStyle: AnswerStyle = AnswerStyle.EXPLANATION,
        format: Format = Format.NO_FORMAT,
        stream: bool = False,
    ) -> None:
        self.prompt = prompt
        self.response_structure = response_structure
        self.messages = messages
        self.model = model
        self.persona = persona
        self.answerStyle = answerStyle
        self.format = format
        self.stream = stream

    async def execute_prompt(self, client: AsyncClient, imagesBytes: list = []):

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

        response = await client.chat.completions.create(
            model=self.model.value,
            messages=self.messages,
            response_format={
                "type": "json_object" if self.format == Format.JSON else "text"
            },
            stream=self.stream,
        )

        if isinstance(response, AsyncStream):
            return response
        else:
            return PromptGeneratorAnswer(
                response.choices[0].message.content, self.messages
            )

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

        return f"""
    
            {self.prompt}
            
            Language Style:
            - The answer should always be appropriate for the user profile.
            - Use words, that are suited for the user profile. Prefer simple words over technical jargon.
            - Do not answer directly to the user. Instead, provide a general answer that is easy to understand.
            - Do not mention the user profile itself in the answer. The answer should be general.
            - Use professional language, that is appropriate for the user profile.
    
            {response_structure}
            
            Answer Style:
            {answer_style}
            
            Answer Format:
            {answer_format}
    
            User Profile:
            {user_profile}
        """

    def _get_user_profile(self):
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
