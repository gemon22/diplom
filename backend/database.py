import json
import logging
from datetime import datetime

import mysql.connector
from mysql.connector import Error

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()

    def _connect_kwargs(self, database: str | None = None) -> dict:
        kwargs = {
            "host": Config.DB_HOST,
            "port": Config.DB_PORT,
            "user": Config.DB_USER,
            "password": Config.DB_PASSWORD,
            "autocommit": True,
        }
        if database:
            kwargs["database"] = database
        if Config.DB_SSL_DISABLED:
            kwargs["ssl_disabled"] = True
        elif Config.DB_SSL_CA:
            kwargs["ssl_ca"] = Config.DB_SSL_CA
        return kwargs

    def _ensure_database_exists(self):
        """Создаёт БД tour_generator, если её ещё нет (локально). В облаке — DB_SKIP_CREATE=true."""
        if Config.DB_SKIP_CREATE:
            return
        try:
            conn = mysql.connector.connect(**self._connect_kwargs())
            cursor = conn.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Error as e:
            logger.error(f"Cannot create database: {e}")
            raise

    def connect(self):
        try:
            self._ensure_database_exists()
            self.connection = mysql.connector.connect(
                **self._connect_kwargs(Config.DB_NAME)
            )
            logger.info("Connected to MySQL")
        except Error as e:
            logger.error(f"DB error: {e}")
            raise

    def create_tables(self):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hotels (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                destination VARCHAR(100) NOT NULL,
                price_per_night DECIMAL(10,2),
                total_stay_price DECIMAL(10,2),
                amenities TEXT,
                rating FLOAT,
                source_url VARCHAR(512),
                source_site VARCHAR(255),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_destination (destination),
                INDEX idx_price (total_stay_price)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS flights (
                id INT AUTO_INCREMENT PRIMARY KEY,
                from_city VARCHAR(100),
                to_city VARCHAR(100),
                departure_date DATE,
                return_date DATE,
                price DECIMAL(10,2),
                airline VARCHAR(100),
                source_site VARCHAR(255),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id VARCHAR(100) PRIMARY KEY,
                dialog_state JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_queries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(100),
                user_input TEXT,
                extracted_params JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_session (session_id),
                INDEX idx_created (created_at)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS generated_tours (
                id INT AUTO_INCREMENT PRIMARY KEY,
                query_id INT,
                tour_package JSON,
                total_price DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES user_queries(id) ON DELETE CASCADE
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                requests_count INT DEFAULT 0,
                tours_generated INT DEFAULT 0,
                avg_response_time_ms INT DEFAULT 0
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS agency_leads (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(100),
                name VARCHAR(255) NOT NULL,
                phone VARCHAR(50) NOT NULL,
                email VARCHAR(255),
                message TEXT,
                tour_name VARCHAR(512),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_leads_created (created_at)
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS managers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(64) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'manager',
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_managers_username (username)
            )
        """
        )

        self.connection.commit()
        cursor.close()
        logger.info("Tables ready")
        self.ensure_default_manager()

    def clear_hotels(self):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM hotels")
        self.connection.commit()
        cursor.close()

    def insert_hotels(self, hotels_list):
        cursor = self.connection.cursor()
        sql = """
            INSERT INTO hotels
            (name, destination, price_per_night, total_stay_price, amenities, rating, source_url, source_site)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        for h in hotels_list:
            cursor.execute(
                sql,
                (
                    h.get("name"),
                    h.get("destination"),
                    h.get("price_per_night"),
                    h.get("total_stay_price"),
                    h.get("amenities"),
                    h.get("rating"),
                    h.get("source_url"),
                    h.get("source_site"),
                ),
            )
        self.connection.commit()
        cursor.close()
        logger.info(f"Inserted {len(hotels_list)} hotels")

    def get_all_hotels_sample(self, limit=50, source_site=None):
        """Срез каталога для контекста нейросети."""
        cursor = self.connection.cursor(dictionary=True)
        query = """
            SELECT name, destination, total_stay_price, source_url
            FROM hotels
            WHERE 1=1
        """
        params: list = []
        if source_site:
            query += " AND source_site = %s"
            params.append(source_site)
        query += " ORDER BY destination, total_stay_price ASC LIMIT %s"
        params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def get_hotels(
        self,
        destination=None,
        max_price_rub=None,
        limit=10,
        source_site=None,
    ):
        """max_price_rub — бюджет в рублях; цены в БД — в рублях."""
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM hotels WHERE 1=1"
        params = []
        if destination:
            query += " AND destination LIKE %s"
            params.append(f"%{destination}%")
        if source_site:
            query += " AND source_site = %s"
            params.append(source_site)
        if max_price_rub is not None:
            try:
                query += " AND (total_stay_price <= %s OR total_stay_price = 0)"
                params.append(float(max_price_rub))
            except (TypeError, ValueError):
                pass
        query += " ORDER BY total_stay_price ASC LIMIT %s"
        params.append(limit)
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results

    def count_demo_records(self) -> int:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT (SELECT COUNT(*) FROM hotels WHERE source_site = 'demo')"
            " + (SELECT COUNT(*) FROM flights WHERE source_site = 'demo')"
        )
        row = cursor.fetchone()
        cursor.close()
        return int(row[0] or 0) if row else 0

    def clear_demo_data(self):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM hotels WHERE source_site = 'demo'")
        cursor.execute("DELETE FROM flights WHERE source_site = 'demo'")
        self.connection.commit()
        cursor.close()

    def count_flights_by_source(self, source_site: str) -> int:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM flights WHERE source_site = %s",
            (source_site,),
        )
        row = cursor.fetchone()
        cursor.close()
        return int(row[0] or 0) if row else 0

    def clear_flights_by_source(self, source_site: str):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM flights WHERE source_site = %s", (source_site,))
        self.connection.commit()
        cursor.close()

    def get_flights(
        self,
        to_city=None,
        departure_date=None,
        return_date=None,
        source_site=None,
        limit=5,
    ):
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM flights WHERE 1=1"
        params: list = []
        if to_city:
            query += " AND to_city LIKE %s"
            params.append(f"%{to_city}%")
        if source_site:
            query += " AND source_site = %s"
            params.append(source_site)
        if departure_date:
            query += " AND (departure_date IS NULL OR departure_date <= %s)"
            params.append(departure_date)
        if return_date:
            query += " AND (return_date IS NULL OR return_date >= %s)"
            params.append(return_date)
        query += " ORDER BY price ASC LIMIT %s"
        params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def save_session(self, session_id, dialog_state):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO user_sessions (session_id, dialog_state)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE dialog_state = VALUES(dialog_state)
        """,
            (session_id, json.dumps(dialog_state, ensure_ascii=False)),
        )
        self.connection.commit()
        cursor.close()

    def get_session(self, session_id):
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT dialog_state FROM user_sessions WHERE session_id = %s",
            (session_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        if row and row["dialog_state"]:
            state = row["dialog_state"]
            return json.loads(state) if isinstance(state, str) else state
        return None

    def log_query(self, session_id, user_input, extracted_params=None):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO user_queries (session_id, user_input, extracted_params)
            VALUES (%s, %s, %s)
        """,
            (
                session_id,
                user_input,
                json.dumps(extracted_params, ensure_ascii=False)
                if extracted_params
                else None,
            ),
        )
        self.connection.commit()
        qid = cursor.lastrowid
        cursor.close()

        today = datetime.now().date()
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO daily_stats (date, requests_count, tours_generated)
            VALUES (%s, 1, 0)
            ON DUPLICATE KEY UPDATE requests_count = requests_count + 1
        """,
            (today,),
        )
        self.connection.commit()
        cursor.close()
        return qid

    def update_query_params(self, query_id: int, extracted_params: dict | None):
        if not query_id or not extracted_params:
            return
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE user_queries SET extracted_params = %s WHERE id = %s
            """,
            (json.dumps(extracted_params, ensure_ascii=False), query_id),
        )
        self.connection.commit()
        cursor.close()

    def ensure_default_manager(self):
        from admin_auth import hash_password
        from config import Config

        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM managers")
        count = int((cursor.fetchone() or [0])[0])
        if count == 0:
            cursor.execute(
                """
                INSERT INTO managers (username, password_hash, role)
                VALUES (%s, %s, 'admin')
                """,
                (
                    Config.ADMIN_DEFAULT_LOGIN,
                    hash_password(Config.ADMIN_DEFAULT_PASSWORD),
                ),
            )
            self.connection.commit()
            logger.info("Default manager created: %s", Config.ADMIN_DEFAULT_LOGIN)
        cursor.close()

    def get_manager_by_username(self, username: str) -> dict | None:
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM managers WHERE username = %s AND is_active = 1",
            (username,),
        )
        row = cursor.fetchone()
        cursor.close()
        return row

    def get_manager_by_id(self, manager_id: int) -> dict | None:
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, role, is_active, created_at FROM managers WHERE id = %s",
            (manager_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return row

    def list_managers(self) -> list[dict]:
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, role, is_active, created_at FROM managers ORDER BY id"
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def create_manager(self, username: str, password_hash: str, role: str = "manager") -> int:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO managers (username, password_hash, role)
            VALUES (%s, %s, %s)
            """,
            (username, password_hash, role),
        )
        self.connection.commit()
        mid = cursor.lastrowid
        cursor.close()
        return mid

    def update_manager_credentials(
        self, manager_id: int, username: str | None = None, password_hash: str | None = None
    ):
        cursor = self.connection.cursor()
        if username and password_hash:
            cursor.execute(
                "UPDATE managers SET username = %s, password_hash = %s WHERE id = %s",
                (username, password_hash, manager_id),
            )
        elif username:
            cursor.execute(
                "UPDATE managers SET username = %s WHERE id = %s",
                (username, manager_id),
            )
        elif password_hash:
            cursor.execute(
                "UPDATE managers SET password_hash = %s WHERE id = %s",
                (password_hash, manager_id),
            )
        self.connection.commit()
        cursor.close()

    def get_recent_queries(self, limit: int = 100, since_id: int = 0) -> list[dict]:
        cursor = self.connection.cursor(dictionary=True)
        if since_id > 0:
            cursor.execute(
                """
                SELECT id, session_id, user_input, extracted_params, created_at
                FROM user_queries
                WHERE id > %s
                ORDER BY id ASC
                LIMIT %s
                """,
                (since_id, limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, session_id, user_input, extracted_params, created_at
                FROM user_queries
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )
        rows = cursor.fetchall()
        cursor.close()
        for r in rows:
            ep = r.get("extracted_params")
            if isinstance(ep, str):
                try:
                    r["extracted_params"] = json.loads(ep)
                except json.JSONDecodeError:
                    r["extracted_params"] = None
        if since_id == 0:
            rows.reverse()
        return rows

    def get_destination_stats(self, limit: int = 15) -> dict:
        """Считает популярные направления только по репликам, где явно указана страна."""
        from dialog_hints import destination_from_message

        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT user_input, extracted_params
            FROM user_queries
            ORDER BY id DESC
            LIMIT 5000
            """
        )
        rows = cursor.fetchall()
        cursor.close()

        counts: dict[str, int] = {}
        matched = 0
        for r in rows:
            ep = r.get("extracted_params")
            if isinstance(ep, str):
                try:
                    ep = json.loads(ep)
                except json.JSONDecodeError:
                    ep = None
            ep_dest = ep.get("destination") if isinstance(ep, dict) else None
            dest = destination_from_message(r.get("user_input") or "", ep_dest)
            if dest:
                matched += 1
                counts[dest] = counts.get(dest, 0) + 1

        items = [
            {"destination": d, "count": c}
            for d, c in sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:limit]
        ]
        return {
            "items": items,
            "matched_queries": matched,
        }

    def save_tour(self, query_id, tour_package, total_price):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO generated_tours (query_id, tour_package, total_price)
            VALUES (%s, %s, %s)
        """,
            (query_id, json.dumps(tour_package, ensure_ascii=False), total_price),
        )
        self.connection.commit()
        cursor.close()

        today = datetime.now().date()
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO daily_stats (date, requests_count, tours_generated)
            VALUES (%s, 0, 1)
            ON DUPLICATE KEY UPDATE tours_generated = tours_generated + 1
        """,
            (today,),
        )
        self.connection.commit()
        cursor.close()

    def save_flights(self, flights: list[dict]):
        if not flights:
            return
        cursor = self.connection.cursor()
        sql = """
            INSERT INTO flights
            (from_city, to_city, departure_date, return_date, price, airline, source_site)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for f in flights:
            dep = (f.get("departure_at") or "")[:10] or None
            ret = (f.get("return_at") or "")[:10] or None
            cursor.execute(
                sql,
                (
                    f.get("origin"),
                    f.get("destination"),
                    dep,
                    ret,
                    f.get("price"),
                    f.get("airline"),
                    f.get("source_site", "travelpayouts"),
                ),
            )
        self.connection.commit()
        cursor.close()

    def insert_lead(
        self,
        name: str,
        phone: str,
        email: str | None = None,
        message: str | None = None,
        session_id: str | None = None,
        tour_name: str | None = None,
    ) -> int:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO agency_leads (session_id, name, phone, email, message, tour_name)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (session_id, name, phone, email, message, tour_name),
        )
        self.connection.commit()
        lid = cursor.lastrowid
        cursor.close()
        return lid

    def get_today_stats(self):
        today = datetime.now().date()
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT requests_count, tours_generated FROM daily_stats WHERE date = %s",
            (today,),
        )
        row = cursor.fetchone()
        cursor.close()
        return row or {"requests_count": 0, "tours_generated": 0}

    def get_recent_leads(self, limit: int = 50) -> list[dict]:
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, session_id, name, phone, email, message, tour_name, created_at
            FROM agency_leads
            ORDER BY id DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def get_recent_tours(self, limit: int = 20) -> list[dict]:
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT gt.id, gt.query_id, gt.total_price, gt.created_at,
                   uq.session_id, uq.user_input
            FROM generated_tours gt
            LEFT JOIN user_queries uq ON uq.id = gt.query_id
            ORDER BY gt.id DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def count_leads_today(self) -> int:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM agency_leads WHERE DATE(created_at) = CURDATE()"
        )
        row = cursor.fetchone()
        cursor.close()
        return int(row[0] or 0) if row else 0

    def close(self):
        if self.connection:
            self.connection.close()


_db_instance = None


def get_db():
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
