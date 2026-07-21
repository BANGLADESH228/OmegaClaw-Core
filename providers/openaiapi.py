import os
import lib_llm_ext as llm
import providers
from config import config_get_by_key

class OpenAIAPI(providers.LLMProvider):

    def __init__(self, name):
        super().__init__()
        self._name = name

    def api_token_var(self):
        return config_get_by_key("api_token_var", "OPENAIAPI_API_KEY")

    def model(self):
        return config_get_by_key("model", "qwen3.5:9b")

    def base_url(self):
        return config_get_by_key("openaiapi_url", "http://localhost:11434/v1/")

    def start(self) -> None:
        self.delegate = llm.AIProvider(self._name, self.api_token_var(),
                                       self.model(), self.base_url())

    def stop(self) -> None:
        self.delegate.stop()

    def chat(self, prompt: str, max_tokens: int = 6000, reasoning_mode: str = "medium") -> str:
        return self.delegate.chat(prompt, max_tokens, reasoning_mode)


class OpenAIAPIPreconfigured(OpenAIAPI):

    def __init__(self, name, api_token_var, default_model, base_url):
        super().__init__(name)
        self._api_token_var = api_token_var
        self._default_model = default_model
        self._base_url = base_url

    def api_token_var(self):
        return self._api_token_var

    def model(self):
        return config_get_by_key("model", self._default_model)

    def base_url(self):
        return self._base_url

def loadOmegaClawPlugin():
    providers.registerLLMProvider("OpenAIAPI", OpenAIAPI("OpenAIAPI"))
    providers.registerLLMProvider("ASICloud", OpenAIAPIPreconfigured("ASICloud", "ASI_API_KEY", "minimax/minimax-m3", "https://inference.asicloud.cudos.org/v1"))
    providers.registerLLMProvider("Anthropic", OpenAIAPIPreconfigured("Anthropic", "ANTHROPIC_API_KEY", "claude-opus-4-8", "https://api.anthropic.com/v1/"))
