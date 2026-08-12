"""RegistrationReport.summary implementation. Attached to the
RegistrationReport class in registration_report.py."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from smile.capabilities.registration_report import RegistrationReport


def registration_report_summary(self: "RegistrationReport") -> str:
    lines = [f"Registered {len(self.registered)} capabilities: {self.registered}"]
    if self.skipped:
        lines.append(f"Skipped {len(self.skipped)}:")
        for name, reason in self.skipped:
            lines.append(f"  - {name}: {reason}")
    return "\n".join(lines)
