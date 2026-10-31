"""Square dance module level classifier.

Detects the dance program level (Mainstream / Plus / A1 / A2) of an Obsidian
choreography-module markdown file by recognizing the calls in its body against
the authoritative CALLERLAB lists effective 2026-09-01, then:

  * fills in a missing ``level`` and moves the file to the matching level folder,
  * or flags modules whose detected level disagrees with their set ``level`` for
    the user to confirm.

Standalone tool; independent of square-modules/sd-choreo-importer.
"""
