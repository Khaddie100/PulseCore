
from pulsecore.core.registry import ModuleManifest


class WardPulseModule:

    manifest = ModuleManifest(
        module_id="wardpulse",
        name="WardPulse",
        version="0.1.0",
        domain="healthcare_workforce_operations",
        description=(
            "Healthcare workforce wellbeing and "
            "operational early warning application."
        ),
        supported_entity_types=[
            "facility",
            "department",
            "healthcare_worker"
        ]
    )
