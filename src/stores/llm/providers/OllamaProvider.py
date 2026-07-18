from ..LLMInterface import LLMInterface
from ..LLMEnums import OllamaEnums

import ollama
from ollama import Client
from loguru import logger

from typing import List, Union


class OllamaProvider(LLMInterface):

    def __init__(
        self,
        api_url: str = None,
        default_input_max_characters: int = 1000,
        default_generation_max_output_tokens: int = 1000,
        default_generation_temperature: float = 0.1,
        think: bool = False,
    ):

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None

        self.think = think

        self.client = Client(
            host=api_url if api_url else "http://localhost:11434"
        )

        self.enums = OllamaEnums

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()

    def generate_text(
        self,
        prompt: str,
        chat_history: list = [],
        max_output_tokens: int = None,
        temperature: float = None,
    ):

        if not self.generation_model_id:
            logger.error("Generation model for Ollama was not set")
            return None

        max_output_tokens = (
            max_output_tokens
            if max_output_tokens
            else self.default_generation_max_output_tokens
        )

        temperature = (
            temperature
            if temperature is not None
            else self.default_generation_temperature
        )

        chat_history.append(
            self.construct_prompt(
                prompt=prompt,
                role=OllamaEnums.USER.value,
            )
        )

        response = self.client.chat(
            model=self.generation_model_id,
            messages=chat_history,
            think=self.think,
            options={
                "temperature": temperature,
                "num_predict": max_output_tokens,
            },
        )

        if (
            not response
            or "message" not in response
            or "content" not in response["message"]
        ):
            logger.error("Error while generating text with Ollama")
            return None

        return response["message"]["content"]

    def embed_text(
        self,
        text: Union[str, List[str]],
        document_type: str = None,
    ):

        if not self.embedding_model_id:
            logger.error("Embedding model for Ollama was not set")
            return None

        if isinstance(text, str):
            text = [text]

        response = self.client.embed(
            model=self.embedding_model_id,
            input=text,
        )

        if (
            not response
            or "embeddings" not in response
            or len(response["embeddings"]) == 0
        ):
            logger.error("Error while embedding text with Ollama")
            return None

        return response["embeddings"]

    def construct_prompt(
        self,
        prompt: str,
        role: str,
    ):
        return {
            "role": role,
            "content": prompt,
        }