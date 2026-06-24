# """
# db.py
# =====

# PostgreSQL persistence layer for:
# - Conversations
# - Messages
# - Documents

# Uses:
# - SQLAlchemy ORM
# - DATABASE_URL from .env

# Required packages:

# pip install sqlalchemy psycopg2-binary python-dotenv
# """

# import os
# import uuid
# from datetime import datetime
# from typing import List, Optional

# from dotenv import load_dotenv
# from sqlalchemy import (
#     Column,
#     DateTime,
#     ForeignKey,
#     Integer,
#     String,
#     Text,
#     create_engine,
# )
# from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# # ------------------------------------------------------------------
# # Environment
# # ------------------------------------------------------------------
# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")

# if not DATABASE_URL:
#     raise ValueError(
#         "DATABASE_URL not found in environment variables."
#     )

# # ------------------------------------------------------------------
# # SQLAlchemy
# # ------------------------------------------------------------------
# engine = create_engine(
#     DATABASE_URL,
#     pool_pre_ping=True,
# )

# SessionLocal = sessionmaker(
#     autocommit=False,
#     autoflush=False,
#     bind=engine,
# )

# Base = declarative_base()

# # ------------------------------------------------------------------
# # Models
# # ------------------------------------------------------------------


# class Conversation(Base):
#     __tablename__ = "conversations"

#     id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

#     title = Column(String(255), nullable=False, default="New Chat")

#     summary = Column(Text, nullable=True)

#     created_at = Column(
#         DateTime,
#         default=datetime.utcnow,
#         nullable=False,
#     )

#     updated_at = Column(
#         DateTime,
#         default=datetime.utcnow,
#         nullable=False,
#     )

#     messages = relationship(
#         "Message",
#         back_populates="conversation",
#         cascade="all, delete-orphan",
#     )

#     documents = relationship(
#         "Document",
#         back_populates="conversation",
#         cascade="all, delete-orphan",
#     )


# class Message(Base):
#     __tablename__ = "messages"

#     id = Column(Integer, primary_key=True, autoincrement=True)

#     conversation_id = Column(
#         String(36),
#         ForeignKey("conversations.id", ondelete="CASCADE"),
#         nullable=False,
#     )

#     role = Column(String(20), nullable=False)

#     content = Column(Text, nullable=False)

#     created_at = Column(
#         DateTime,
#         default=datetime.utcnow,
#         nullable=False,
#     )

#     conversation = relationship(
#         "Conversation",
#         back_populates="messages",
#     )


# class Document(Base):
#     __tablename__ = "documents"

#     id = Column(Integer, primary_key=True, autoincrement=True)

#     conversation_id = Column(
#         String(36),
#         ForeignKey("conversations.id", ondelete="CASCADE"),
#         nullable=False,
#     )

#     filename = Column(String(500), nullable=False)

#     num_chunks = Column(Integer, nullable=False)

#     uploaded_at = Column(
#         DateTime,
#         default=datetime.utcnow,
#         nullable=False,
#     )

#     conversation = relationship(
#         "Conversation",
#         back_populates="documents",
#     )


# # ------------------------------------------------------------------
# # Initialization
# # ------------------------------------------------------------------


# def init_db():
#     Base.metadata.create_all(bind=engine)


# # ------------------------------------------------------------------
# # Conversations
# # ------------------------------------------------------------------


# def create_conversation(title: str = "New Chat"):
#     session = SessionLocal()

#     try:
#         conversation = Conversation(
#             title=title,
#         )

#         session.add(conversation)
#         session.commit()
#         session.refresh(conversation)

#         return conversation

#     finally:
#         session.close()


# def get_conversation(conversation_id: str):
#     session = SessionLocal()

#     try:
#         return (
#             session.query(Conversation)
#             .filter(Conversation.id == conversation_id)
#             .first()
#         )

#     finally:
#         session.close()


# def list_conversations():
#     session = SessionLocal()

#     try:
#         return (
#             session.query(Conversation)
#             .order_by(Conversation.updated_at.desc())
#             .all()
#         )

#     finally:
#         session.close()


# def update_conversation_title(
#     conversation_id: str,
#     title: str,
# ):
#     session = SessionLocal()

#     try:
#         convo = (
#             session.query(Conversation)
#             .filter(Conversation.id == conversation_id)
#             .first()
#         )

#         if convo:
#             convo.title = title
#             convo.updated_at = datetime.utcnow()
#             session.commit()

#     finally:
#         session.close()


# def update_conversation_summary(
#     conversation_id: str,
#     summary: str,
# ):
#     session = SessionLocal()

#     try:
#         convo = (
#             session.query(Conversation)
#             .filter(Conversation.id == conversation_id)
#             .first()
#         )

#         if convo:
#             convo.summary = summary
#             convo.updated_at = datetime.utcnow()
#             session.commit()

#     finally:
#         session.close()


# def touch_conversation(conversation_id: str):
#     session = SessionLocal()

#     try:
#         convo = (
#             session.query(Conversation)
#             .filter(Conversation.id == conversation_id)
#             .first()
#         )

#         if convo:
#             convo.updated_at = datetime.utcnow()
#             session.commit()

#     finally:
#         session.close()


# def delete_conversation(conversation_id: str):
#     session = SessionLocal()

#     try:
#         convo = (
#             session.query(Conversation)
#             .filter(Conversation.id == conversation_id)
#             .first()
#         )

#         if convo:
#             session.delete(convo)
#             session.commit()

#     finally:
#         session.close()


# # ------------------------------------------------------------------
# # Messages
# # ------------------------------------------------------------------


# def add_message(
#     conversation_id: str,
#     role: str,
#     content: str,
# ):
#     session = SessionLocal()

