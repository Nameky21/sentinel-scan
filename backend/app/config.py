from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    zap_host: str = "127.0.0.1"
    zap_port: int = 8080
    zap_api_key: str = "change-me"
    database_url: str = "sqlite:///./sentinelscan.db"
    cors_origins: str = "http://localhost:5173"

    # Scans are time-boxed so a run against a large target stays demo-practical.
    spider_max_duration_mins: int = 2
    ajax_spider_max_duration_mins: int = 3
    ascan_max_duration_mins: int = 10
    # Single-page apps need a real browser to crawl; ZAP defaults to Firefox.
    ajax_spider_browser: str = "chrome-headless"
    reports_dir: str = "reports_output"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def zap_base_url(self) -> str:
        return f"http://{self.zap_host}:{self.zap_port}"


settings = Settings()
