from django.utils import timezone

import datetime


def turn_back_time(minutes):
    return timezone.now() - datetime.timedelta(minutes=minutes)
