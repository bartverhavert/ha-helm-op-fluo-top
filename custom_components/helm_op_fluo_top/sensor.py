"""Sensors for Helm Op Fluo Top."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import PupilData
from .const import DOMAIN
from .coordinator import HoftConfigEntry, HoftCoordinator


@dataclass(frozen=True, kw_only=True)
class HoftSensorDescription(SensorEntityDescription):
    """Describes a Helm Op Fluo Top sensor."""

    value_fn: Callable[[PupilData], int]
    attrs_fn: Callable[[PupilData], dict[str, Any]] | None = None


SENSORS: tuple[HoftSensorDescription, ...] = (
    HoftSensorDescription(
        key="points",
        translation_key="points",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.points,
        attrs_fn=lambda d: {
            "edition": d.edition_name,
            "school": d.school,
            "class": d.class_name,
        },
    ),
    HoftSensorDescription(
        key="badges",
        translation_key="badges",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.badge_count,
        attrs_fn=lambda d: {
            "badges": [{"title": b.title, "count": b.count} for b in d.badges]
        },
    ),
    HoftSensorDescription(
        key="vouchers",
        translation_key="vouchers",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: len(d.vouchers),
        attrs_fn=lambda d: {"vouchers": d.vouchers},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HoftConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(HoftSensor(coordinator, desc) for desc in SENSORS)


class HoftSensor(CoordinatorEntity[HoftCoordinator], SensorEntity):
    """A single pupil statistic."""

    _attr_has_entity_name = True
    entity_description: HoftSensorDescription

    def __init__(
        self, coordinator: HoftCoordinator, description: HoftSensorDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Helm Op Fluo Top {entry.title}",
            manufacturer="Vlaamse Stichting Verkeerskunde",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://helmopfluotop.vsv.be/beloningen",
        )

    @property
    def native_value(self) -> int:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data)
