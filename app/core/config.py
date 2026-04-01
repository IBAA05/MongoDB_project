from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "smartphone_catalog"
    COLLECTION_NAME: str = "phones"
    APP_TITLE: str = "Smartphone Catalog API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "MongoDB Text Search and Aggregation — Person 1: Data, Search & Performance"
    )

    class Config:
        env_file = ".env"


settings = Settings()
