"""Registro local de perfiles de presentación confiables."""

from copy import deepcopy
from types import MappingProxyType

from .core import PresentationSpec


class PresentationRegistry:
    """Perfiles instalados por el cliente; nunca se cargan desde la solicitud."""

    def __init__(self, profiles=None):
        profiles = dict(profiles or {})
        if any(not isinstance(value, PresentationSpec) or value.profile is not None
               for value in profiles.values()):
            raise ValueError("invalid presentation registry")
        self._profiles = MappingProxyType(profiles)

    def resolve(self, request):
        requested = request.presentation
        if isinstance(requested, str):
            return PresentationSpec(mode=requested)
        requested.validate_fields(field.name for field in request.fields)
        if requested.profile is None:
            return deepcopy(requested)
        template = self._profiles.get(requested.profile)
        if template is None:
            raise ValueError("unknown presentation profile")
        template.validate_fields(field.name for field in request.fields)
        return deepcopy(template)
