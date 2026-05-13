from collections import Counter

from sqlalchemy.orm import Session

from app.models import WeakTopic, utc_now


def update_weak_topics(db: Session, course_id: int, missed_topics: list[str]) -> None:
    counts = Counter(topic for topic in missed_topics if topic)
    now = utc_now()
    for topic, count in counts.items():
        weak_topic = (
            db.query(WeakTopic)
            .filter(WeakTopic.course_id == course_id, WeakTopic.topic == topic)
            .one_or_none()
        )
        if weak_topic is None:
            db.add(WeakTopic(course_id=course_id, topic=topic, miss_count=count, last_missed_at=now))
        else:
            weak_topic.miss_count += count
            weak_topic.last_missed_at = now
