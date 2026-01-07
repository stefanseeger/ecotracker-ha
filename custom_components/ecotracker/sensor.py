"""Sensor platform for Ecotracker integration."""
from __future__ import annotations

from datetime import timedelta
import logging

import aiohttp
import async_timeout

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_IP_ADDRESS,
    UnitOfPower,
    UnitOfEnergy,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 5


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ecotracker sensors based on a config entry."""
    ip_address = entry.data[CONF_IP_ADDRESS]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    
    url = f"http://{ip_address}/v1/json"
    
    session = async_get_clientsession(hass)
    coordinator = EcotrackerCoordinator(hass, session, url, scan_interval)
    
    await coordinator.async_config_entry_first_refresh()
    
    entities = [
        EcotrackerPowerSensor(coordinator, entry),
        EcotrackerPowerPhase1Sensor(coordinator, entry),
        EcotrackerPowerPhase2Sensor(coordinator, entry),
        EcotrackerPowerPhase3Sensor(coordinator, entry),
        EcotrackerPowerAvgSensor(coordinator, entry),
        EcotrackerEnergyInSensor(coordinator, entry),
        EcotrackerEnergyOutSensor(coordinator, entry),
    ]
    
    async_add_entities(entities)


class EcotrackerCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Ecotracker data."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        session: aiohttp.ClientSession, 
        url: str,
        scan_interval: int
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.session = session
        self.url = url

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(10):
                async with self.session.get(self.url) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Error fetching data: HTTP {response.status}")
                    data = await response.json()
                    
                    if not all(key in data for key in ["power", "powerPhase1", "powerPhase2", "powerPhase3", "powerAvg", "energyCounterIn", "energyCounterOut"]):
                        raise UpdateFailed("Missing required keys in response")
                    
                    return data
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}")


class EcotrackerSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Ecotracker sensors."""

    def __init__(self, coordinator: EcotrackerCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Ecotracker",
            manufacturer="Ecotracker",
            model="Energy Monitor",
        )


class EcotrackerPowerSensor(EcotrackerSensorBase):
    """Representation of Ecotracker Power Sensor."""

    def __init__(self, coordinator: EcotrackerCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = "Power"
        self._attr_unique_id = f"{entry.entry_id}_power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("power")


class EcotrackerPowerPhase1Sensor(EcotrackerSensorBase):
    """Representation of Ecotracker Power Phase 1 Sensor."""

    def __init__(self, coordinator: EcotrackerCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = "Power Phase 1"
        self._attr_unique_id = f"{entry.entry_id}_power_phase1"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("powerPhase1")


class EcotrackerPowerPhase2Sensor(EcotrackerSensorBase):
    """Representation of Ecotracker Power Phase 2 Sensor."""

    def __init__(self, coordinator: EcotrackerCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = "Power Phase 2"
        self._attr_unique_id = f"{entry.entry_id}_power_phase2"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("powerPhase2")


class EcotrackerPowerPhase3Sensor(EcotrackerSensorBase):
    """Representation of Ecotracker Power Phase 3 Sensor."""

    def __init__(self, coordinator: EcotrackerCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = "Power Phase 3"
        self._attr_unique_id = f"{entry.entry_id}_power_phase3"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("powerPhase3")


class EcotrackerPowerAvgSensor(EcotrackerSensorBase):
    """Representation of Ecotracker Power Average Sensor."""

    def __init__(self, coordinator: EcotrackerCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = "Power Average"
        self._attr_unique_id = f"{entry.entry_id}_power_avg"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("powerAvg")


class EcotrackerEnergyInSensor(EcotrackerSensorBase):
    """Representation of Ecotracker Energy Counter In Sensor."""

    def __init__(self, coordinator: EcotrackerCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = "Energy In"
        self._attr_unique_id = f"{entry.entry_id}_energy_in"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("energyCounterIn")


class EcotrackerEnergyOutSensor(EcotrackerSensorBase):
    """Representation of Ecotracker Energy Counter Out Sensor."""

    def __init__(self, coordinator: EcotrackerCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = "Energy Out"
        self._attr_unique_id = f"{entry.entry_id}_energy_out"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("energyCounterOut")