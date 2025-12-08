# test_chrome_min.py
import pytest

pytest.importorskip("selenium")

from libot.recorder import record_task


def main():
    record_task(
        meeting_url="https://teams.microsoft.com/l/meetup-join/19%3ameeting_MTVjNjNlNGQtYWJhZi00ODNjLWIwOTEtZWFmYmM5NWJhNGVl%40thread.v2/0?context=%7b%22Tid%22%3a%2234ff9106-4c49-4535-98fa-c6566a9218f8%22%2c%22Oid%22%3a%22619a0a3b-ad73-47cd-b36b-07e588d11db1%22%7d",
        max_duration=50,
        task_id="test-session",
        record_audio=False,
        record_video=False,
    )


if __name__ == "__main__":
    main()
