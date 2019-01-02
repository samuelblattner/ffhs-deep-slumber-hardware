from unittest import TestCase

from datetime import datetime

from outpost.message import Settings
from risenshine.risenshine import RiseNShine
from risenshine.waking import WakeTimerThread


class TestRiseNShine(TestCase):

    # Expected Waking Times
    # Pattern: ( (LATEST_HOUR, LATEST_MINUTE), (EXP_DECISION_HOUR, EXP_DECISION_MINUTE, EXP_DAY_DELTA) )
    WAKE_TIMES = (
        ((6, 15), (4, 45, 0)),
        ((12, 0), (10, 30, 0)),
        ((0, 5), (22, 35, 1))
    )

    def test_correct_decision_time(self):
        """
        ATC-0001: Test if decision time for waking process is calculated correctly.
        """

        time = datetime.now()
        risenshine = RiseNShine(None, None)

        for wake_time, exp_decision_time in self.WAKE_TIMES:
            settings = Settings()
            settings.wakeMaxSpan = 5400
            settings.latestWakeTime = time.replace(hour=wake_time[0], minute=wake_time[1])

            # Pass settings to RiseNShine
            risenshine.on_message(settings)

            # For the sake of correct assertions below, we need to place the latest waking time
            # one day into the future manually (=tomorrow) since we created the time using now().
            # This step is also done within the mechanics of RiseNShine when calculating the decision time
            placed_ahead_latest_wake_time = WakeTimerThread.place_waketime_ahead(settings.latestWakeTime)
            decision_time = risenshine.get_decision_time()

            exp_decision_day = 0 if decision_time.day in (30, 31) and placed_ahead_latest_wake_time.day == 1 else decision_time.day

            self.assertEqual(exp_decision_time[0], decision_time.hour)
            self.assertEqual(exp_decision_time[1], decision_time.minute)
            self.assertEqual(exp_decision_time[2], placed_ahead_latest_wake_time.day - exp_decision_day)
