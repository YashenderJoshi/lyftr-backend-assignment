from datetime import datetime
import sqlite3
from app.models import get_connection


def insert_message(message: dict) -> str:
    """
    Inserts a message if it does not already exist.
    Returns:
      - "created" if inserted
      - "duplicate" if message_id already exists
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO messages (
                message_id,
                from_msisdn,
                to_msisdn,
                ts,
                text,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message["message_id"],
                message["from"],
                message["to"],
                message["ts"],
                message.get("text"),
                datetime.utcnow().isoformat() + "Z",
            ),
        )
        conn.commit()
        return "created"

    except sqlite3.IntegrityError:
        # PRIMARY KEY violation → duplicate message_id
        return "duplicate"

    finally:
        conn.close()

def list_messages(
    limit: int = 50,
    offset: int = 0,
    from_msisdn: str | None = None,
    since: str | None = None,
    q: str | None = None,
):
    conn = get_connection()
    cursor = conn.cursor()

    where = []
    params = []

    if from_msisdn:
        where.append("from_msisdn = ?")
        params.append(from_msisdn)

    if since:
        where.append("ts >= ?")
        params.append(since)

    if q:
        where.append("LOWER(text) LIKE ?")
        params.append(f"%{q.lower()}%")

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    # total count (ignores limit/offset)
    cursor.execute(f"SELECT COUNT(*) FROM messages {where_sql}", params)
    total = cursor.fetchone()[0]

    # page data
    cursor.execute(
        f"""
        SELECT message_id, from_msisdn, to_msisdn, ts, text
        FROM messages
        {where_sql}
        ORDER BY ts ASC, message_id ASC
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset],
    )
    rows = cursor.fetchall()
    conn.close()

    data = [
        {
            "message_id": r[0],
            "from": r[1],
            "to": r[2],
            "ts": r[3],
            "text": r[4],
        }
        for r in rows
    ]

    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()

    # total messages
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]

    # unique senders
    cursor.execute("SELECT COUNT(DISTINCT from_msisdn) FROM messages")
    senders_count = cursor.fetchone()[0]

    # messages per sender (top 10)
    cursor.execute(
        """
        SELECT from_msisdn, COUNT(*) as cnt
        FROM messages
        GROUP BY from_msisdn
        ORDER BY cnt DESC
        LIMIT 10
        """
    )
    messages_per_sender = [
        {"from": row[0], "count": row[1]} for row in cursor.fetchall()
    ]

    # first and last message timestamps
    cursor.execute("SELECT MIN(ts), MAX(ts) FROM messages")
    first_ts, last_ts = cursor.fetchone()

    conn.close()

    return {
        "total_messages": total_messages,
        "senders_count": senders_count,
        "messages_per_sender": messages_per_sender,
        "first_message_ts": first_ts,
        "last_message_ts": last_ts,
    }

