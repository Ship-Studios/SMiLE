"""RegistrationReport.__repr__ implementation. Attached to the
RegistrationReport class in registration_report.py."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from smile.capabilities.registration_report import RegistrationReport


def registration_report_repr(self: "RegistrationReport") -> str:
    return f"RegistrationReport(registered={len(self.registered)}, skipped={len(self.skipped)})"
