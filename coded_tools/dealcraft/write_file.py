"""
write_file.py — DealCraft re-export of the sdlc_pipeline WriteFile coded tool.
Uses sly_data["project_folder"] as the root directory for all writes.
"""
from coded_tools.sdlc_pipeline.write_file import WriteFile  # noqa: F401

__all__ = ["WriteFile"]
