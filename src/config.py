from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: str
    HOST: str
    DATABASE: str
    USER_PG: str
    PASSWORD: str

    model_config = SettingsConfigDict(env_file=".env")
