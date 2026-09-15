"""
Ma'lumotlar bazasi modellari.
Bot ham, admin panel ham shu fayldagi jadvallardan foydalanadi.
"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)          # masalan: "Uzuklar", "Atirlar"
    emoji = Column(String(10), default="✨")              # tugmada ko'rinadigan emoji
    order = Column(Integer, default=0)                    # tartib raqami
    is_active = Column(Boolean, default=True)

    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    price = Column(Float, nullable=False)                 # asosiy (joriy) narx
    old_price = Column(Float, nullable=True)               # chegirmadan oldingi narx (chizib ko'rsatiladi)
    photo_path = Column(String(300), nullable=True)        # /uploads/xxx.jpg
    in_stock = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)               # mijozga ko'rinsinmi
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="products")

    @property
    def has_discount(self):
        return self.old_price is not None and self.old_price > self.price

    @property
    def discount_percent(self):
        if self.has_discount:
            return round((1 - self.price / self.old_price) * 100)
        return 0


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(Integer, nullable=False)
    customer_name = Column(String(150), nullable=False)
    phone = Column(String(30), nullable=False)
    address = Column(String(400), nullable=False)
    total_price = Column(Float, default=0)
    status = Column(String(30), default="yangi")   # yangi | tasdiqlandi | bekor_qilindi | yetkazildi
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(200), nullable=False)     # nusxa - mahsulot o'chirilsa ham buyurtma tarixi qolsin
    price = Column(Float, nullable=False)                   # sotilgan paytdagi narx
    quantity = Column(Integer, default=1)

    order = relationship("Order", back_populates="items")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(300), nullable=False)


# ---- Baza bilan ulanish uchun umumiy funksiyalar ----
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = "sqlite:///" + os.path.join(_PROJECT_ROOT, "shop.db")

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
