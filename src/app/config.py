from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Begriff"
    DATABASE_URL: str = "sqlite:///./test.db"
    JWT_SECRET_KEY: str = "supersecret"
    JWT_ALGORITHM: str = "HS256"
    GATEWAY_API_URL: str = "http://localhost:8080"
    OPEN_BANKING_MOCK_URL: str = "http://localhost:8081"
    BLOCKCHAIN_NODE_URL: str = "http://localhost:8545"
    AUDIT_CONTRACT_ADDRESS: str = "0x0000000000000000000000000000000000000000"
    GEMINI_API_KEY: str = ""
    app_name: str = "Begriff"
    app_version: str = "1.5.0"
    debug: bool = False
    database_wal_mode: bool = True
    sqlite_version_min: str = "3.40"
    secret_key: str = "supersecret"
    access_token_expire_minutes: int = 30
    cpp_gateway_host: str = "localhost"
    cpp_gateway_port: int = 8080
    cpp_gateway_timeout: int = 30
    pipe_communication_enabled: bool = True
    ml_model_path: str = "./models/"
    fraud_detection_algorithm: str = "isolation_forest"
    fraud_detection_threshold: float = 0.7
    carbon_calculation_enabled: bool = True
    audit_hash_algorithm: str = "sha256"
    audit_trail_enabled: bool = True
    blockchain_simulation_mode: bool = True
    monte_carlo_engine: str = "numpy"
    monte_carlo_simulations: int = 10000
    digital_twins_enabled: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
