from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./codereviewer.db"

    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # GitHub
    GITHUB_TOKEN: str
    GITHUB_WEBHOOK_SECRET: str

    # Set to true ONLY during local development to skip signature verification.
    # Never set this in production.
    DEBUG_SKIP_WEBHOOK_SIGNATURE_CHECK: bool = False

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    # Recipients — stored as raw string, exposed as list
    REPORT_RECIPIENT_EMAILS: str = ""

    @property
    def recipient_emails(self) -> List[str]:
        return [
            e.strip()
            for e in self.REPORT_RECIPIENT_EMAILS.split(",")
            if e.strip()
        ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
