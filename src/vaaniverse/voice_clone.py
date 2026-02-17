from pathlib import Path
from .consent import verify_consent_for_sample


class ConsentError(Exception):
    pass


def clone_voice(sample_path: str, output_name: str, consent: bool = False) -> str:
    """Placeholder for voice cloning.

    For safety and legality, this function requires explicit consent. Consent
    can be provided directly via `consent=True` or via a recorded consent
    artifact created by `vaaniverse.consent.make_consent` which `verify_consent_for_sample`
    will validate.
    """
    sample = Path(sample_path)
    if not sample.exists():
        raise FileNotFoundError("Sample file not found: %s" % sample_path)

    # If consent flag not set, check recorded consent artifact
    if not consent:
        ok = verify_consent_for_sample(str(sample))
        if not ok:
            raise ConsentError("Explicit consent is required to clone a voice. Provide consent=True or record consent via the web UI.")

    out = Path(f"{output_name}.voice.txt")
    out.write_text("placeholder: cloned voice metadata for %s" % sample.name)
    return str(out)
