from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course, ScheduleItem, utc_now
from app.schemas import ScheduleItemCreate, ScheduleItemOut, ScheduleItemUpdate, ScheduleItemWithCourseOut

router = APIRouter(tags=["schedule"])


def _schedule_item_or_404(db: Session, item_id: int) -> ScheduleItem:
    item = db.get(ScheduleItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule item not found")
    return item


def _schedule_item_with_course_out(item: ScheduleItem) -> ScheduleItemWithCourseOut:
    return ScheduleItemWithCourseOut(
        **ScheduleItemOut.model_validate(item).model_dump(),
        course_title=item.course.title,
    )


@router.post("/courses/{course_id}/schedule", response_model=ScheduleItemOut, status_code=status.HTTP_201_CREATED)
def create_schedule_item(course_id: int, payload: ScheduleItemCreate, db: Session = Depends(get_db)) -> ScheduleItem:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    item = ScheduleItem(
        course_id=course_id,
        title=payload.title,
        event_type=payload.event_type,
        due_at=payload.due_at,
        notes=payload.notes,
        reminder_minutes_before=payload.reminder_minutes_before,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/courses/{course_id}/schedule", response_model=list[ScheduleItemOut])
def list_course_schedule(
    course_id: int,
    include_completed: bool = True,
    db: Session = Depends(get_db),
) -> list[ScheduleItem]:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    query = db.query(ScheduleItem).filter(ScheduleItem.course_id == course_id)
    if not include_completed:
        query = query.filter(ScheduleItem.is_completed.is_(False))
    return query.order_by(ScheduleItem.is_completed.asc(), ScheduleItem.due_at.asc()).all()


@router.get("/schedule", response_model=list[ScheduleItemWithCourseOut])
def list_global_schedule(
    include_completed: bool = False,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[ScheduleItemWithCourseOut]:
    query = db.query(ScheduleItem).join(Course, ScheduleItem.course_id == Course.id)
    if not include_completed:
        query = query.filter(ScheduleItem.is_completed.is_(False))
    items = query.order_by(ScheduleItem.is_completed.asc(), ScheduleItem.due_at.asc()).limit(max(1, min(limit, 100))).all()
    return [_schedule_item_with_course_out(item) for item in items]


@router.get("/schedule/{item_id}", response_model=ScheduleItemOut)
def get_schedule_item(item_id: int, db: Session = Depends(get_db)) -> ScheduleItem:
    return _schedule_item_or_404(db, item_id)


@router.patch("/schedule/{item_id}", response_model=ScheduleItemOut)
def update_schedule_item(item_id: int, payload: ScheduleItemUpdate, db: Session = Depends(get_db)) -> ScheduleItem:
    item = _schedule_item_or_404(db, item_id)
    if payload.title is not None:
        item.title = payload.title
    if payload.event_type is not None:
        item.event_type = payload.event_type
    if payload.due_at is not None:
        item.due_at = payload.due_at
    if "notes" in payload.model_fields_set:
        item.notes = payload.notes
    if "reminder_minutes_before" in payload.model_fields_set:
        item.reminder_minutes_before = payload.reminder_minutes_before
    if payload.is_completed is not None:
        item.is_completed = payload.is_completed
        item.completed_at = utc_now() if payload.is_completed else None

    db.commit()
    db.refresh(item)
    return item


@router.delete("/schedule/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule_item(item_id: int, db: Session = Depends(get_db)) -> None:
    item = _schedule_item_or_404(db, item_id)
    db.delete(item)
    db.commit()
