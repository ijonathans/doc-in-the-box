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
    medlineplus_collection: str = "medlineplus_topics"

    # Zocdoc developer API: use sandbox or production (https://api-docs.zocdoc.com/guides)
    zocdoc_base_url: str = "https://api-developer-sandbox.zocdoc.com"
    zocdoc_client_id: str = ""  # Required for real API; leave empty for in-app sandbox data
    zocdoc_client_secret: str = ""

    epic_fhir_base_url: str = "https://fhir.epic.com/interconnect-fhir-oauth"
    epic_client_id: str = ""
    epic_client_secret: str = ""

    elevenlabs_api_key: str = ""
    elevenlabs_agent_id: str = ""
    # ElevenLabs Twilio outbound: phone number ID from ElevenLabs Agents (connected Twilio number)
    elevenlabs_agent_phone_number_id: str = ""
    # Optional: set to your phone (E.164) to run test_outbound_call and receive a call
    outbound_call_test_phone: str = "9122242661"

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

