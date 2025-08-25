import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, JSON, Float, Boolean, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from .database import Base

def _uuid():
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dataset_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    inference_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    headers_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    hmac_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thresholds_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    baseline_run_id: Mapped[str | None] = mapped_column(String, ForeignKey("runs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    baseline_run_id: Mapped[str | None] = mapped_column(String, ForeignKey("runs.id"), nullable=True)

    runs: Mapped[list["Run"]] = relationship(
        "Run",
        back_populates="project",
        foreign_keys="Run.project_id",
        cascade="all, delete-orphan",
    )
    
    baseline_run: Mapped["Run"] = relationship(
        "Run",
        foreign_keys="[Project.baseline_run_id]",
        uselist=False,
        post_update=True,
    )

class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    tag: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="queued")  # queued|running|done|failed
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    totals_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="runs",
        foreign_keys="Run.project_id",
    )
    samples: Mapped[list["Sample"]] = relationship("Sample", back_populates="run", cascade="all, delete-orphan")

class Sample(Base):
    __tablename__ = "samples"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("runs.id"), nullable=False)
    test_id: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=True)
    reference_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Optional embedding for similarity/dedup
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)

    run: Mapped["Run"] = relationship("Run", back_populates="samples")
    checks: Mapped[list["CheckResult"]] = relationship("CheckResult", back_populates="sample", cascade="all, delete-orphan")

class CheckResult(Base):
    __tablename__ = "check_results"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    sample_id: Mapped[str] = mapped_column(String, ForeignKey("samples.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # json_validity|regex_policy|pii|length_bounds|similarity|toxicity
    score: Mapped[float] = mapped_column(Float, default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    details_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    sample: Mapped["Sample"] = relationship("Sample", back_populates="checks")
