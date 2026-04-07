import os
from dataclasses import dataclass

import dspy
from dotenv import load_dotenv


@dataclass
class Settings:
    provider: str
    temperature: float
    max_tokens: int
    ollama_model: str
    ollama_api_base: str
    azure_api_key: str
    azure_endpoint: str
    azure_deployment: str
    azure_api_version: str


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        provider=os.getenv("DSPY_PROVIDER", "ollama").strip().lower(),
        temperature=float(os.getenv("DSPY_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv("DSPY_MAX_TOKENS", "300")),
        ollama_model=os.getenv("DSPY_OLLAMA_MODEL", "ollama_chat/llama3.2:3b").strip(),
        ollama_api_base=os.getenv("DSPY_OLLAMA_API_BASE", "http://localhost:11434").strip(),
        azure_api_key=os.getenv("AZURE_OPENAI_API_KEY", "").strip(),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").strip(),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "").strip(),
        azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview").strip(),
    )


def build_lm(settings: Settings) -> dspy.LM:
    if settings.provider == "ollama":
        return dspy.LM(
            model=settings.ollama_model,
            api_base=settings.ollama_api_base,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

    if settings.provider == "azure":
        api_key = settings.azure_api_key or _required_env("AZURE_OPENAI_API_KEY")
        endpoint = settings.azure_endpoint or _required_env("AZURE_OPENAI_ENDPOINT")
        deployment = settings.azure_deployment or _required_env("AZURE_OPENAI_DEPLOYMENT")

        return dspy.LM(
            model=f"azure/{deployment}",
            api_key=api_key,
            api_base=endpoint,
            api_version=settings.azure_api_version,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

    raise ValueError(
        f"Unsupported DSPY_PROVIDER '{settings.provider}'. Expected one of: ollama, azure"
    )


def configure_dspy() -> Settings:
    settings = load_settings()
    lm = build_lm(settings)
    dspy.settings.configure(lm=lm)
    return settings
