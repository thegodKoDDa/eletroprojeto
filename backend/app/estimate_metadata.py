"""Versioned estimate provenance; no dependency on normative documents."""

import hashlib

from .version import ENGINE_VERSION


def revision():
    return hashlib.sha256(("residential-estimates-" + ENGINE_VERSION).encode()).hexdigest()


def snapshot():
    return {"scope": "residential_energy_estimates", "engine_version": ENGINE_VERSION}
