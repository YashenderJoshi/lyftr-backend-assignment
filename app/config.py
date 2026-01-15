import os

class Settings:
    DATABASE_URL: str
    WEBHOOK_SECRET: str
    LOG_LEVEL: str = "INFO"

    def __init__(self):
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        self.WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

        if not self.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")

        if not self.WEBHOOK_SECRET:
            raise RuntimeError("WEBHOOK_SECRET is not set")


settings = Settings()

