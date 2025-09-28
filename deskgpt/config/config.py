"""
Configuration management for DeskGPT
"""
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class BrowserConfig(BaseModel):
    headless: bool = False
    timeout: int = 30000
    viewport_width: int = 1920
    viewport_height: int = 1080


class LoggingConfig(BaseModel):
    level: str = "INFO"


class Config(BaseModel):
    openai_api_key: str
    browser: BrowserConfig = BrowserConfig()
    logging: LoggingConfig = LoggingConfig()

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables"""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            browser=BrowserConfig(
                headless=os.getenv("NODE_ENV") == "production",
                timeout=int(os.getenv("BROWSER_TIMEOUT", "30000")),
                viewport_width=int(os.getenv("VIEWPORT_WIDTH", "1920")),
                viewport_height=int(os.getenv("VIEWPORT_HEIGHT", "1080"))
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO")
            )
        )


def validate_config(config: Config) -> None:
    """Validate configuration"""
    if not config.openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")


# Global config instance
config = Config.from_env()