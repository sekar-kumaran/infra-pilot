from pydantic import BaseModel

class DockerContainerTarget(BaseModel):
    container_id: str

class DockerLogParams(BaseModel):
    max_lines: int = 100
