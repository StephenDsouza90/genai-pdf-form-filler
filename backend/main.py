import os
import uuid
import logging
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import SessionLocal, engine
from models import Base, FormSession, FormField
from schemas import (
    FormSessionResponse, 
    FormFieldResponse, 
    QuestionResponse, 
    AnswerRequest, 
    FormCompletionResponse
)
from services.pdf_service import PDFService
from services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="AI PDF Form Filler API",
    description="API for filling PDF forms using AI-guided conversations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize services
pdf_service = PDFService()
ai_service = AIService()

# Ensure upload directory exists
os.makedirs(os.getenv("UPLOAD_DIR", "uploads"), exist_ok=True)

@app.get("/")
async def root():
    return {"message": "AI PDF Form Filler API"}


@app.post("/upload", response_model=FormSessionResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF form and extract its fields
    """
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    max_size = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB default
    if file.size and file.size > max_size:
        raise HTTPException(status_code=400, detail="File size exceeds limit")
    
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Save uploaded file
        upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        file_path = os.path.join(upload_dir, f"{session_id}.pdf")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"PDF uploaded: {file_path}")

        # Extract form fields
        fields = pdf_service.extract_form_fields(file_path)
        logger.info(f"Extracted fields: {fields}")

        if len(fields) == 0:
            raise HTTPException(status_code=400, detail="No form fields found in PDF")
        

        logger.info(f"Creating form session with ID: {session_id}")
        # Create form session in database
        form_session = FormSession(
            session_id=session_id,
            filename=file.filename,
            file_path=file_path,
            total_fields=len(fields),
            filled_fields=0,
            status="active"
        )
        db.add(form_session)
        db.flush()
        logger.info(f"Form session created: {form_session}")
        
        logger.info("Saving form fields to database")
        # Save form fields to database
        for field_name, field_type in fields.items():
            form_field = FormField(
                session_id=session_id,
                field_name=field_name,
                field_type=field_type,
                is_filled=False
            )
            db.add(form_field)
        
        db.commit()
        logger.info("Form fields saved successfully")
        
        return FormSessionResponse(
            session_id=session_id,
            filename=file.filename,
            total_fields=len(fields),
            status="active"
        )
        
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.get("/session/{session_id}/fields", response_model=List[FormFieldResponse])
async def get_session_fields(session_id: str, db: Session = Depends(get_db)):
    """
    Get all fields for a form session
    """
    fields = db.query(FormField).filter(FormField.session_id == session_id).all()
    if not fields:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return [
        FormFieldResponse(
            field_name=field.field_name,
            field_type=field.field_type,
            is_filled=field.is_filled,
            value=field.value
        ) for field in fields
    ]


@app.get("/session/{session_id}/question", response_model=QuestionResponse)
async def get_next_question(session_id: str, db: Session = Depends(get_db)):
    """
    Get the next question for the user to answer
    """
    # Check if session exists
    session = db.query(FormSession).filter(FormSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get unfilled fields
    unfilled_fields = db.query(FormField).filter(
        FormField.session_id == session_id,
        FormField.is_filled == False
    ).all()
    
    if not unfilled_fields:
        return QuestionResponse(
            question="All fields have been filled! You can now download your completed form.",
            field_name=None,
            field_type=None,
            is_complete=True
        )
    
    # Get the next field to fill
    next_field = unfilled_fields[0]
    
    # Generate AI question
    question = await ai_service.generate_question(next_field.field_name, next_field.field_type)
    
    return QuestionResponse(
        question=question,
        field_name=next_field.field_name,
        field_type=next_field.field_type,
        is_complete=False
    )


@app.post("/session/{session_id}/answer")
async def submit_answer(
    session_id: str,
    answer_data: AnswerRequest,
    db: Session = Depends(get_db)
):
    """
    Submit an answer for a specific field
    """
    # Find the field
    field = db.query(FormField).filter(
        FormField.session_id == session_id,
        FormField.field_name == answer_data.field_name
    ).first()
    
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    
    # Process answer with AI if needed
    processed_value = ai_service.process_answer(
        answer_data.answer, 
        field.field_type,
        field.field_name
    )
    
    # Update field
    field.value = processed_value
    field.is_filled = True
    
    # Update session progress
    session = db.query(FormSession).filter(FormSession.session_id == session_id).first()
    session.filled_fields += 1
    
    if session.filled_fields >= session.total_fields:
        session.status = "completed"
    
    db.commit()
    
    return {"message": "Answer submitted successfully", "processed_value": processed_value}


@app.get("/session/{session_id}/complete", response_model=FormCompletionResponse)
async def complete_form(session_id: str, db: Session = Depends(get_db)):
    """
    Complete the form filling and generate the filled PDF
    """
    # Get session
    session = db.query(FormSession).filter(FormSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get all filled fields
    fields = db.query(FormField).filter(FormField.session_id == session_id).all()
    
    # Check if all fields are filled
    unfilled_count = sum(1 for field in fields if not field.is_filled)
    if unfilled_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Form incomplete. {unfilled_count} fields remaining."
        )
    
    try:
        # Create field mapping
        field_values = {field.field_name: field.value for field in fields if field.value}
        
        # Fill the PDF
        output_path = pdf_service.fill_pdf_form(session.file_path, field_values, session_id)
        
        # Update session
        session.output_path = output_path
        session.status = "completed"
        db.commit()
        
        return FormCompletionResponse(
            session_id=session_id,
            download_url=f"/download/{session_id}",
            filled_fields=len(field_values),
            total_fields=session.total_fields
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing form: {str(e)}")


@app.get("/download/{session_id}")
async def download_completed_form(session_id: str, db: Session = Depends(get_db)):
    """
    Download the completed PDF form
    """
    session = db.query(FormSession).filter(FormSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.output_path or not os.path.exists(session.output_path):
        raise HTTPException(status_code=404, detail="Completed form not found")
    
    return FileResponse(
        session.output_path,
        media_type="application/pdf",
        filename=f"completed_{session.filename}"
    )


@app.get("/session/{session_id}/status")
async def get_session_status(session_id: str, db: Session = Depends(get_db)):
    """
    Get session status and progress
    """
    session = db.query(FormSession).filter(FormSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "status": session.status,
        "filled_fields": session.filled_fields,
        "total_fields": session.total_fields,
        "progress": (session.filled_fields / session.total_fields) * 100 if session.total_fields > 0 else 0
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI PDF Form Filler API"}
