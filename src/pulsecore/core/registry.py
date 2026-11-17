
from typing import Any
from pydantic import BaseModel, Field


class ModuleManifest(BaseModel):
    """Describes an application module registered with PulseCore."""

    module_id: str
    name: str
    version: str
    domain: str
    description: str = ""
    supported_entity_types: list[str] = Field(default_factory=list)


class ModuleRegistry:
    """Registers and manages application modules."""

    def __init__(self):
        self._modules: dict[str, Any] = {}

    def register(self, module: Any) -> ModuleManifest:
        manifest = getattr(module, "manifest", None)

        if not isinstance(manifest, ModuleManifest):
            raise ValueError(
                "Module must provide a valid ModuleManifest."
            )

        if manifest.module_id in self._modules:
            raise ValueError(
                f"Module '{manifest.module_id}' is already registered."
            )

        self._modules[manifest.module_id] = module

        return manifest

    def get(self, module_id: str) -> Any:
        if module_id not in self._modules:
            raise KeyError(f"Module '{module_id}' not found.")

        return self._modules[module_id]

    def list_modules(self) -> list[ModuleManifest]:
        return [
            module.manifest
            for module in self._modules.values()
        ]

    def unregister(self, module_id: str) -> None:
        if module_id not in self._modules:
            raise KeyError(f"Module '{module_id}' not found.")

        del self._modules[module_id]
