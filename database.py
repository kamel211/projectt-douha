from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import psycopg2

# ---------------- إعداد بيانات الاتصال ----------------
DB_USER = "postgres"        
DB_PASSWORD = "douha2004" 
DB_PORT = "5432"            
DB_NAME = "progect"        
DB_HOST="localhost"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ---------------- إعداد SQLAlchemy ----------------
engine = create_engine(DATABASE_URL, echo=True)  # echo=True لطباعة كل الاستعلامات
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------------- اختبار psycopg2 ----------------
try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    print("✅ Connected with psycopg2!")
    conn.close()
except psycopg2.OperationalError as e:
    print("❌ psycopg2 connection failed:", e)

# ---------------- اختبار SQLAlchemy ----------------
try:
    with engine.connect() as connection:
        print("✅ Connected with SQLAlchemy!")
except Exception as e:
    print("❌ SQLAlchemy connection failed:", e)

# ---------------- دالة get_db لاستخدامها مع FastAPI ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
