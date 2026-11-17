# Helm Op Fluo Top for Home Assistant

Track your children's [Helm Op Fluo Top](https://helmopfluotop.vsv.be/beloningen) points, badges and reward vouchers in Home Assistant.

> **Unofficial.** This integration is not made or endorsed by the Vlaamse Stichting Verkeerskunde (VSV). It uses the same API as the public rewards page, which may change at any time.

## Features

One device per child, with three sensors:

| Sensor | State | Attributes |
|---|---|---|
| Points | Total points this school year | edition, school, class |
| Badges | Number of badges earned | list of badge titles and counts |
| Vouchers | Number of reward vouchers | voucher type and code |

Data refreshes every hour. When a code stops working (for example at the start of a new school year), Home Assistant asks you to enter the new code.

## Installation

### HACS

1. In HACS, open the menu → **Custom repositories**.
2. Add `https://github.com/bartverhavert/ha-helm-op-fluo-top` with type **Integration**.
3. Download **Helm Op Fluo Top** and restart Home Assistant.

### Manual

Copy `custom_components/helm_op_fluo_top` into your `config/custom_components/` folder and restart Home Assistant.

## Configuration

**Settings → Devices & services → Add integration → Helm Op Fluo Top**, then enter your child's code: the same one used on the rewards page. Repeat for each child.

## Example automation

Get notified when a new voucher arrives:

```yaml
automation:
  - alias: New Helm Op Fluo Top voucher
    triggers:
      - trigger: state
        entity_id: sensor.helm_op_fluo_top_jan_vouchers
    conditions:
      - "{{ trigger.from_state.state | int(0) < trigger.to_state.state | int(0) }}"
    actions:
      - action: notify.notify
        data:
          message: "New Helm Op Fluo Top voucher earned!"
```

## Privacy

- The code is the only thing needed to read a child's data, so treat it like a password. It is stored in Home Assistant's config entry, never in entity attributes.
- The API's badge data also lists classmates. This integration only requests their numeric ids and counts, so classmates' names never reach Home Assistant.

## License

MIT
