from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/hacklytics"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    memory_top_k: int = 3
    memory_vector_dimension: int = 1536

    actian_host: str = "localhost:50051"
    actian_collection_name: str = "patient_long_term_memory"

    zocdoc_base_url: str = "https://api.zocdoc.com"
    zocdoc_client_id: str = ""
    zocdoc_client_secret: str = ""

    epic_fhir_base_url: str = "https://fhir.epic.com/interconnect-fhir-oauth"
    epic_client_id: str = ""
    epic_client_secret: str = ""

    elevenlabs_api_key: str = ""
    elevenlabs_agent_id: str = ""

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

