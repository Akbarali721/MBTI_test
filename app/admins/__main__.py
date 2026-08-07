"""Admin hisoblarini buyruq satridan boshqarish.

python -m app.admins list
python -m app.admins create --username dilnoza --role moderator --telegram-id 123456
python -m app.admins set-password --username dilnoza
python -m app.admins set-role --username dilnoza --role viewer
python -m app.admins activate --username dilnoza
python -m app.admins deactivate --username dilnoza

Bu "break-glass" vosita: panelga kira olmay qolgan holatda (oxirgi egani o'chirib
qo'yish, parolni unutish) yagona yo'l shu. Parol argument sifatida emas, so'rov
orqali kiritiladi — aks holda u shell tarixida qolib ketardi.
"""

import argparse
import getpass
import sys

from sqlalchemy.orm import Session

from app.authz import ACTOR_CLI, AdminIdentity, role_label
from app.database import SessionLocal
from app.models.enums import AdminRole
from app.repositories.admin_repository import AdminRepository
from app.services import admin_service, audit_service

ROLE_CHOICES = [role.value for role in AdminRole]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.admins", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="Hisoblar ro'yxati")

    create = subparsers.add_parser("create", help="Yangi hisob")
    create.add_argument("--username", required=True)
    create.add_argument("--role", choices=ROLE_CHOICES, default=AdminRole.MODERATOR.value)
    create.add_argument("--telegram-id", type=int, default=None)

    password = subparsers.add_parser("set-password", help="Parolni almashtirish")
    password.add_argument("--username", required=True)

    role = subparsers.add_parser("set-role", help="Rolni o'zgartirish")
    role.add_argument("--username", required=True)
    role.add_argument("--role", choices=ROLE_CHOICES, required=True)

    for name, help_text in (("activate", "Hisobni yoqish"), ("deactivate", "Hisobni o'chirish")):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("--username", required=True)

    return parser


def _cli_actor() -> AdminIdentity:
    return AdminIdentity(username="cli", role=AdminRole.OWNER, actor_type=ACTOR_CLI)


def _ask_password() -> str:
    first = getpass.getpass("Yangi parol: ")
    second = getpass.getpass("Parolni takrorlang: ")
    if first != second:
        raise SystemExit("Parollar mos kelmadi")
    return first


def _list(db: Session) -> int:
    users = AdminRepository(db).list_users()
    if not users:
        print("Bazada admin hisobi yo'q")
        return 0
    for user in users:
        state = "faol" if user.is_active else "o'chirilgan"
        telegram = user.telegram_user_id or "—"
        print(f"{user.username:<24} {role_label(user.admin_role):<12} {state:<11} telegram={telegram}")
    return 0


def _require_user(db: Session, username: str):
    user = AdminRepository(db).get_by_username(username)
    if user is None:
        raise SystemExit(f"Hisob topilmadi: {username}")
    return user


def _run(db: Session, args: argparse.Namespace) -> int:
    actor = _cli_actor()

    if args.command == "list":
        return _list(db)

    if args.command == "create":
        result = admin_service.create_user(
            db,
            username=args.username,
            password=_ask_password(),
            role=AdminRole(args.role),
            telegram_user_id=args.telegram_id,
        )
        if not result.ok or result.user is None:
            raise SystemExit(result.error or "Yaratib bo'lmadi")
        audit_service.record(
            db,
            actor,
            audit_service.USER_CREATED,
            target_type="admin_user",
            target_id=result.user.id,
            detail={"login": result.user.username, "rol": args.role},
        )
        db.commit()
        print(f"Yaratildi: {result.user.username} ({args.role})")
        return 0

    user = _require_user(db, args.username)

    if args.command == "set-password":
        result = admin_service.set_password(db, user, _ask_password())
        action = audit_service.USER_PASSWORD_CHANGED
        message = f"{user.username}: parol almashtirildi"
    elif args.command == "set-role":
        result = admin_service.set_role(db, user, AdminRole(args.role), actor=actor)
        action = audit_service.USER_ROLE_CHANGED
        message = f"{user.username}: rol -> {args.role}"
    else:
        wanted = args.command == "activate"
        result = admin_service.set_active(db, user, wanted, actor=actor)
        action = audit_service.USER_ACTIVATED if wanted else audit_service.USER_DEACTIVATED
        message = f"{user.username}: {'yoqildi' if wanted else 'o‘chirildi'}"

    if not result.ok:
        raise SystemExit(result.error or "Bajarib bo'lmadi")
    audit_service.record(
        db, actor, action, target_type="admin_user", target_id=user.id, detail={"login": user.username}
    )
    db.commit()
    print(message)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    db = SessionLocal()
    try:
        return _run(db, args)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
