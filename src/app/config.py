import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Begriff"
    app_name: str = "Begriff"
    app_version: str = "2.0.0"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    DATABASE_URL: Optional[str] = None
    DATABASE_SSL_MODE: str = "require"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    access_token_expire_minutes: int = 30
    ENABLE_DEFAULT_ADMIN: bool = True
    DEFAULT_ADMIN_EMAIL: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin"

    # Reverse proxy / perimeter.
    TRUST_PROXY_HEADERS: bool = True

    GATEWAY_API_URL: str = "http://localhost:8081"
    OPEN_BANKING_MOCK_URL: str = "http://open_banking_mock_server:8080"
    BLOCKCHAIN_NODE_URL: str = "http://blockchain_node:8545"
    AUDIT_CONTRACT_ADDRESS: str = "0x0000000000000000000000000000000000000000"
    GEMINI_API_KEY: str = ""

    cpp_gateway_host: str = "localhost"
    cpp_gateway_port: int = 8081
    cpp_gateway_timeout: int = 30
    pipe_communication_enabled: bool = True
    ml_model_path: str = "src/domains/risk/models"
    fraud_detection_algorithm: str = "isolation_forest"
    fraud_detection_threshold: float = 0.7
    carbon_calculation_enabled: bool = True
    audit_hash_algorithm: str = "sha256"
    audit_trail_enabled: bool = True
    blockchain_simulation_mode: bool = True
    monte_carlo_engine: str = "numpy"
    monte_carlo_simulations: int = 10000
    digital_twins_enabled: bool = True

    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "begriff"
    POSTGRES_PASSWORD: str = "begriff_secret_password"
    POSTGRES_DB: str = "begriffdb"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        is_docker = self._is_docker_environment()

        if not self.DATABASE_URL:
            if is_docker:
                self.DATABASE_URL = (
                    f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                    f"{self.POSTGRES_SERVER}:5432/{self.POSTGRES_DB}"
                )
            else:
                self.DATABASE_URL = "sqlite:///./data/dev/dev.db"

        if is_docker:
            self.OPEN_BANKING_MOCK_URL = "http://open_banking_mock_server:8080"
            self.BLOCKCHAIN_NODE_URL = "http://blockchain_node:8545"
        else:
            self.OPEN_BANKING_MOCK_URL = "http://localhost:8080"
            self.BLOCKCHAIN_NODE_URL = "http://localhost:8545"

    def _is_docker_environment(self) -> bool:
        return (
            os.path.exists("/.dockerenv")
            or self.POSTGRES_SERVER == "db"
            or "docker" in os.getenv("HOSTNAME", "").lower()
            or os.getenv("CONTAINER_ENV") == "docker"
        )

    @property
    def cors_origins_list(self):
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw:
            return []
        if raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


settings = Settings()
