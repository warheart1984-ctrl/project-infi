"""Flask API for multi-modal AI system"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from src.models import MultiModalAI
from src.logger import get_logger
from src.config import get_config
from src.conversation_memory import conversation_memory
from src.document_rag import document_store, build_rag_prompt
from src.speech import speech_to_text, text_to_speech
from src.text_classifier import text_classifier
from src.video_processor import video_processor
from src.streaming import StreamingTextGenerator, create_sse_generator
import base64
import tempfile
import os
from io import BytesIO
from PIL import Image
import traceback

logger = get_logger(__name__)
config = get_config()

app = Flask(__name__)
CORS(app)

# Initialize AI model
ai_model = None
streaming_generator = None


def init_ai():
    """Initialize AI model on startup"""
    global ai_model, streaming_generator
    if ai_model is None:
        logger.info("Initializing AI model...")
        ai_model = MultiModalAI()
        streaming_generator = StreamingTextGenerator(
            model=ai_model.text_model,
            tokenizer=ai_model.text_tokenizer,
            device=ai_model.device,
        )
        logger.info("AI model initialized")


@app.before_request
def before_request():
    """Initialize AI before first request and track timing"""
    import time as _time
    request._start_time = _time.perf_counter()
    init_ai()


@app.after_request
def after_request(response):
    """Add performance timing header to every response"""
    import time as _time
    start = getattr(request, "_start_time", None)
    if start:
        elapsed_ms = (_time.perf_counter() - start) * 1000
        response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.1f}"
    return response


# ──────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "model": "AAIS Multi-Modal AI"})


# ──────────────────────────────────────────────
# Text Generation
# ──────────────────────────────────────────────

@app.route("/api/text/generate", methods=["POST"])
def generate_text():
    """Generate text from prompt"""
    try:
        data = request.json
        prompt = data.get("prompt")
        max_length = data.get("max_length", 512)
        temperature = data.get("temperature", 0.7)

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        result = ai_model.generate_text(prompt, max_length, temperature)
        return jsonify({"generated_text": result})

    except Exception as e:
        logger.error(f"Error in generate_text: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Streaming Text Generation (SSE)
# ──────────────────────────────────────────────

@app.route("/api/text/stream", methods=["POST"])
def stream_text():
    """Stream text generation token-by-token via Server-Sent Events"""
    try:
        data = request.json
        prompt = data.get("prompt")
        max_new_tokens = data.get("max_new_tokens", 512)
        temperature = data.get("temperature", 0.7)

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        stream = streaming_generator.generate_stream(
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )

        return Response(
            create_sse_generator(stream),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        logger.error(f"Error in stream_text: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Image Endpoints
# ──────────────────────────────────────────────

@app.route("/api/image/analyze", methods=["POST"])
def analyze_image():
    """Analyze image and generate description"""
    try:
        if "image" not in request.files:
            return jsonify({"error": "Image file is required"}), 400

        image_file = request.files["image"]
        image = Image.open(image_file.stream).convert("RGB")

        result = ai_model.analyze_image(image)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in analyze_image: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/image/generate", methods=["POST"])
def generate_image():
    """Generate image from text prompt"""
    try:
        data = request.json
        prompt = data.get("prompt")
        num_steps = data.get("num_inference_steps", 50)

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        image = ai_model.generate_image(prompt, num_steps)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode()

        return jsonify({"image": image_base64, "format": "png"})

    except Exception as e:
        logger.error(f"Error in generate_image: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/multimodal/query", methods=["POST"])
def multimodal_query():
    """Process combined text and image query"""
    try:
        text_prompt = request.form.get("prompt")
        image = None

        if not text_prompt:
            return jsonify({"error": "Prompt is required"}), 400

        if "image" in request.files:
            image_file = request.files["image"]
            image = Image.open(image_file.stream).convert("RGB")

        result = ai_model.multimodal_query(text_prompt, image)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in multimodal_query: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Conversation Memory / Chat
# ──────────────────────────────────────────────

@app.route("/api/chat/sessions", methods=["POST"])
def create_chat_session():
    """Create a new chat session"""
    try:
        data = request.json or {}
        system_prompt = data.get("system_prompt")
        session_id = conversation_memory.create_session(system_prompt=system_prompt)
        return jsonify({"session_id": session_id}), 201

    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/sessions", methods=["GET"])
def list_chat_sessions():
    """List all active chat sessions"""
    return jsonify({"sessions": conversation_memory.list_sessions()})


@app.route("/api/chat/sessions/<session_id>", methods=["GET"])
def get_chat_session(session_id):
    """Get conversation history for a session"""
    session = conversation_memory.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found or expired"}), 404
    return jsonify(session.to_dict())


@app.route("/api/chat/sessions/<session_id>", methods=["DELETE"])
def delete_chat_session(session_id):
    """Delete a chat session"""
    if conversation_memory.delete_session(session_id):
        return jsonify({"message": "Session deleted"})
    return jsonify({"error": "Session not found"}), 404


@app.route("/api/chat/sessions/<session_id>/message", methods=["POST"])
def chat_message(session_id):
    """Send a message in a chat session (with conversation memory)"""
    try:
        session = conversation_memory.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found or expired"}), 404

        data = request.json
        user_message = data.get("message")
        max_length = data.get("max_length", 512)
        temperature = data.get("temperature", 0.7)

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # Add user message and build contextual prompt
        session.add_turn("user", user_message)
        contextual_prompt = session.build_prompt()

        # Generate response with full conversation context
        response_text = ai_model.generate_text(
            contextual_prompt, max_length, temperature
        )

        # Store assistant response
        session.add_turn("assistant", response_text)

        return jsonify({
            "response": response_text,
            "session_id": session_id,
            "turn_count": len(session.turns),
        })

    except Exception as e:
        logger.error(f"Error in chat_message: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/sessions/<session_id>/stream", methods=["POST"])
def chat_message_stream(session_id):
    """Send a message in a chat session with streaming response (SSE)"""
    try:
        session = conversation_memory.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found or expired"}), 404

        data = request.json
        user_message = data.get("message")
        max_new_tokens = data.get("max_new_tokens", 512)
        temperature = data.get("temperature", 0.7)

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        session.add_turn("user", user_message)
        contextual_prompt = session.build_prompt()

        # We need to capture the full response for memory after streaming
        def stream_and_remember():
            full_response = ""
            stream = streaming_generator.generate_stream(
                prompt=contextual_prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
            )
            for chunk in create_sse_generator(stream):
                yield chunk
                # Parse the last token to build full response
                import json as _json
                try:
                    line = chunk.strip()
                    if line.startswith("data: "):
                        payload = _json.loads(line[6:])
                        if payload.get("finished"):
                            full_response = payload.get("text_so_far", full_response)
                except Exception:
                    pass
            session.add_turn("assistant", full_response)

        return Response(
            stream_and_remember(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        logger.error(f"Error in chat_message_stream: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Document / RAG
# ──────────────────────────────────────────────

@app.route("/api/documents", methods=["GET"])
def list_documents():
    """List all ingested documents"""
    return jsonify({"documents": document_store.list_documents()})


@app.route("/api/documents/upload/text", methods=["POST"])
def upload_text_document():
    """Ingest a plain text document"""
    try:
        data = request.json
        text = data.get("text")
        doc_id = data.get("doc_id")

        if not text:
            return jsonify({"error": "Text content is required"}), 400

        result_id = document_store.ingest_text(text, doc_id=doc_id, metadata=data.get("metadata"))
        return jsonify({"doc_id": result_id, "message": "Document ingested"}), 201

    except Exception as e:
        logger.error(f"Error ingesting text: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/upload/pdf", methods=["POST"])
def upload_pdf_document():
    """Ingest a PDF document"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "PDF file is required"}), 400

        pdf_file = request.files["file"]
        doc_id = request.form.get("doc_id")

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_file.save(tmp)
            tmp_path = tmp.name

        try:
            result_id = document_store.ingest_pdf(tmp_path, doc_id=doc_id)
            return jsonify({"doc_id": result_id, "message": "PDF ingested"}), 201
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error ingesting PDF: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/upload/url", methods=["POST"])
def upload_url_document():
    """Ingest a document from a URL"""
    try:
        data = request.json
        url = data.get("url")
        doc_id = data.get("doc_id")

        if not url:
            return jsonify({"error": "URL is required"}), 400

        result_id = document_store.ingest_url(url, doc_id=doc_id)
        return jsonify({"doc_id": result_id, "message": "URL content ingested"}), 201

    except Exception as e:
        logger.error(f"Error ingesting URL: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """Delete an ingested document"""
    if document_store.delete_document(doc_id):
        return jsonify({"message": "Document deleted"})
    return jsonify({"error": "Document not found"}), 404


@app.route("/api/documents/search", methods=["POST"])
def search_documents():
    """Search across ingested documents"""
    try:
        data = request.json
        query = data.get("query")
        top_k = data.get("top_k", 5)
        doc_id = data.get("doc_id")

        if not query:
            return jsonify({"error": "Query is required"}), 400

        results = document_store.search(query, top_k=top_k, doc_id=doc_id)
        return jsonify({"results": results})

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents/ask", methods=["POST"])
def ask_documents():
    """Ask a question grounded in ingested documents (RAG)"""
    try:
        data = request.json
        query = data.get("query")
        top_k = data.get("top_k", 5)
        doc_id = data.get("doc_id")
        max_length = data.get("max_length", 512)

        if not query:
            return jsonify({"error": "Query is required"}), 400

        # Retrieve relevant chunks
        context_chunks = document_store.search(query, top_k=top_k, doc_id=doc_id)

        if not context_chunks:
            return jsonify({
                "answer": "No relevant documents found. Please ingest documents first.",
                "sources": [],
            })

        # Build RAG prompt and generate answer
        rag_prompt = build_rag_prompt(query, context_chunks)
        answer = ai_model.generate_text(rag_prompt, max_length=max_length, temperature=0.3)

        return jsonify({
            "answer": answer,
            "sources": [
                {"doc_id": c["doc_id"], "score": c["score"], "excerpt": c["chunk"][:200]}
                for c in context_chunks
            ],
        })

    except Exception as e:
        logger.error(f"Error in ask_documents: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Speech-to-Text (Whisper)
# ──────────────────────────────────────────────

@app.route("/api/audio/transcribe", methods=["POST"])
def transcribe_audio():
    """Transcribe audio file to text"""
    try:
        if "audio" not in request.files:
            return jsonify({"error": "Audio file is required"}), 400

        audio_file = request.files["audio"]
        language = request.form.get("language")

        # Determine file extension
        filename = audio_file.filename or "audio.wav"
        suffix = os.path.splitext(filename)[1] or ".wav"

        audio_bytes = audio_file.read()
        result = speech_to_text.transcribe_bytes(
            audio_bytes, suffix=suffix, language=language
        )
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in transcribe_audio: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/audio/voice-query", methods=["POST"])
def voice_query():
    """Transcribe audio and use it as a text prompt for AI generation"""
    try:
        if "audio" not in request.files:
            return jsonify({"error": "Audio file is required"}), 400

        audio_file = request.files["audio"]
        filename = audio_file.filename or "audio.wav"
        suffix = os.path.splitext(filename)[1] or ".wav"
        language = request.form.get("language")
        max_length = int(request.form.get("max_length", 512))

        # Transcribe
        audio_bytes = audio_file.read()
        transcription = speech_to_text.transcribe_bytes(
            audio_bytes, suffix=suffix, language=language
        )

        # Generate response from transcribed text
        response_text = ai_model.generate_text(
            transcription["text"], max_length=max_length
        )

        return jsonify({
            "transcription": transcription["text"],
            "response": response_text,
            "language": transcription["language"],
        })

    except Exception as e:
        logger.error(f"Error in voice_query: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Text-to-Speech
# ──────────────────────────────────────────────

@app.route("/api/audio/synthesize", methods=["POST"])
def synthesize_speech():
    """Convert text to speech audio (returns WAV)"""
    try:
        data = request.json
        text = data.get("text")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        wav_bytes = text_to_speech.synthesize_to_wav_bytes(text)
        wav_base64 = base64.b64encode(wav_bytes).decode()

        return jsonify({
            "audio": wav_base64,
            "format": "wav",
            "encoding": "base64",
        })

    except Exception as e:
        logger.error(f"Error in synthesize_speech: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/audio/synthesize/download", methods=["POST"])
def synthesize_speech_download():
    """Convert text to speech and return WAV file directly"""
    try:
        data = request.json
        text = data.get("text")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        wav_bytes = text_to_speech.synthesize_to_wav_bytes(text)

        return Response(
            wav_bytes,
            mimetype="audio/wav",
            headers={"Content-Disposition": "attachment; filename=speech.wav"},
        )

    except Exception as e:
        logger.error(f"Error in synthesize_speech_download: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Sentiment Analysis & Text Classification
# ──────────────────────────────────────────────

@app.route("/api/text/sentiment", methods=["POST"])
def analyze_sentiment():
    """Analyze sentiment of text"""
    try:
        data = request.json
        text = data.get("text")
        texts = data.get("texts")  # For batch

        if texts:
            results = text_classifier.analyze_sentiment_batch(texts)
            return jsonify({"results": results})
        elif text:
            result = text_classifier.analyze_sentiment(text)
            return jsonify(result)
        else:
            return jsonify({"error": "'text' or 'texts' is required"}), 400

    except Exception as e:
        logger.error(f"Error in analyze_sentiment: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/text/classify", methods=["POST"])
def classify_text():
    """Classify text into custom categories (zero-shot)"""
    try:
        data = request.json
        text = data.get("text")
        texts = data.get("texts")  # For batch
        labels = data.get("labels") or data.get("candidate_labels")
        multi_label = data.get("multi_label", False)

        if not labels:
            return jsonify({"error": "'labels' list is required"}), 400

        if texts:
            results = text_classifier.classify_batch(texts, labels, multi_label=multi_label)
            return jsonify({"results": results})
        elif text:
            result = text_classifier.classify(text, labels, multi_label=multi_label)
            return jsonify(result)
        else:
            return jsonify({"error": "'text' or 'texts' is required"}), 400

    except Exception as e:
        logger.error(f"Error in classify_text: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Video Processing
# ──────────────────────────────────────────────

@app.route("/api/video/info", methods=["POST"])
def video_info():
    """Get video metadata"""
    try:
        if "video" not in request.files:
            return jsonify({"error": "Video file is required"}), 400

        video_file = request.files["video"]
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            video_file.save(tmp)
            tmp_path = tmp.name

        try:
            info = video_processor.get_video_info(tmp_path)
            return jsonify(info)
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error in video_info: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/video/extract-frames", methods=["POST"])
def extract_video_frames():
    """Extract frames from a video"""
    try:
        if "video" not in request.files:
            return jsonify({"error": "Video file is required"}), 400

        video_file = request.files["video"]
        num_frames = int(request.form.get("num_frames", 10))

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            video_file.save(tmp)
            tmp_path = tmp.name

        try:
            frames = video_processor.extract_frames(tmp_path, num_frames=num_frames)

            # Convert frame images to base64
            frame_results = []
            for frame in frames:
                with open(frame["path"], "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                frame_results.append({
                    "timestamp": frame["timestamp"],
                    "frame_index": frame["frame_index"],
                    "image": img_b64,
                    "format": "jpg",
                })

            return jsonify({"frames": frame_results, "count": len(frame_results)})
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error in extract_video_frames: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/video/analyze", methods=["POST"])
def analyze_video():
    """Analyze video: extract key frames, analyze each, and generate summary"""
    try:
        if "video" not in request.files:
            return jsonify({"error": "Video file is required"}), 400

        video_file = request.files["video"]
        num_frames = int(request.form.get("num_frames", 8))

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            video_file.save(tmp)
            tmp_path = tmp.name

        try:
            info = video_processor.get_video_info(tmp_path)
            frames = video_processor.extract_frames(tmp_path, num_frames=num_frames)
            analyzed = video_processor.analyze_frames(frames, ai_model)
            summary = video_processor.generate_summary(analyzed, ai_model)

            return jsonify({
                "video_info": info,
                "summary": summary,
                "frames_analyzed": len(analyzed),
            })
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error in analyze_video: {e}")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Error Handlers
# ──────────────────────────────────────────────

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


def run_api(host="0.0.0.0", port=5000, debug=False):
    """Run the Flask API"""
    logger.info(f"Starting API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_api(debug=config.DEBUG)
