"""Centrale auditregistry: allowlist van uitvoerbare audits.

Alleen audits die hier geregistreerd zijn, kunnen vanuit Django Admin of
via de centrale runner worden gestart — nooit arbitraire commandnamen uit
requestparameters.
"""

from dataclasses import dataclass, field
from typing import Callable

#: Snelheidsklassen (spec §9). Netwerkafhankelijke audits zijn niet
#: geschikt voor directe adminuitvoering.
SPEED_QUICK = "quick"
SPEED_STANDARD = "standard"
SPEED_LONG_RUNNING = "long_running"
SPEED_NETWORK = "network_dependent"


@dataclass(frozen=True)
class AuditDefinition:
    key: str
    title: str
    description: str
    #: runner(category: str | None, params: dict) -> list[AuditIssue], dict
    runner: Callable | None
    supports_category: bool = False
    uses_network: bool = False
    speed: str = SPEED_QUICK
    #: Vereiste Django-permissie om deze audit te starten.
    required_permission: str = "audits.run_product_audits"
    #: Alleen audits met een runner zijn vanuit admin uitvoerbaar; audits
    #: zonder runner (netwerk/lang) tonen een commandline-instructie.
    cli_hint: str = ""
    categories: tuple = field(default=())

    @property
    def admin_runnable(self):
        return self.runner is not None and not self.uses_network


_REGISTRY: dict[str, AuditDefinition] = {}


def register_audit(**kwargs):
    definition = AuditDefinition(**kwargs)
    if definition.key in _REGISTRY:
        raise ValueError(f"Audit '{definition.key}' is al geregistreerd")
    _REGISTRY[definition.key] = definition
    return definition


def get_audit(key):
    return _REGISTRY.get(key)


def all_audits():
    return list(_REGISTRY.values())
