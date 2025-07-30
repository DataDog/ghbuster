import sys
from typing import List

from . import TargetSpec
from .heuristics.base import HeuristicRunResult


class Color:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    @staticmethod
    def disable_if_not_tty():
        """Disable colors if output is not a TTY (e.g., piped to file)"""
        if not sys.stdout.isatty():
            Color.RED = Color.GREEN = Color.YELLOW = Color.BLUE = ''
            Color.MAGENTA = Color.CYAN = Color.WHITE = Color.BOLD = ''
            Color.UNDERLINE = Color.END = ''

class OutputFormatter:
    """Rich output formatter for heuristic scan results"""
    
    def __init__(self, disable_colors: bool = False):
        if disable_colors:
            Color.disable_if_not_tty()
    
    def format_results(self, target_spec: TargetSpec, results: List[HeuristicRunResult]) -> str:
        """Format all heuristic results into a nice report"""
        Color.disable_if_not_tty()
        
        output = []
        
        # Header
        output.append(self._create_header(target_spec))
        output.append("")

        # Separate passed and failed results
        failed_results = [r for r in results if r.triggered]
        passed_results = [r for r in results if not r.triggered]
        
        # Failed heuristics section (show first if any)
        if failed_results:
            output.append(self._create_failed_section(failed_results))
            output.append("")
        
        # Passed heuristics section
        if passed_results:
            output.append(self._create_passed_section(passed_results))
            output.append("")
        
        # Summary
        output.append(self._create_summary(len(failed_results), len(passed_results)))
        
        return "\n".join(output)
    
    def _create_header(self, target_spec: TargetSpec) -> str:
        """Create formatted header section"""
        title = f"🔍 ghbuster scan results"
        target_info = f"Target: {target_spec}"
        
        border = "=" * max(len(title), len(target_info)) 
        
        return f"{Color.BOLD}{Color.CYAN}{border}{Color.END}\n" \
               f"{Color.BOLD}{Color.WHITE}{title}{Color.END}\n" \
               f"{Color.CYAN}{target_info}{Color.END}\n" \
               f"{Color.CYAN}{border}{Color.END}"
    
    def _create_failed_section(self, failed_results: List[HeuristicRunResult]) -> str:
        """Create section for failed heuristics"""
        lines = []
        
        # Section header
        count = len(failed_results)
        lines.append(f"{Color.BOLD}{Color.RED}🚨 {count} heuristics triggered{Color.END}")
        lines.append("")
        
        # Individual failed heuristics
        for i, result in enumerate(failed_results, 1):
            lines.append(self._format_failed_heuristic(i, result))
            if i < len(failed_results):
                lines.append("")  # Add spacing between heuristics
        
        return "\n".join(lines)
    
    def _create_passed_section(self, passed_results: List[HeuristicRunResult]) -> str:
        """Create section for passed heuristics"""
        lines = []
        
        # Section header
        lines.append(f"{Color.BOLD}{Color.GREEN}Non-triggered heuristics ({len(passed_results)}){Color.END}")
        lines.append("")
        
        # Show passed heuristics in a compact format
        for result in passed_results:
            heuristic_name = result.heuristic.friendly_name()
            lines.append(f"  {Color.GREEN}✅{Color.END} {heuristic_name}")
        
        return "\n".join(lines)
    
    def _format_failed_heuristic(self, index: int, result: HeuristicRunResult) -> str:
        """Format a single failed heuristic with details"""
        heuristic_name = result.heuristic.friendly_name()
        
        lines = []
        lines.append(f"{Color.BOLD}{Color.RED}❌ {index}. {heuristic_name}{Color.END}")

        description = result.heuristic.description()
        lines.append(f"   {Color.YELLOW}📋 Description:{Color.END} {description}")
        
        # Additional details
        if result.additional_details:
            lines.append(f"   {Color.CYAN}🔍 Details:{Color.END} {result.additional_details}")
        
        return "\n".join(lines)
    
    def _create_summary(self, failed_count: int, passed_count: int) -> str:
        """Create summary section"""
        total = failed_count + passed_count
        
        lines = []
        lines.append(f"{Color.BOLD}{Color.CYAN}📊 SCAN SUMMARY{Color.END}")
        lines.append("─" * 40)
        lines.append(f"Total Heuristics Run: {Color.BOLD}{total}{Color.END}")
        lines.append(f"Heuristics triggered:     {Color.BOLD}{Color.RED if failed_count > 0 else Color.GREEN}{failed_count}{Color.END}")
        
        return "\n".join(lines)
    
    def _camel_to_title(self, camel_str: str) -> str:
        """Convert CamelCase to Title Case with spaces"""
        import re
        # Insert space before uppercase letters (except first)
        spaced = re.sub(r'(?<!^)(?=[A-Z])', ' ', camel_str)
        # Remove common suffixes
        spaced = spaced.replace(' Heuristic', '').replace(' Metadata', '')
        return spaced 