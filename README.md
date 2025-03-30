# FMI Testbed radar integration for Home Assistant

FMI Testbed displays a radar map of rain around in Southern Finland. The integration creates a
camera image showing the latest radar map.

## Installation

### Option 1: by copying manually

1. Copy the `custom_components/fmi_testbed` folder to the `custom_components` directory in the Home
   Assistant config directory. If the `custom_components` directory doesn't exist, create it first.
2. Proceed to configuration (see the next section).

### Option 2: via Home Assistant Community Store

1. Go to **HACS**.
2. Click the three dots in the top-right corner and select **Custom repositories**.
3. Enter the repository `https://github.com/senarvi/fmi-testbed-home-assistant` and select
   **Integration** as the type. Then click **Add**.
4. Search for FMI Testbed in HACS and select the FMI Testbed integration.
5. Click **Download** and then confirm downloading the integration.
6. Proceed to configuration (see the next section).

## Configuration

### Enable the component

You can enable the component by adding the camera platform to `configuration.yaml`:

```yaml
camera:
  - platform: fmi_testbed
```

### Debug logging

Enable debug logging for the component by adding the following to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.fmi_testbed: debug
```

## Displaying the radar map in the Home Assistant UI

You can display the radar map using a picture entity or a picture glance card.

```yaml
type: picture-entity
entity: camera.fmi_testbed
show_name: true
show_state: false
```

![image](https://github.com/user-attachments/assets/3a0c48fc-4b6a-4e2b-8f3b-275c41b178cb)


