
# ------------------------
# 0️⃣ جلب كل الدكاترة
# ------------------------
def get_all_doctors(db: Session):
    doctors = db.query(Doctors).all()
    result = []
    for doctor in doctors:
        result.append({
            "id": doctor.id,
            "name": doctor.name,
            "specialty": doctor.specialty
        })
    return {"doctors": result}


# ------------------------
# 1️⃣ حجز موعد جديد
# ------------------------
def book_appointment(db: Session, user: Users, doctor_id: int, date_time: datetime, reason: str = None):
    # التحقق من وجود الدكتور
    doctor = db.query(Doctors).filter(Doctors.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # التحقق من التاريخ والوقت
    now = datetime.now()
    if date_time <= now:
        raise HTTPException(status_code=400, detail="Cannot book an appointment in the past")

    # التحقق من ساعات العمل
    if date_time.time() < time(10, 0) or date_time.time() > time(16, 0):
        raise HTTPException(status_code=400, detail="Appointment must be within working hours (10:00 - 16:00)")

    # التحقق من أيام العمل (Sunday=6, Monday=0 حسب التقويم العربي إذا تريد التغيير)
    weekday = date_time.weekday()  # 0=Monday ... 6=Sunday
    if weekday > 4:  # الجمعة=5، السبت=6
        raise HTTPException(status_code=400, detail="Appointments are only allowed from Sunday to Thursday")

    # التحقق من الدقائق (نصف ساعة فقط)
    if date_time.minute not in (0, 30):
        raise HTTPException(status_code=400, detail="Appointments must start at 00 or 30 minutes")

    # التحقق من التعارض
    conflict = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date_time == date_time,
        Appointment.status != "Cancelled"
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Doctor already has an appointment at this time")

    # إنشاء الموعد
    new_app = Appointment(
        user_id=user.id,
        doctor_id=doctor_id,
        date_time=date_time,
        reason=reason,
        status="Scheduled"
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)

    return new_app


# ------------------------
# 2️⃣ إلغاء موعد
# ------------------------
def cancel_appointment(db: Session, user: Users, appointment_id: int):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not allowed to cancel this appointment")

    if appointment.status == "Cancelled":
        raise HTTPException(status_code=400, detail="Appointment already cancelled")
#  مابقدر الغي موعد ان صاير قبل وقت قديم
    if appointment.date_time < datetime.now():
     raise HTTPException(status_code=400, detail="Cannot cancel a past appointment")

    appointment.status = "Cancelled"
    db.commit()
    db.refresh(appointment)

    return {"message": "Appointment cancelled successfully", "appointment_id": appointment.id}


# ------------------------
# 3️⃣ عرض كل مواعيد المريض
# ------------------------
def get_user_appointments(db: Session, user: Users):
    appointments = db.query(Appointment).filter(Appointment.user_id == user.id).all()
    if not appointments:
        return {"message": "No appointments found", "appointments": []}

    result = []
    for app in appointments:
        doctor = db.query(Doctors).filter(Doctors.id == app.doctor_id).first()
        doctor_name = doctor.name if doctor else "Unknown"

        result.append({
            "appointment_id": app.id,
            "doctor_name": doctor_name,
            "date_time": app.date_time.strftime("%Y-%m-%d %H:%M"),
            "status": app.status,
            "reason": getattr(app, "reason", None)
        })

    return {"appointments": result}
