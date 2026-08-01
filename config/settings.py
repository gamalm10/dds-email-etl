from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    imap_host: str = "imap.example.com"
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""

    maria_host: str = "localhost"
    maria_port: int = 3306
    maria_user: str = "dds"
    maria_password: str = ""
    maria_database: str = "dds"

    pi_sidecar_cmd: str = "npx @earendil-works/pi-coding-agent --mode rpc --no-session"
    pi_timeout_seconds: int = 120

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_user: str = "gamal.abdelmoety@a-part.com"
    smtp_password: str = "guzn zcne wkyg jcnl"
    notify_recipients: str = ""
    notify_rate_limit_hours: int = 24
    jwt_secret: str = "dds-jwt-secret-change-in-production"

    @property
    def maria_dsn(self) -> str:
        return f"mysql+aiomysql://{self.maria_user}:{self.maria_password}@{self.maria_host}:{self.maria_port}/{self.maria_database}"

    @property
    def notify_recipient_list(self) -> list[str]:
        return [r.strip() for r in self.notify_recipients.split(",") if r.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

