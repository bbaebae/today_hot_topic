from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"

    # Toss mTLS
    toss_api_base_url: str = "https://apps-in-toss-api.toss.im"
    toss_mtls_cert_path: str = "certs/todayhottopic_public.crt"
    toss_mtls_key_path: str = "certs/todayhottopic_private.key"
    toss_app_id: str = "today-hot-topic"
    toss_promotion_code: str = ""  # 앱인토스 콘솔에서 발급받은 프로모션 코드

    # Auth (서버 세션용 JWT — Toss accessToken과 별개)
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 3600  # 1시간 (Toss accessToken 만료 주기에 맞춤)

    # Point policy
    vote_reward_amount: int = 10
    ad_reward_amount: int = 20
    share_reward_amount: int = 5
    daily_point_limit: int = 100

    # Naver Search API
    naver_client_id: str
    naver_client_secret: str

    # Crawler
    crawler_interval_minutes: int = 30
    crawler_max_topics_per_source: int = 20

    # CORS
    allowed_origins: list[str] = ["*"]


settings = Settings()
