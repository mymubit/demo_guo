from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class MonitoringAnonThrottle(AnonRateThrottle):
    scope = "monitoring_anon"


class MonitoringUserThrottle(UserRateThrottle):
    scope = "monitoring_user"
