import enum


class TargetType(enum.Enum):
    REPOSITORY = "repository"
    USER = "user"


class TargetSpec:
    target_type: TargetType
    username: str = None
    repo_name: str = None

    def __init__(self, target_type: TargetType, username: str = None, repo_name: str = None):
        self.target_type = target_type
        self.username = username
        self.repo_name = repo_name

    def repo_full_name(self) -> str:
        if self.target_type == TargetType.REPOSITORY and self.username and self.repo_name:
            return f"{self.username}/{self.repo_name}"
        raise ValueError("Target is not a repository or missing username/repo_name")

    def __repr__(self):
        if self.target_type == TargetType.REPOSITORY:
            return f"GitHub repository {self.repo_full_name()}"
        elif self.target_type == TargetType.USER:
            return f"GitHub user {self.username}"
        return None
