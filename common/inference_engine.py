import json
import os
import asyncio
import httpx
import anthropic
from typing import Any, Dict, List, Optional, AsyncGenerator

from decimal import Decimal

NANO_GPT_API_KEY=os.getenv("NANO_GPT_API_KEY", None)

class InferenceEvent:
    """
    Container for streaming events. 
    event_type could be "aiCompletion", "toolUse", "usage_delta", "done", etc.
    """
    def __init__(self, event_type: str, text: str = "", usage: Any = None, data: Any = {}):
        self.type = event_type
        self.text = text
        self.usage = usage
        self.data = data

class ProviderNotImplementedError(Exception):
    pass

class InferenceEngine:
    """
    A provider-agnostic inference engine that can be spun up with either
    'anthropic' or 'nanogpt' or any additional providers you define.
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model_name: str = None,
        max_tokens: int = 8192,
    ):
        self.provider = provider
        self.model_name = model_name
        self.max_tokens = max_tokens

    async def infer_stream(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None
    ) -> AsyncGenerator[InferenceEvent, None]:
        """
        Async generator that yields InferenceEvent objects in real time.
        Also emits events to your JS and main app streams as needed.
        """

        # 3) Actually stream from the chosen provider
        async for event in self._stream_provider(messages, system):
            if event.type == "token_delta":
                yield InferenceEvent("aiCompletion", text=event.text)

        yield InferenceEvent("done")

    async def _stream_provider(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str],
    ) -> AsyncGenerator[InferenceEvent, None]:
        """
        Routes to the correct provider method. Yields InferenceEvent objects.
        """
        if self.provider == "anthropic":
            async for event in self._stream_anthropic(messages, system):
                yield event
        elif self.provider == "nanogpt":
            async for event in self._stream_nanogpt(messages, system):
                yield event
        else:
            raise ProviderNotImplementedError(f"Provider {self.provider} is not implemented.")

    async def _stream_anthropic(
        self,
        messages,
        system,
        user=None,
        session=None
    ) -> AsyncGenerator[InferenceEvent, None]:
        """
        Streams tokens from Anthropic using the anthropic library.
        """
        from os import getenv
        ENV = getenv("ENV", "dev")

        model = self.model_name
        client = anthropic.AsyncAnthropic()

        if not system:
            system = ""
        async with client.messages.stream(
            model=model,
            messages=messages,
            system=system,
            max_tokens=self.max_tokens
        ) as stream:
            async for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "text_delta":
                    yield InferenceEvent("token_delta", text=event.delta.text)
                if event.type in ["message_delta", "message_start"]:
                    usage_data = getattr(event, "usage", None)
                    if event.type == "message_start":
                        usage_data = event.message.usage

    async def _stream_nanogpt(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str]
    ) -> AsyncGenerator[InferenceEvent, None]:
        """
        Streams tokens from a hypothetical NanoGPT endpoint. 
        Mirrors your existing `stream_nano_gpt` logic.
        """
        import json

        nano_gpt_endpoint = "https://nano-gpt.com/api/v1/chat/completions"
        model = self.model_name or "nano-gpt-base"

        combined_messages = []
        if system:
            combined_messages.append({"role": "system", "content": system})
        combined_messages.extend(messages)

        #Disable images on nanogpt for now
        for i, message in enumerate(combined_messages):
            if message["role"] == "user" and type(message["content"])==type([]):
                content = None
                for c in message["content"]:
                    if c["type"] == "text":
                        content = c["text"]
                        break
                message["content"] = content

        data = {
            "model": model,
            "messages": combined_messages,
            "stream": True
        }
        headers = {
            "Authorization": f"Bearer {NANO_GPT_API_KEY}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", nano_gpt_endpoint, headers=headers, json=data) as response:
                if response.status_code != 200:
                    err_text = await response.aread()
                    yield InferenceEvent("token_delta", text=f"Error: {err_text.decode()}")
                    return

                buffer = ""
                async for chunk in response.aiter_bytes():
                    if not chunk:
                        continue
                    buffer += chunk.decode("utf-8")

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line.startswith("data: "):
                            payload = line[len("data: "):]
                            try:
                                data_obj = json.loads(payload)
                                delta_chunk = data_obj["choices"][0]["delta"].get("content", "")
                                if delta_chunk:
                                    yield InferenceEvent("token_delta", text=delta_chunk)
                            except (json.JSONDecodeError, KeyError):
                                pass


async def llm_call(system, messages):
    engine = InferenceEngine(
        provider="nanogpt",
        model_name="deepseek-reasoner",
        max_tokens=4096,
    )
    response_text = ""
    async for event in engine.infer_stream(
        messages=messages,
        system=system
    ):
        if event.type == "aiCompletion":
            response_text += event.text
        elif event.type == "done":
            break
    return response_text


