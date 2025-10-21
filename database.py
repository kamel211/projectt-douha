# # from sqlalchemy import create_engine, text
# # from sqlalchemy.orm import sessionmaker, declarative_base
# from pymongo import MongoClient
# from pymongo.errors import ConnectionFailure

# # # =============== PostgreSQL Connection ===============
# # SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:douha@localhost:5432/project"

# # try:
# #     engine = create_engine(SQLALCHEMY_DATABASE_URL)
# #     SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# #     Base = declarative_base()

# #     # اختبار الاتصال بـ PostgreSQL
# #     with engine.connect() as conn:
# #         conn.execute(text("SELECT 1"))
# #     print(" Connected to PostgreSQL successfully!")

# # except Exception as e:
# #     print(" PostgreSQL connection failed:", e)


# # =============== MongoDB Connection ===============
# MONGO_URL = "mongodb+srv://kamelbataineh:Kamel123@cluster0.cf0rmeu.mongodb.net/university_project?retryWrites=true&w=majority&appName=Cluster0"

# try:
#     mongo_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
#     mongo_client.server_info() 
#     mongo_db = mongo_client["university_project"]
#     print(" Connected to MongoDB successfully!")
#     doctors_collection = mongo_db["doctors"]
#     appointments_collection = mongo_db["appointments"]
#     patients_collection = mongo_db["patients"]

# except ConnectionFailure as e:
#     print(" MongoDB connection failed:", e)
# except Exception as e:
#     print("MongoDB unknown error:", e)



# # pip install uvicorn


from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# ================= MongoDB Connection =================
MONGO_URL = "mongodb+srv://kamelbataineh:Kamel123@cluster0.cf0rmeu.mongodb.net/university_project?retryWrites=true&w=majority&appName=Cluster0"

try:
    # إنشاء الاتصال
    mongo_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=10000)
    
    # اختبار الاتصال
    mongo_client.admin.command('ping')
    
    # اختيار قاعدة البيانات
    mongo_db = mongo_client["university_project"]
    
    # اختيار الـ Collections
    doctors_collection = mongo_db["doctors"]
    appointments_collection = mongo_db["appointments"]
    patients_collection = mongo_db["patients"]

    print("✅ Connected to MongoDB successfully!")

except ConnectionFailure as e:
    print("❌ MongoDB connection failed:", e)
except Exception as e:
    print("❌ MongoDB unknown error:", e)
