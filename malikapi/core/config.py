from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class SourceConfig(BaseModel):
    type: Literal['oracle', 'postgresql']
    instance: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    table: str
    columns: List[str]
    delta_column: str
    key_columns: List[str]

class TargetConfig(BaseModel):
    type: Literal['oracle', 'postgresql']
    instance: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    table: str

class ErrorHandlingConfig(BaseModel):
    max_retries: int = 3
    retry_delay_seconds: int = 60
    on_error: Literal['log_and_skip', 'fail_job'] = 'log_and_skip'

class ReplicationSpec(BaseModel):
    id: str
    source: SourceConfig
    target: TargetConfig
    error_handling: ErrorHandlingConfig = Field(default_factory=ErrorHandlingConfig)

class ReplicationJobConfig(BaseModel):
    id: str
    description: Optional[str] = None
    enabled: bool = True
    mode: Literal['scheduled'] = 'scheduled'
    interval_seconds: int
    replications: List[ReplicationSpec]

class Config(BaseModel):
    replication_jobs: List[ReplicationJobConfig]

def load_config(filepath: str) -> Config:
    import yaml
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return Config(**data)
