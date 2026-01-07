# Ecotracker Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Custom integration for Ecotracker energy monitoring device.

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS:
   - Go to HACS > Integrations
   - Click the three dots in the top right
   - Select "Custom repositories"
   - Add the repository URL and select "Integration" as the category
2. Click "Install"
3. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/ecotracker` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings > Devices & Services
2. Click "+ Add Integration"
3. Search for "Ecotracker"
4. Enter your device's IP address
5. Set the polling interval (default: 5 seconds, range: 1-3600 seconds)

### Changing Settings

To change the polling interval after setup:
1. Go to Settings > Devices & Services
2. Find your Ecotracker device
3. Click "Configure"
4. Update the polling interval as needed

## Features

- Configurable polling interval (1-3600 seconds, default: 5 seconds)
- Three sensors:
  - Power (W)
  - Energy In (kWh)
  - Energy Out (kWh)
- Compatible with Home Assistant Energy Dashboard
- Config flow UI for easy setup
- Options flow for changing settings without re-adding the integration

## Sensors

- `sensor.ecotracker_power` - Current power consumption in Watts
- `sensor.ecotracker_energy_in` - Total energy imported in kWh
- `sensor.ecotracker_energy_out` - Total energy exported in kWh