from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now():
    return datetime.utcnow()


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(200))
    sector: Mapped[str] = mapped_column(String(100), default="")
    scope: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    analysis_status: Mapped[str] = mapped_column(String(20), default="idle")  # idle|running|done|error
    analysis_done: Mapped[int] = mapped_column(Integer, default=0)
    analysis_total: Mapped[int] = mapped_column(Integer, default=0)
    analysis_error: Mapped[str] = mapped_column(Text, default="")
    analysis_provider: Mapped[str] = mapped_column(String(100), default="")
    documents: Mapped[list["Document"]] = relationship(cascade="all, delete-orphan", back_populates="assessment")
    answers: Mapped[list["Answer"]] = relationship(cascade="all, delete-orphan", back_populates="assessment")
    acceptances: Mapped[list["TermsAcceptance"]] = relationship(cascade="all, delete-orphan", back_populates="assessment", order_by="TermsAcceptance.id")


class TermsAcceptance(Base):
    """Registro de aceite dos termos de uso por avaliação (um por versão aceita)."""
    __tablename__ = "terms_acceptances"
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"))
    version: Mapped[str] = mapped_column(String(20))
    text_hash: Mapped[str] = mapped_column(String(64))
    accepted_by: Mapped[str] = mapped_column(String(200))
    accepted_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    assessment: Mapped["Assessment"] = relationship(back_populates="acceptances")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"))
    slot: Mapped[str] = mapped_column(String(50))
    filename: Mapped[str] = mapped_column(String(300))
    path: Mapped[str] = mapped_column(String(500))
    size: Mapped[int] = mapped_column(Integer, default=0)
    n_chunks: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    assessment: Mapped[Assessment] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(cascade="all, delete-orphan", back_populates="document")
    covers: Mapped[list["DocumentSlot"]] = relationship(cascade="all, delete-orphan", back_populates="document", lazy="selectin")


class DocumentSlot(Base):
    """Tipo de documento que um arquivo principal (slot="principal") cobre, detectado em Python ou marcado pelo usuário."""
    __tablename__ = "document_slots"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    slot: Mapped[str] = mapped_column(String(50))
    score: Mapped[float] = mapped_column(Float, default=0)
    reason: Mapped[str] = mapped_column(Text, default="")
    document: Mapped[Document] = relationship(back_populates="covers")


class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    idx: Mapped[int] = mapped_column(Integer)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str] = mapped_column(Text)
    document: Mapped[Document] = relationship(back_populates="chunks")


class Answer(Base):
    """Resposta de um item do checklist.

    status: pending (sem resposta) | suggested (IA pré-preencheu, falta validar) | validated (profissional confirmou)
    level: 0..5, ou None; na=True significa "não se aplica".
    evidence: lista de {chunk_id, doc_id, doc_name, slot, page, quote, accepted}
    """
    __tablename__ = "answers"
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"))
    item_no: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    na: Mapped[bool] = mapped_column(default=False)
    comment: Mapped[str] = mapped_column(Text, default="")
    ai_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_justification: Mapped[str] = mapped_column(Text, default="")
    ai_missing: Mapped[list] = mapped_column(JSON, default=list)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    ai_criteria: Mapped[list] = mapped_column(JSON, default=list)  # [{text, status, quote}] por critério da norma
    claude_review: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # parecer do revisor Claude (ver /reviews)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
    assessment: Mapped[Assessment] = relationship(back_populates="answers")
