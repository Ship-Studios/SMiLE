# RegistrationReport

::: smile.capabilities.registration_report.RegistrationReport
    options:
      show_bases: false
      members: false

Returned by every bulk registration path (`register_module`,
`register_class`, `collect`): what made it in, and what didn't and why.
Bulk-wrapping existing code routinely hits functions/methods that were
never meant to be capabilities — this makes that visible instead of silent.

## `summary`

::: smile.capabilities.registration_report_summary.registration_report_summary
    options:
      show_root_heading: false
      show_root_toc_entry: false
      heading_level: 3
