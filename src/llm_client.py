from src.config import CLAUDE_CLI, GEMINI_CLI, CLAUDE_MODEL, GEMINI_MODEL, SYSTEM_PROMPT, ENABLE_FALLBACK, logger
import litellm
from src.llm_service.litellm_acp_provider import register_acp_providers

class AIClient:
    def __init__(self):
        self._setup_provider()

    def _setup_provider(self):
        # Register ACP Providers (Claude CLI, Gemini CLI)
        try:
            register_acp_providers()
            logger.info("ACP Providers registered.")
        except Exception as e:
            logger.warning(f"Failed to register ACP providers: {e}")

        # Determine Model String based on CLI flags
        if CLAUDE_CLI:
            self.model_name = CLAUDE_MODEL
        elif GEMINI_CLI:
            self.model_name = GEMINI_MODEL
        else:
            self.model_name = "echo" # Special internal flag for Echo
            logger.warning("No CLI provider enabled. Defaulting to Echo mode.")
        
        logger.info(f"AI Client configured with model: {self.model_name}")

    def _get_fallback_model(self, current_model: str) -> str:
        """Determines the fallback model based on the current one."""
        if "gemini" in current_model.lower():
            return "gemini-acp/gemini-2.5-flash"
        elif "claude" in current_model.lower():
            return "claude-acp/sonnet"
        return None

    async def get_response(self, prompt: str) -> str:
        """
        Get response from LLM via LiteLLM.
        """
        if self.model_name == "echo":
             return f"[Echo] {prompt}"

        # AISOP Native Shim Logic
        # Priority: Configured SYSTEM_PROMPT from .env, or a fallback basic prompt
        system_prompt = SYSTEM_PROMPT or "# Role: AISOP Virtual Runtime (V3.1)\nYou are a helpful AI assistant."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            logger.info(f"Sending prompt to {self.model_name}...")
            response = await litellm.acompletion(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Error calling LLM ({self.model_name}): {e}")
            
            # Fallback Logic
            if ENABLE_FALLBACK:
                fallback_model = self._get_fallback_model(self.model_name)
                # Check if we should fallback (and haven't already tried the fallback model)
                if fallback_model and fallback_model != self.model_name:
                    logger.warning(f"[Fallback] Switching to {fallback_model} due to error...")
                    try:
                        response = await litellm.acompletion(
                            model=fallback_model,
                            messages=messages
                        )
                        return response.choices[0].message.content
                    except Exception as fallback_error:
                        error_msg = (
                            f"⚠️ **Service Unavailable (All Models Failed)**\n\n"
                            f"**Primary ({self.model_name})**: {e}\n"
                            f"**Fallback ({fallback_model})**: {fallback_error}\n\n"
                            f"Please check quotas or configuration."
                        )
                        logger.error(error_msg)
                        return error_msg

            return f"Error interacting with AI: {e}"

    async def get_streaming_response(self, prompt: str):
        """
        Get streaming response from LLM via LiteLLM.
        """
        if self.model_name == "echo":
             yield f"[Echo] {prompt}"
             return

        system_prompt = SYSTEM_PROMPT or "# Role: AISOP Virtual Runtime (V3.1)\nYou are a helpful AI assistant."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            logger.info(f"Sending streaming prompt to {self.model_name}...")
            response = await litellm.acompletion(
                model=self.model_name,
                messages=messages,
                stream=True
            )
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.warning(f"Error calling streaming LLM ({self.model_name}): {e}")
            
            # Fallback Logic
            should_fallback = False
            fallback_model = None
            
            if ENABLE_FALLBACK:
                fallback_model = self._get_fallback_model(self.model_name)
                if fallback_model and fallback_model != self.model_name:
                    should_fallback = True
            
            if should_fallback:
                logger.warning(f"[Fallback] Switching stream to {fallback_model} due to error...")
                try:
                    response = await litellm.acompletion(
                        model=fallback_model,
                        messages=messages,
                        stream=True
                    )
                    async for chunk in response:
                        content = chunk.choices[0].delta.content
                        if content:
                            yield content
                except Exception as fallback_error:
                    error_msg = (
                        f"⚠️ **Service Unavailable (All Models Failed)**\n\n"
                        f"**Primary ({self.model_name})**: {e}\n"
                        f"**Fallback ({fallback_model})**: {fallback_error}\n\n"
                        f"Please check quotas or configuration."
                    )
                    logger.error(error_msg)
                    yield error_msg
            else:
                yield f"Error interacting with AI: {e}"