#     try:
#         message = Message(
#             conversation_id=conversation_id,
#             role=role,
#             content=content,
#         )

#         session.add(message)
#         session.commit()

#         return message

#     finally:
#         session.close()


# def get_messages(
#     conversation_id: str,
#     limit: Optional[int] = None,
# ):
#     session = SessionLocal()

#     try:
#         query = (
#             session.query(Message)
#             .filter(Message.conversation_id == conversation_id)
#             .order_by(Message.created_at.asc())
#         )

#         messages = query.all()

#         if limit:
#             messages = messages[-limit:]

#         return messages

#     finally:
#         session.close()


# def count_messages(conversation_id: str):
#     session = SessionLocal()

#     try:
#         return (
#             session.query(Message)
#             .filter(Message.conversation_id == conversation_id)
#             .count()
#         )

#     finally:
#         session.close()


# # ------------------------------------------------------------------
# # Documents
# # ------------------------------------------------------------------


# def add_document_record(
#     conversation_id: str,
#     filename: str,
#     num_chunks: int,
# ):
#     session = SessionLocal()

#     try:
#         document = Document(
#             conversation_id=conversation_id,
#             filename=filename,
#             num_chunks=num_chunks,
#         )

#         session.add(document)
#         session.commit()

#         return document

#     finally:
#         session.close()


# def list_documents(conversation_id: str):
#     session = SessionLocal()

#     try:
#         return (
#             session.query(Document)
#             .filter(Document.conversation_id == conversation_id)
#             .order_by(Document.uploaded_at.desc())
#             .all()
#         )

#     finally:
#         session.close()


























"""
db.py
=====

PostgreSQL persistence layer for:
- Conversations
- Messages
- Documents

Uses:
- SQLAlchemy ORM
- DATABASE_URL from .env

Required packages:

pip install sqlalchemy psycopg2-binary python-dotenv

NOTE: Message ordering assumption:
  In backend_server.py's /chat handler, db.add_message(...) is called
  BEFORE backend.generate_answer(...). This means when build_memory_context()
  later fetches messages inside generate_answer(), the current user question
  is already the last row in the list. The memory expansion logic in backend.py
  accounts for this (skipping the last message when looking for prior context).
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# ------------------------------------------------------------------
# Environment
# ------------------------------------------------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL not found in environment variables."
    )

# ------------------------------------------------------------------
# SQLAlchemy
# ------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    title = Column(String(255), nullable=False, default="New Chat")

    summary = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    documents = relationship(
        "Document",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)

    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )

    role = Column(String(20), nullable=False)

    content = Column(Text, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    conversation = relationship(
        "Conversation",
        back_populates="messages",
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)

    conversation_id = Column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )

    filename = Column(String(500), nullable=False)

    num_chunks = Column(Integer, nullable=False)

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    conversation = relationship(
        "Conversation",
        back_populates="documents",
    )


# ------------------------------------------------------------------
# Initialization
# ------------------------------------------------------------------


def init_db():
    Base.metadata.create_all(bind=engine)


# ------------------------------------------------------------------
# Conversations
# ------------------------------------------------------------------


def create_conversation(title: str = "New Chat"):
    session = SessionLocal()

    try:
        conversation = Conversation(
            title=title,
        )

        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        return conversation

    finally:
        session.close()


def get_conversation(conversation_id: str):
    session = SessionLocal()

    try:
        return (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

    finally:
        session.close()


def list_conversations():
    session = SessionLocal()

    try:
        return (
            session.query(Conversation)
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    finally:
        session.close()


def update_conversation_title(
    conversation_id: str,
    title: str,
):
    session = SessionLocal()

    try:
        convo = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if convo:
            convo.title = title
            convo.updated_at = datetime.utcnow()
            session.commit()

    finally:
        session.close()


def update_conversation_summary(
    conversation_id: str,
    summary: str,
):
    session = SessionLocal()

    try:
        convo = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if convo:
            convo.summary = summary
            convo.updated_at = datetime.utcnow()
            session.commit()

    finally:
        session.close()


def touch_conversation(conversation_id: str):
    session = SessionLocal()

    try:
        convo = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if convo:
            convo.updated_at = datetime.utcnow()
            session.commit()

    finally:
        session.close()


def delete_conversation(conversation_id: str):
    session = SessionLocal()

    try:
        convo = (
            session.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        if convo:
            session.delete(convo)
            session.commit()

    finally:
        session.close()


# ------------------------------------------------------------------
# Messages
# ------------------------------------------------------------------


def add_message(
    conversation_id: str,
    role: str,
    content: str,
):
    session = SessionLocal()

    try:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        session.add(message)
        session.commit()

        return message

    finally:
        session.close()


def get_messages(
    conversation_id: str,
    limit: Optional[int] = None,
):
    session = SessionLocal()

    try:
        query = (
            session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )

        messages = query.all()

        if limit:
            messages = messages[-limit:]

        return messages

    finally:
        session.close()


def count_messages(conversation_id: str):
    session = SessionLocal()

    try:
        return (
            session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .count()
        )

    finally:
        session.close()


# ------------------------------------------------------------------
# Documents
# ------------------------------------------------------------------


def add_document_record(
    conversation_id: str,
    filename: str,
    num_chunks: int,
):
    session = SessionLocal()

    try:
        document = Document(
            conversation_id=conversation_id,
            filename=filename,
            num_chunks=num_chunks,
        )

        session.add(document)
        session.commit()

        return document

    finally:
        session.close()


def list_documents(conversation_id: str):
    session = SessionLocal()

    try:
        return (
            session.query(Document)
            .filter(Document.conversation_id == conversation_id)
            .order_by(Document.uploaded_at.desc())
            .all()
        )

    finally:
        session.close()