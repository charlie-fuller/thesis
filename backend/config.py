"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PocketBase
    pocketbase_url: str = "http://127.0.0.1:8090"
    pocketbase_email: str = ""
    pocketbase_password: str = ""

    # Vector sidecar
    vec_url: str = "http://127.0.0.1:8080"

    # Auth
    api_key: str = ""

    # AI providers
    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    mem0_api_key: str = ""

    # Server
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    default_model: str = "claude-sonnet-4-6"
    cors_origins: str = ""
    environment: str = "development"

    # Neo4j (kept for graph features)
    neo4j_uri: str = ""
    neo4j_user: str = ""
    neo4j_password: str = ""

    model_config = {"env_prefix": "THESIS_"}


settings = Settings()
