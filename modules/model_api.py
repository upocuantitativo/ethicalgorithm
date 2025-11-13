"""
Module 3: Model API Handler
Manages interactions with various LLM APIs (OpenAI, Anthropic, Google, etc.)
"""

import os
from typing import Optional, List, Dict, Any
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelAPIHandler:
    """
    Unified interface for querying different LLM APIs.
    Supports OpenAI (GPT-4, GPT-3.5), Anthropic (Claude), Google (Gemini), and others.
    """

    def __init__(self):
        """Initialize the API handler and load credentials."""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')

        # Initialize clients lazily when needed
        self._openai_client = None
        self._anthropic_client = None
        self._google_client = None

    def _get_openai_client(self):
        """Lazy initialization of OpenAI client."""
        if self._openai_client is None:
            try:
                import openai
                openai.api_key = self.openai_api_key
                self._openai_client = openai
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.error("openai package not installed. Install with: pip install openai")
                raise
        return self._openai_client

    def _get_anthropic_client(self):
        """Lazy initialization of Anthropic client."""
        if self._anthropic_client is None:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                logger.info("Anthropic client initialized")
            except ImportError:
                logger.error("anthropic package not installed. Install with: pip install anthropic")
                raise
        return self._anthropic_client

    def _get_google_client(self):
        """Lazy initialization of Google Generative AI client."""
        if self._google_client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_api_key)
                self._google_client = genai
                logger.info("Google Generative AI client initialized")
            except ImportError:
                logger.error("google-generativeai package not installed. Install with: pip install google-generativeai")
                raise
        return self._google_client

    def call_model_api(
        self,
        model_name: str,
        prompt: str,
        context: Optional[List[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        retry_attempts: int = 3
    ) -> str:
        """
        Query the specified LLM API and return the response text.

        Args:
            model_name: Name/identifier of the model (e.g., "gpt-4", "claude-v1", "gemini-pro")
            prompt: The question/prompt to send to the model
            context: Optional list of previous Q&A strings for conversation context
            temperature: Sampling temperature (0.0 to 1.0+)
            max_tokens: Maximum tokens in the response
            retry_attempts: Number of retry attempts on failure

        Returns:
            String containing the model's response
        """
        # Build full prompt with context if provided
        full_prompt = self._build_prompt_with_context(prompt, context)

        # Route to appropriate API based on model name
        model_lower = model_name.lower()

        for attempt in range(retry_attempts):
            try:
                if "gpt-4" in model_lower or "gpt-3.5" in model_lower or "chatgpt" in model_lower:
                    return self._call_openai(model_name, full_prompt, temperature, max_tokens)

                elif "claude" in model_lower:
                    return self._call_anthropic(model_name, full_prompt, temperature, max_tokens)

                elif "gemini" in model_lower or "palm" in model_lower:
                    return self._call_google(model_name, full_prompt, temperature, max_tokens)

                else:
                    logger.warning(f"Unknown model: {model_name}. Returning placeholder.")
                    return f"[Placeholder response for {model_name}]"

            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{retry_attempts} failed for {model_name}: {e}")
                if attempt < retry_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All retry attempts failed for {model_name}")
                    return f"[Error: Failed to get response from {model_name}]"

    def _build_prompt_with_context(self, prompt: str, context: Optional[List[str]]) -> str:
        """
        Build full prompt including conversation context.

        Args:
            prompt: Current prompt
            context: List of previous context strings

        Returns:
            Combined prompt string
        """
        if context:
            context_str = "\n".join(context)
            return f"{context_str}\n\n{prompt}"
        return prompt

    def _call_openai(self, model_name: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """
        Call OpenAI API (GPT-4, GPT-3.5-turbo, etc.)

        Args:
            model_name: OpenAI model identifier
            prompt: Full prompt including context
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Model response text
        """
        client = self._get_openai_client()

        # Determine actual model ID
        if "gpt-4" in model_name.lower():
            model_id = "gpt-4"
        else:
            model_id = "gpt-3.5-turbo"

        # Use ChatCompletion API
        messages = [{"role": "user", "content": prompt}]

        response = client.ChatCompletion.create(
            model=model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        answer = response['choices'][0]['message']['content'].strip()
        logger.info(f"OpenAI API call successful for {model_name}")
        return answer

    def _call_anthropic(self, model_name: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """
        Call Anthropic API (Claude models)

        Args:
            model_name: Anthropic model identifier
            prompt: Full prompt including context
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Model response text
        """
        client = self._get_anthropic_client()

        # Use the new Messages API with claude-3-opus
        response = client.messages.create(
            model="claude-3-opus-20240229",  # Claude 3 Opus (most capable)
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.content[0].text.strip()
        logger.info(f"Anthropic API call successful for {model_name}")
        return answer

    def _call_google(self, model_name: str, prompt: str, temperature: float, max_tokens: int) -> str:
        """
        Call Google Generative AI API (Gemini, PaLM)

        Args:
            model_name: Google model identifier
            prompt: Full prompt including context
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Model response text
        """
        genai = self._get_google_client()

        # Configure generation parameters
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # Use Gemini Pro model
        model = genai.GenerativeModel('gemini-pro')

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        answer = response.text.strip()
        logger.info(f"Google API call successful for {model_name}")
        return answer

    def test_connection(self, model_name: str) -> bool:
        """
        Test if API connection works for a given model.

        Args:
            model_name: Model to test

        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_prompt = "Say 'OK' if you can read this."
            response = self.call_model_api(model_name, test_prompt, max_tokens=10)
            logger.info(f"Connection test successful for {model_name}: {response}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed for {model_name}: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    print("ModelAPIHandler module loaded successfully")
    print("\nExample usage:")
    print("handler = ModelAPIHandler()")
    print("response = handler.call_model_api('gpt-4', 'What is ethics?')")
    print("\nNote: Requires API keys set as environment variables:")
    print("  OPENAI_API_KEY for GPT models")
    print("  ANTHROPIC_API_KEY for Claude models")
    print("  GOOGLE_API_KEY for Gemini models")
