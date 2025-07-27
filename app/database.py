import databases
import sqlalchemy

from app.config import config

# ---- The sqlalchemy modules is used to create the database schema ----
metadata = sqlalchemy.MetaData()

post_table = sqlalchemy.Table(
    "posts",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("body", sqlalchemy.String),
)

user_table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True),
    sqlalchemy.Column("password", sqlalchemy.String),
)


comment_table = sqlalchemy.Table(
    "comments",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("body", sqlalchemy.String),
    sqlalchemy.Column(
        "post_id",
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("posts.id"),
        nullable=False,
    ),
)

engine = sqlalchemy.create_engine(
    url=config.DATABASE_URL,
    connect_args={
        "check_same_thread": False  # This enables sqlite to be multithreaded
    },  # Because sqlite is single threaded by default
)

metadata.create_all(engine)

# ---- The databases module is used to interact with the database ----
database = databases.Database(
    config.DATABASE_URL,
    force_rollback=config.DB_FORCE_ROLL_BACK,
)
