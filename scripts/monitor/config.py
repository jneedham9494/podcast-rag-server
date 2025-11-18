"""
Configuration constants for the monitor package.
"""

# Worker targets
TARGET_DOWNLOADERS = 30
TARGET_TRANSCRIBERS = 6  # Adjusted for system capacity
TARGET_ENRICHERS = 20  # Enrichment is IO-bound, can run many

# Timing
REFRESH_INTERVAL = 10  # seconds between dashboard updates

# Stall detection
STALL_THRESHOLD = 5  # Consider feed stalled after N cycles with no progress

# Worker allocation
MIN_EPISODES_FOR_MULTIPLE_WORKERS = 50  # Feeds with 50+ remaining episodes get multiple workers

# Manual failover
MANUAL_FAILOVER_THRESHOLD = 3  # After this many failures, switch to manual mode

# Patreon backoff defaults
PATREON_BASE_DELAY = 60  # Start with 60 second delay
PATREON_MAX_DELAY = 1800  # Cap at 30 minutes
