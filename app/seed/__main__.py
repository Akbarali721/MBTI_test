"""Kontent va ma'lumot xizmat buyruqlari.

python -m app.seed                          savol va natija kontentini (uz + ru) yuklaydi
python -m app.seed --language ru            faqat bitta til kontentini yuklaydi
python -m app.seed --variant B              savollarni B to'plamiga yuklaydi (A/B test)
python -m app.seed --force --yes            mavjud kontentni joyida almashtiradi
python -m app.seed --recompute              mavjud sessiya ballarini qayta hisoblaydi
python -m app.seed --purge-visited --days 30  eskirgan VISITED sessiyalarni o'chiradi
"""

import argparse
import sys

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.personality import DEFAULT_VARIANT
from app.personality.variants import normalize_variant
from app.repositories.personality_repository import PersonalityRepository
from app.seed.personality_placeholders import (
    SEED_LANGUAGES,
    questions_are_empty,
    results_are_empty,
    seed_personality_questions,
    seed_personality_results,
)

DEFAULT_PURGE_DAYS = 30


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.seed", description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Mavjud kontentni joyida almashtiradi (javoblar saqlanadi)",
    )
    parser.add_argument("--yes", action="store_true", help="Tasdiq so'ramaydi")
    parser.add_argument(
        "--recompute",
        action="store_true",
        help="Saqlangan javoblardan sessiya ballari va result_type ni qayta hisoblaydi",
    )
    parser.add_argument(
        "--purge-visited",
        action="store_true",
        help="Boshlanmagan (VISITED) eskirgan sessiyalarni o'chiradi",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_PURGE_DAYS,
        help=f"--purge-visited uchun kunlar chegarasi (standart: {DEFAULT_PURGE_DAYS})",
    )
    parser.add_argument(
        "--variant",
        default=DEFAULT_VARIANT,
        help=f"Savollar qaysi to'plamga yuklanadi (standart: {DEFAULT_VARIANT}). A/B test uchun.",
    )
    parser.add_argument(
        "--language",
        choices=SEED_LANGUAGES,
        default=None,
        help=f"Faqat bitta tilni yuklaydi (standart: hammasi — {', '.join(SEED_LANGUAGES)})",
    )
    return parser


def _confirm(prompt: str) -> bool:
    if not sys.stdin or not sys.stdin.isatty():
        return False
    answer = input(f"{prompt} [yes/no]: ").strip().lower()
    return answer in ("y", "yes", "ha")


def _run_seed(db: Session, *, force: bool, language: str | None, variant: str = DEFAULT_VARIANT) -> int:
    chosen = normalize_variant(variant)
    questions = seed_personality_questions(db, force=force, variant=chosen)
    if questions:
        print(f"Savollar yuklandi/yangilandi: {questions} ta ({chosen} to'plami)")
    elif not questions_are_empty(db, chosen):
        print(f"{chosen} to'plamida savollar bor, o'zgartirilmadi (--force bilan almashtiring)")

    languages = (language,) if language else SEED_LANGUAGES
    for code in languages:
        results = seed_personality_results(db, force=force, language=code)
        if results:
            print(f"Natija kontenti yuklandi/yangilandi: {results} ta ({code})")
        elif not results_are_empty(db, code):
            print(f"Natija kontenti allaqachon mavjud ({code}), o'zgartirilmadi (--force bilan almashtiring)")
    return 0


def _run_recompute(db: Session) -> int:
    updated = PersonalityRepository(db).recompute_stored_sessions()
    db.commit()
    print(f"Ballari qayta hisoblangan sessiyalar: {updated} ta")
    return 0


def _run_purge(db: Session, days: int) -> int:
    removed = PersonalityRepository(db).delete_stale_visited_sessions(older_than_days=days)
    db.commit()
    print(f"O'chirilgan VISITED sessiyalar ({days} kundan eski): {removed} ta")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    needs_confirmation = args.force and not args.yes
    if needs_confirmation and not _confirm("Mavjud savol/natija kontenti almashtiriladi. Davom etilsinmi?"):
        print("Bekor qilindi. --yes bayrog'i bilan tasdiqlashingiz mumkin.")
        return 1

    db = SessionLocal()
    try:
        if args.recompute:
            return _run_recompute(db)
        if args.purge_visited:
            return _run_purge(db, args.days)
        return _run_seed(db, force=args.force, language=args.language, variant=args.variant)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
