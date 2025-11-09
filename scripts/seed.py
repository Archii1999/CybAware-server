# scripts/seed.py
from pathlib import Path
import sys

# Projectroot toevoegen zodat imports werken
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import SessionLocal
from app import models
from app.security import hash_password  # jouw bestaande veilige functie

def main():
    db = SessionLocal()
    try:
        # 1) ORGANIZATION
        org = db.query(models.Organization).filter_by(slug="cybaware").first()
        if not org:
            org = models.Organization(name="CybAware Demo", slug="cybaware")
            db.add(org); db.flush()

        # 2) USERS
        def ensure_user(email, name, pwd):
            u = db.query(models.User).filter_by(email=email).first()
            if not u:
                u = models.User(email=email, name=name,
                                password_hash=hash_password(pwd),
                                is_active=True)
                db.add(u); db.flush()
            return u

        admin    = ensure_user("admin@demo.local",   "Admin Demo",   "Admin!123")
        manager  = ensure_user("manager@demo.local", "Manager Demo", "Manager!123")
        employee = ensure_user("employee@demo.local","Employee Demo","Employee!123")

        # 3) MEMBERSHIPS
        def ensure_member(user_id, org_id, role: models.Role):
            m = db.query(models.Membership).filter_by(user_id=user_id, org_id=org_id).first()
            if not m:
                m = models.Membership(user_id=user_id, org_id=org_id, role=role.value)
                db.add(m)
            return m

        ensure_member(admin.id,   org.id, models.Role.ADMIN)
        ensure_member(manager.id, org.id, models.Role.MANAGER)
        ensure_member(employee.id,org.id, models.Role.EMPLOYEE)

        # 4) COMPANY
        company = db.query(models.Company).filter_by(org_id=org.id, name="Zorggroep Noord").first()
        if not company:
            company = models.Company(
                org_id=org.id, name="Zorggroep Noord", kvk="12345678",
                sector="Zorg", email_domain="zorgnoord.nl", is_active=True
            )
            db.add(company)

        db.commit()
        print(f"✅ Seed klaar. org_id={org.id}")
        print("  admin@demo.local   / Admin!123   (ADMIN)")
        print("  manager@demo.local / Manager!123 (MANAGER)")
        print("  employee@demo.local/ Employee!123 (EMPLOYEE)")
    finally:
        db.close()

if __name__ == "__main__":
    main()
