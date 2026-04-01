"""
Phase 1: Path Extractor Service

Consumes: validation.completed
Produces: extraction.completed
"""
import sys
from pathlib import Path
import os
from datetime import datetime, timezone # Import timezone

from kimvieware_shared import MicroserviceBase, JobStatus
from extractors import PythonExtractor, CExtractor, JavaExtractor # Import CExtractor and JavaExtractor

class ExtractorService(MicroserviceBase):
    """Phase 1: Symbolic Execution Path Extractor"""
    
    def __init__(self):
        super().__init__(
            service_name="Phase1_Extractor",
            input_queue="validation.completed",
            output_queue="extraction.completed"
        )
        
        # Load max_paths from environment variable, default to 1000
        self.max_paths = int(os.getenv('EXTRACTOR_MAX_PATHS', '1000'))
        
        # Initialize extractors
        self.python_extractor = PythonExtractor(max_paths=self.max_paths)
        self.c_extractor = CExtractor(max_paths=self.max_paths) # Initialize CExtractor
        self.java_extractor = JavaExtractor(max_paths=self.max_paths) # Initialize JavaExtractor
    
    def process_message(self, message: dict) -> dict:
        """Extract symbolic execution paths"""
        
        job_id = message['job_id']
        
        # Only process validated jobs
        if message.get('status') != JobStatus.VALIDATED.value:
            self.logger.warning(f"[{job_id}] Skipping or failing job: status is not 'validated'. Current status: {message.get('status')}")
            # Optionally, return a failed response to mark it as explicitly failed
            return self._error_response(job_id, f"Job was not validated. Current status: {message.get('status')}")
        
        sut_info = message['sut_info']
        extracted_path = Path(message['extracted_path'])
        language = sut_info['language']
        
        self.logger.info(f"[{job_id}] Extracting paths from {language} service")
        self.logger.info(f"[{job_id}] Path: {extracted_path}")
        self.logger.info(f"[{job_id}] Entry point: {sut_info.get('entry_point')}")
        
        # Extract based on language
        if language == 'python':
            trajectories = self.python_extractor.extract_paths(extracted_path)
        
        elif language == 'java':
            self.logger.info(f"[{job_id}] Using Java extractor")
            trajectories = self.java_extractor.extract_paths(extracted_path)
        
        elif language in ['c', 'cpp']:
            self.logger.info(f"[{job_id}] Using C/C++ extractor")
            trajectories = self.c_extractor.extract_paths(extracted_path)
        
        else:
            return self._error_response(job_id, f"Unsupported language: {language}")
        
        self.logger.info(f"[{job_id}]  Extracted {len(trajectories)} trajectories")
        
        # Return result
        return {
            'job_id': job_id,
            'status': JobStatus.EXTRACTED.value,
            'sut_info': sut_info,
            'trajectories_count': len(trajectories),
            'trajectories': [t.to_dict() for t in trajectories],  # NO LIMIT
            'metadata': {
                'language': language,
                'extractor': 'python' if language == 'python' else ('clang' if language in ['c', 'cpp'] else 'javalang'),
                'trajectories_count': len(trajectories),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
    
    def _error_response(self, job_id: str, error: str) -> dict:
        """Error response"""
        return {
            'job_id': job_id,
            'status': JobStatus.FAILED.value,
            'error': error,
            'phase': 'extraction'
        }

if __name__ == "__main__":
    service = ExtractorService()
    service.start()