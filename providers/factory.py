from .ollama_provider import OllamaProvider


_provider = None


def get_provider():
    global _provider
    if _provider is None:
        _provider = OllamaProvider()
    return _provider


def reset_provider() -> None:
    global _provider
    _provider = None
