"""Minimal AWS Strands Agent Example.

This is a minimal example of an AWS Strands agent using Anthropic Claude Sonnet 4.
The agent is kept simple without A2A protocol support for basic framework detection.
"""

from .agent import root_agent

__all__ = ["root_agent"]