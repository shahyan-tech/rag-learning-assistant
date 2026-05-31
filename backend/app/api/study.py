import json

from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.db.models import StudyArtifact
from app.db.session import get_db
from app.models.study import (
    DeleteStudyArtifactResponse,
    FlashcardRequest,
    FlashcardResponse,
    MindMapRequest,
    MindMapResponse,
    QuizRequest,
    QuizResponse,
    StudyArtifactDetail,
    StudyArtifactSummary,
)
from app.study.generators import (
    generate_flashcards,
    generate_mindmap,
    generate_quiz,
)


router = APIRouter(
    prefix="/study",
    tags=["Study Tools"],
)


def save_study_artifact(
    db: Session,
    artifact_type: str,
    topic: str,
    payload: dict,
    sources: list,
) -> StudyArtifact:
    artifact = StudyArtifact(
        artifact_type=artifact_type,
        topic=topic,
        payload_json=json.dumps(payload, ensure_ascii=False),
        sources_json=json.dumps(sources, ensure_ascii=False),
    )

    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return artifact


def parse_json_field(value: str | None, fallback):
    if not value:
        return fallback

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


@router.post("/flashcards", response_model=FlashcardResponse)
def create_flashcards(
    request: FlashcardRequest,
    db: Session = Depends(get_db),
):
    try:
        result = generate_flashcards(
            topic=request.topic,
            count=request.count,
            n_results=request.n_results,
        )

        artifact = save_study_artifact(
            db=db,
            artifact_type="flashcards",
            topic=request.topic,
            payload={
                "topic": result["topic"],
                "flashcards": result["flashcards"],
            },
            sources=result.get("sources", []),
        )

        return {
            "artifact_id": artifact.id,
            "topic": result["topic"],
            "flashcards": result["flashcards"],
            "sources": result.get("sources", []),
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate flashcards: {str(error)}",
        )


@router.post("/quiz", response_model=QuizResponse)
def create_quiz(
    request: QuizRequest,
    db: Session = Depends(get_db),
):
    try:
        result = generate_quiz(
            topic=request.topic,
            count=request.count,
            difficulty=request.difficulty,
            n_results=request.n_results,
        )

        artifact = save_study_artifact(
            db=db,
            artifact_type="quiz",
            topic=request.topic,
            payload={
                "topic": result["topic"],
                "difficulty": result["difficulty"],
                "questions": result["questions"],
            },
            sources=result.get("sources", []),
        )

        return {
            "artifact_id": artifact.id,
            "topic": result["topic"],
            "difficulty": result["difficulty"],
            "questions": result["questions"],
            "sources": result.get("sources", []),
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quiz: {str(error)}",
        )


@router.post("/mindmap", response_model=MindMapResponse)
def create_mindmap(
    request: MindMapRequest,
    db: Session = Depends(get_db),
):
    try:
        result = generate_mindmap(
            topic=request.topic,
            n_results=request.n_results,
        )

        artifact = save_study_artifact(
            db=db,
            artifact_type="mindmap",
            topic=request.topic,
            payload={
                "topic": result["topic"],
                "mind_map": result["mind_map"],
            },
            sources=result.get("sources", []),
        )

        return {
            "artifact_id": artifact.id,
            "topic": result["topic"],
            "mind_map": result["mind_map"],
            "sources": result.get("sources", []),
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate mind map: {str(error)}",
        )


@router.get("/artifacts", response_model=list[StudyArtifactSummary])
def list_study_artifacts(db: Session = Depends(get_db)):
    artifacts = (
        db.query(StudyArtifact)
        .order_by(StudyArtifact.created_at.desc())
        .all()
    )

    return [
        {
            "id": artifact.id,
            "artifact_type": artifact.artifact_type,
            "topic": artifact.topic,
            "created_at": artifact.created_at,
        }
        for artifact in artifacts
    ]


@router.get("/artifacts/{artifact_id}", response_model=StudyArtifactDetail)
def get_study_artifact(
    artifact_id: int,
    db: Session = Depends(get_db),
):
    artifact = (
        db.query(StudyArtifact)
        .filter(StudyArtifact.id == artifact_id)
        .first()
    )

    if not artifact:
        raise HTTPException(
            status_code=404,
            detail=f"Study artifact {artifact_id} not found.",
        )

    return {
        "id": artifact.id,
        "artifact_type": artifact.artifact_type,
        "topic": artifact.topic,
        "payload": parse_json_field(artifact.payload_json, {}),
        "sources": parse_json_field(artifact.sources_json, []),
        "created_at": artifact.created_at,
    }


@router.delete("/artifacts/{artifact_id}", response_model=DeleteStudyArtifactResponse)
def delete_study_artifact(
    artifact_id: int,
    db: Session = Depends(get_db),
):
    artifact = (
        db.query(StudyArtifact)
        .filter(StudyArtifact.id == artifact_id)
        .first()
    )

    if not artifact:
        raise HTTPException(
            status_code=404,
            detail=f"Study artifact {artifact_id} not found.",
        )

    db.delete(artifact)
    db.commit()

    return {
        "message": "Study artifact deleted successfully.",
        "artifact_id": artifact_id,
    }