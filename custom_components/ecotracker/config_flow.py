from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ecotracker"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 5

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=3600)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    ip_address = data[CONF_IP_ADDRESS]
    
    url = f"http://{ip_address}"

    session = async_get_clientsession(hass)
    
    try:
        async with async_timeout.timeout(10):
            async with session.get(url) as response:
                if response.status != 200:
                    raise CannotConnect(f"HTTP {response.status}")
                
                json_data = await response.json()
                
                # Validate required keys
                if not all(key in json_data for key in ["power", "energyCounterIn", "energyCounterOut"]):
                    raise InvalidData("Missing required keys in JSON response")
                
    except aiohttp.ClientError as err:
        raise CannotConnect(f"Connection error: {err}")
    except Exception as err:
        raise CannotConnect(f"Unexpected error: {err}")

    return {"title": f"Ecotracker ({ip_address})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ecotracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidData:
                errors["base"] = "invalid_data"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Ecotracker."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update config entry with new data
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input}
            )
            return self.async_create_entry(title="", data={})

        current_interval = self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=3600)
                    ),
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidData(HomeAssistantError):
    """Error to indicate invalid data received."""


# ==== File: custom_components/ecotracker/sensor.py ====
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
    
    url = f"http://{ip_address}"
    
    session = async_get_clientsession(hass)
    coordinator = EcotrackerCoordinator(hass, session, url, scan_interval)
    
    await coordinator.async_config_entry_first_refresh()
    
    entities = [
        EcotrackerPowerSensor(coordinator, entry),
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
                    
                    if not all(key in data for key in ["power", "energyCounterIn", "energyCounterOut"]):
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


class EcotrackerEnergyInSensor(EcotrackerSensorBase):
    """Representation of Ecotracker Energy Counter In Sensor."""

    def __init__(self, coordinator: EcotrackerCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_name = "Energy In"
        self._attr_unique_id = f"{entry.entry_id}_energy_in"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

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
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("energyCounterOut")