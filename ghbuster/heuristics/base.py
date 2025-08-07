from abc import ABC, abstractmethod

import github

from .. import TargetType, TargetSpec


class HeuristicRunResult:
    def __init__(self, triggered: bool, additional_details: str = "", heuristic: 'MetadataHeuristic' = None,
                 skipped: bool = False):
        self.triggered = triggered
        self.additional_details = additional_details
        self.heuristic = heuristic
        self.skipped = skipped

    @staticmethod
    def TRIGGERED(additional_details: str = "") -> 'HeuristicRunResult':
        return HeuristicRunResult(triggered=True, additional_details=additional_details)

    @staticmethod
    def PASSED(additional_details: str = "") -> 'HeuristicRunResult':
        return HeuristicRunResult(triggered=False)

    @staticmethod
    def SKIPPED() -> 'HeuristicRunResult':
        return HeuristicRunResult(triggered=False, skipped=True)


class MetadataHeuristic(ABC):
    @abstractmethod
    def run(self, github_client: github.Github, target_spec: TargetSpec) -> HeuristicRunResult:
        """
        Run the heuristic against the provided GitHub client and repository URL.

        :param github_client: An authenticated GitHub client.
        :param target_spec: The target specification containing the type and details of the target (user or repository).
        """
        pass

    @abstractmethod
    def target_type(self) -> TargetType:
        """
        Return the type of target this heuristic is designed for.
        """
        pass

    @abstractmethod
    def id(self) -> str:
        pass

    @abstractmethod
    def friendly_name(self) -> str:
        pass

    @abstractmethod
    def description(self) -> str:
        pass
