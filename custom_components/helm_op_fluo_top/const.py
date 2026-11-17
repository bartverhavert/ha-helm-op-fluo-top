"""Constants for the Helm Op Fluo Top integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "helm_op_fluo_top"

CONF_CODE: Final = "code"

API_URL: Final = "https://graphql.vsv.be/hoft/api/graphql"

UPDATE_INTERVAL: Final = timedelta(hours=1)
