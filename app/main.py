import logging
import random
import time
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

# --- OpenTelemetry (tracing) setup ---
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Configure logging (structured)
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger("fastapi-demo")

# Global tracer
tracer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global tracer
    
    # Startup
    logger.info("Starting FastAPI Observability Demo")
    
    # Initialize OpenTelemetry with error handling
    try:
        resource = Resource.create({
            "service.name": "fastapi-demo",
            "service.version": "1.0.0"
        })
        provider = TracerProvider(resource=resource)
        
        # Try to connect to Tempo
        tempo_endpoint = os.getenv("TEMPO_ENDPOINT", "http://tempo:4318/v1/traces")
        exporter = OTLPSpanExporter(endpoint=tempo_endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer(__name__)
        
        logger.info(f"OpenTelemetry configured with endpoint: {tempo_endpoint}")
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        # Create a no-op tracer as fallback
        tracer = trace.NoOpTracer()
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI Observability Demo")

app = FastAPI(
    title="FastAPI Observability Demo",
    description="Demo app with Prometheus metrics, Loki logs, and Tempo traces",
    version="1.0.0",
    lifespan=lifespan
)

# Prometheus metrics for FastAPI
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="fastapi_inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app).expose(app)

# Auto-instrument FastAPI & requests
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

@app.get("/")
def root():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return {"message": "FastAPI Observability Demo", "status": "healthy"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "fastapi-demo"}

@app.get("/hello")
def hello():
    """Demo endpoint with simulated work, logging, and tracing"""
    try:
        # Simulate variable latency (100–800 ms)
        delay = random.uniform(0.1, 0.8)
        
        with tracer.start_as_current_span("work-simulation") as span:
            if span.is_recording():
                span.set_attribute("app.delay_seconds", delay)
                span.set_attribute("app.endpoint", "/hello")
            
            # Simulate some work
            time.sleep(delay)
            
            # Random chance of "error" for demo purposes
            if random.random() < 0.1:  # 10% chance
                logger.warning("Simulated warning condition", extra={
                    "delay": delay,
                    "endpoint": "/hello",
                    "warning_type": "simulated"
                })
        
        logger.info("Hello endpoint accessed successfully", extra={
            "delay": delay,
            "endpoint": "/hello",
            "status": "success"
        })
        
        return {
            "message": "Hello, World!",
            "delay_seconds": round(delay, 3),
            "timestamp": time.time(),
            "service": "fastapi-demo"
        }
        
    except Exception as e:
        logger.error(f"Error in hello endpoint: {e}", extra={
            "endpoint": "/hello",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/slow")
def slow_endpoint():
    """Intentionally slow endpoint for testing"""
    delay = random.uniform(2.0, 5.0)
    
    with tracer.start_as_current_span("slow-operation") as span:
        if span.is_recording():
            span.set_attribute("app.delay_seconds", delay)
            span.set_attribute("app.endpoint", "/slow")
        
        time.sleep(delay)
    
    logger.info("Slow endpoint accessed", extra={
        "delay": delay,
        "endpoint": "/slow"
    })
    
    return {"message": "This was slow!", "delay_seconds": round(delay, 3)}

@app.get("/error")
def error_endpoint():
    """Endpoint that always returns an error for testing"""
    logger.error("Error endpoint accessed", extra={
        "endpoint": "/error",
        "error_type": "intentional"
    })
    raise HTTPException(status_code=500, detail="This is an intentional error for testing")

