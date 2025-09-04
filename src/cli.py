from __future__ import annotations

import argparse
import sys

from src.utils import get_logger

logger = get_logger("cli")


def cmd_init_db(args: argparse.Namespace) -> int:
    from src.utils import get_engine
    base = "db"
    files = ["init.sql", "views.sql", "stored_procs.sql"]
    eng = get_engine()
    for fname in files:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), base, fname)
        with open(path, "r", encoding="utf-8") as f:
            sql = f.read()
        with eng.begin() as con:
            con.exec_driver_sql(sql)
        logger.info("Executed %s", fname)
    return 0


def cmd_seed(args: argparse.Namespace) -> int:
    from src.data_gen.generate_entities import seed_entities_to_db
    seed_entities_to_db()
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    from src.data_gen.generate_transactions import write_transactions
    from src.data_gen.inject_fraud_patterns import inject_fraud
    from src.utils import read_sql, write_df
    n = write_transactions(days=args.days, tx_per_day=args.tx_per_day)
    # Optional: label some fraud records with injected patterns for training
    tx = read_sql("SELECT * FROM transactions ORDER BY ts DESC LIMIT :n", {"n": n})
    tx = inject_fraud(tx)
    # Upsert: for simplicity insert new rows only (demo purpose)
    write_df(tx.tail(max(0, len(tx) - n)), "transactions")
    logger.info("Generated and injected fraud into recent batch")
    return 0


def cmd_features(args: argparse.Namespace) -> int:
    from src.features.build_features import build_features
    cnt = build_features()
    logger.info("Built %d rows of features", cnt)
    return 0


def cmd_rulescore(args: argparse.Namespace) -> int:
    from src.rules.engine import score_rules
    cnt = score_rules()
    logger.info("Created %d alerts", cnt)
    return 0


def cmd_trainsklearn(args: argparse.Namespace) -> int:
    from src.ml.train import train
    model_path, feat_list = train(algo=args.algo)
    logger.info("Model saved: %s", model_path)
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    from src.ml.evaluate import evaluate
    from src.ml.predict import _latest_model
    model = _latest_model()
    evaluate(model)
    return 0


def cmd_predict(args: argparse.Namespace) -> int:
    from src.ml.predict import predict_and_store
    predict_and_store()
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from src.reporting.daily_report import generate_daily_report
    path = generate_daily_report()
    print(path)
    return 0


def cmd_label_fraud(args: argparse.Namespace) -> int:
    """Heuristic post-labeling: mark transactions with alerts or high model proba as fraud.

    This simulates feedback from Ops. It writes to labels and updates transactions.label_fraud.
    """
    from src.utils import get_engine
    threshold = float(args.threshold)
    eng = get_engine()
    sql = f"""
        INSERT INTO labels (tx_id, source, label)
        SELECT t.tx_id, 'heuristic', TRUE
        FROM transactions t
        LEFT JOIN alerts a ON a.tx_id = t.tx_id
        LEFT JOIN LATERAL (
          SELECT * FROM model_scores ms2 WHERE ms2.tx_id = t.tx_id ORDER BY created_at DESC LIMIT 1
        ) ms ON true
        WHERE (a.alert_id IS NOT NULL) OR (ms.proba >= {threshold})
        ON CONFLICT (tx_id) DO NOTHING;

        UPDATE transactions t SET label_fraud = l.label
        FROM labels l WHERE l.tx_id = t.tx_id;
    """
    with eng.begin() as con:
        con.exec_driver_sql(sql)
    logger.info("Applied heuristic labels with threshold=%.2f", threshold)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fraud-e2e", description="Fraud analytics CLI")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("init-db")
    sub.add_parser("seed")

    pg = sub.add_parser("generate")
    pg.add_argument("--days", type=int, default=1)
    pg.add_argument("--tx-per-day", type=int, default=50000)

    sub.add_parser("features")
    sub.add_parser("rulescore")

    pt = sub.add_parser("trainsklearn")
    pt.add_argument("--algo", choices=["lr", "rf", "xgb"], default="rf")

    sub.add_parser("evaluate")
    sub.add_parser("predict")
    sub.add_parser("report")
    pl = sub.add_parser("label-fraud")
    pl.add_argument("--threshold", type=float, default=0.9)
    return p


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    p = build_parser()
    args = p.parse_args(argv)
    cmd = args.command
    if cmd == "init-db":
        return cmd_init_db(args)
    if cmd == "seed":
        return cmd_seed(args)
    if cmd == "generate":
        return cmd_generate(args)
    if cmd == "features":
        return cmd_features(args)
    if cmd == "rulescore":
        return cmd_rulescore(args)
    if cmd == "trainsklearn":
        return cmd_trainsklearn(args)
    if cmd == "evaluate":
        return cmd_evaluate(args)
    if cmd == "predict":
        return cmd_predict(args)
    if cmd == "report":
        return cmd_report(args)
    if cmd == "label-fraud":
        return cmd_label_fraud(args)
    p.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
