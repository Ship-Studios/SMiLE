"""RegistrationReport: result of a bulk registration call.

Field declarations only -- its __repr__ and summary methods are defined
in their own files and attached below, per the project's one-def-per-file
rule.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from smile.capabilities.registration_report_repr import registration_report_repr
from smile.capabilities.registration_report_summary import registration_report_summary


@dataclass
class RegistrationReport:
    """Result of a bulk registration call (register_module/register_class):
    what made it in, and what didn't and why. Bulk-wrapping existing code
    routinely hits functions/methods that were never meant to be
    capabilities -- this makes that visible instead of silent."""

    registered: list[str] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)  # (name, reason)


RegistrationReport.__repr__ = registration_report_repr
RegistrationReport.summary = registration_report_summary
