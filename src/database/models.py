"""SQLAlchemy модели для базы данных"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, DateTime,
    Boolean, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class PaymentStatus(enum.Enum):
    """Статусы платежей"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethod(enum.Enum):
    """Методы оплаты"""
    CARD = "card"
    SBP = "sbp"
    USDT = "usdt"


class SubscriptionStatus(enum.Enum):
    """Статусы подписок"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)  # Telegram user_id
    username = Column(String(255), nullable=True)
    registration_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    invites = relationship("Invite", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username})>"


class Payment(Base):
    """Модель платежа"""
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False, index=True)
    payment_id = Column(String(255), unique=True, nullable=False, index=True)  # Наш внутренний ID
    external_id = Column(String(255), nullable=True)  # ID от платёжной системы
    
    tariff = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    method = Column(SQLEnum(PaymentMethod), nullable=False)
    
    payment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="payments")

    def __repr__(self):
        return f"<Payment(payment_id={self.payment_id}, status={self.status.value}, amount={self.amount})>"


class Subscription(Base):
    """Модель подписки"""
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False, index=True)
    payment_id = Column(String(255), ForeignKey('payments.payment_id'), nullable=False)
    
    tariff = Column(String(255), nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime, nullable=False, index=True)
    
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, tariff={self.tariff}, status={self.status.value})>"

    @property
    def is_active(self):
        """Проверяет, активна ли подписка"""
        return self.status == SubscriptionStatus.ACTIVE and self.end_date > datetime.utcnow()


class Invite(Base):
    """Модель инвайт-ссылки"""
    __tablename__ = 'invites'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False, index=True)
    chat_id = Column(Integer, nullable=False)
    invite_link = Column(String(512), nullable=False, unique=True, index=True)
    
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    used_at = Column(DateTime, nullable=True)

    # Relationship
    user = relationship("User", back_populates="invites")

    def __repr__(self):
        return f"<Invite(user_id={self.user_id}, chat_id={self.chat_id}, is_used={self.is_used})>"

    def mark_as_used(self):
        """Помечает инвайт как использованный"""
        self.is_used = True
        self.used_at = datetime.utcnow()
