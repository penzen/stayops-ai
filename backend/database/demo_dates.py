from datetime import datetime, timedelta


def get_active_demo_window() -> tuple[str, str]:
    """
    Return a demo stay window that always contains the current time.

    The booking starts one day before the database is seeded and
    ends one day after it is seeded.
    """

    now = datetime.now().replace(microsecond=0)

    check_in = now - timedelta(days=1)
    check_out = now + timedelta(days=1)

    return (
        check_in.isoformat(sep=" "),
        check_out.isoformat(sep=" "),
    )