"""Ma'lumotlarni saqlash siyosati.

python -m app.retention                      nima o'chirilishini ko'rsatadi (hech narsa o'zgarmaydi)
python -m app.retention --apply              siyosatni bajaradi
python -m app.retention --apply --rule visited --rule outbox   faqat tanlangan qoidalar
python -m app.retention --apply --max-rows 5000                bitta yurishdagi chegara

Standart rejim ATAYLAB "quruq": bu buyruq cron'dan ishlaydi va tasodifan
o'chirib yuborish eng qimmat xato bo'lardi.
"""

import argparse
import sys

from sqlalchemy.orm import Session

from app.authz import ACTOR_CLI, AdminIdentity
from app.database import SessionLocal
from app.models.enums import AdminRole
from app.services import retention_service
from app.services.retention_service import RULE_LABELS, RULE_ORDER, RetentionReport


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.retention", description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Haqiqatan bajaradi (standart holatda faqat hisobot ko'rsatiladi)",
    )
    parser.add_argument(
        "--rule",
        action="append",
        choices=list(RULE_ORDER),
        help="Faqat shu qoidani bajaradi (bir necha marta berish mumkin)",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=retention_service.DEFAULT_MAX_ROWS,
        help=f"Bitta yurishdagi maksimal qator (standart: {retention_service.DEFAULT_MAX_ROWS})",
    )
    parser.add_argument("--actor", default="", help="Audit jurnalida ko'rinadigan nom")
    return parser


def _print_report(report: RetentionReport) -> None:
    mode = "BAJARILDI" if not report.dry_run else "HISOBOT (hech narsa o'zgarmadi)"
    print(f"Saqlash siyosati — {mode}, run={report.run_id}")
    for rule in report.rules:
        label = RULE_LABELS.get(rule.rule, rule.rule)
        if not rule.enabled:
            print(f"  {label}: o'chirilgan (0 kun)")
            continue
        # Kesish chegarasi chop etiladi: "30 kun" dan yurishni qayta tiklab bo'lmaydi.
        suffix = f", bajarildi: {rule.affected}" if not report.dry_run else ""
        print(f"  {label}: {rule.candidates} ta mos, chegara {rule.cutoff}{suffix}")
    if not report.dry_run:
        print(f"Jami: {report.total_affected} qator")


def _actor(name: str) -> AdminIdentity:
    return AdminIdentity(username=name or "cli", role=AdminRole.OWNER, actor_type=ACTOR_CLI)


def _run(db: Session, args: argparse.Namespace) -> int:
    report = retention_service.run(
        db,
        dry_run=not args.apply,
        rules=args.rule,
        max_rows=max(1, args.max_rows),
        actor=_actor(args.actor),
    )
    _print_report(report)
    if args.apply:
        retention_service.mark_heartbeat(db, report)
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
