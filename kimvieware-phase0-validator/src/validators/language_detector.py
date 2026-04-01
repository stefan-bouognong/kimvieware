"""
Language Detector
Detects programming language of SUT
"""
from pathlib import Path
from typing import Dict, Optional
import logging


class LanguageDetector:
    """
    Detect programming language and framework from source directory
    
    Supports:
    - Python (.py) - including Django
    - C (.c, .h)
    - C++ (.cpp, .cc, .cxx, .hpp, .h)
    - Java (.java) - including Spring Boot
    """
    
    LANGUAGE_EXTENSIONS = {
        'python': {'.py'},
        'c': {'.c', '.h'},
        'cpp': {'.cpp', '.cc', '.cxx', '.hpp', '.hh', '.h++'},
        'java': {'.java'},
    }
    SUPPORTED_LANGUAGES = set(LANGUAGE_EXTENSIONS.keys())
    
    FRAMEWORK_INDICATORS = {
        'django': ['manage.py', 'settings.py', 'urls.py', 'wsgi.py', 'asgi.py'],
        'spring_boot': ['pom.xml', 'build.gradle', 'application.properties', 'application.yml', 'src/main/java'],
        'flask': ['app.py', 'application.py', 'run.py', 'requirements.txt'],
    }
    
    @classmethod
    def detect(cls, source_dir: Path, logger: logging.Logger = logging.getLogger(__name__)) -> Dict[str, any]:
        """
        Detect language from source directory while ignoring heavy directories (venv, node_modules).
        """
        logger.info(f"🔍 Detecting language in {source_dir}")
        
        # Directories to strictly ignore
        ignore_dirs = {
            'venv', '.venv', 'env', '.env', 'node_modules', 
            '__pycache__', '.git', '.pytest_cache', '.idea', '.vscode',
            'site-packages', 'dist', 'build'
        }
        
        # Count files by extension
        extension_counts = {}
        all_files = []
        
        # Recursive glob, but we'll manually filter out ignored directories
        for path in source_dir.rglob('*'):
            # Check if any part of the path is in our ignore list
            path_parts = set(path.parts)
            if any(ignore in path_parts for ignore in ignore_dirs):
                continue
            
            if path.is_file():
                suffix = path.suffix.lower()
                for lang, exts in cls.LANGUAGE_EXTENSIONS.items():
                    if suffix in exts:
                        all_files.append(path)
                        extension_counts[suffix] = extension_counts.get(suffix, 0) + 1
        
        if not all_files:
            logger.warning("No source files found in authorized directories")
            return {
                'language': 'unknown',
                'files': [],
                'entry_point': None,
                'confidence': 0.0
            }
        
        # Determine language by file counts
        python_count = sum(extension_counts.get(ext, 0) for ext in cls.LANGUAGE_EXTENSIONS['python'])
        c_count = extension_counts.get('.c', 0)
        cpp_count = sum(extension_counts.get(ext, 0) for ext in cls.LANGUAGE_EXTENSIONS['cpp'] if ext != '.h')
        java_count = extension_counts.get('.java', 0)
        
        total_count = python_count + c_count + cpp_count + java_count
        
        # Determine primary language
        if python_count > max(c_count, cpp_count, java_count):
            language = 'python'
            confidence = python_count / total_count if total_count > 0 else 0
            source_files = [f for f in all_files if f.suffix == '.py']
        elif java_count > max(c_count, cpp_count):
            language = 'java'
            confidence = java_count / total_count if total_count > 0 else 0
            source_files = [f for f in all_files if f.suffix == '.java']
        elif cpp_count > c_count:
            language = 'cpp'
            confidence = cpp_count / total_count if total_count > 0 else 0
            source_files = [f for f in all_files if f.suffix in cls.LANGUAGE_EXTENSIONS['cpp']]
        elif c_count > 0:
            language = 'c'
            confidence = c_count / total_count if total_count > 0 else 0
            source_files = [f for f in all_files if f.suffix in {'.c', '.h'}]
        else:
            language = 'unknown'
            confidence = 0.0
            source_files = all_files
        
        # Find entry point
        entry_point = cls._find_entry_point(source_dir, language, source_files)
        
        # Detect framework
        framework = cls._detect_framework(source_dir, language, logger)
        
        logger.info(f"✅ Detected: {language} ({confidence:.0%} confidence)")
        if framework:
            logger.info(f"   Framework: {framework}")
        logger.info(f"   Files: {len(source_files)}")
        if entry_point:
            logger.info(f"   Entry: {entry_point.name}")
        
        return {
            'language': language,
            'framework': framework,
            'files': source_files,
            'entry_point': entry_point,
            'confidence': confidence,
            'file_count': len(source_files)
        }
    
    @classmethod
    def _find_entry_point(cls, source_dir: Path, language: str, files: list) -> Optional[Path]:
        """Find main entry point file"""
        
        if language == 'python':
            # Look for main.py, app.py, __main__.py
            candidates = ['main.py', 'app.py', '__main__.py', 'run.py']
            for candidate in candidates:
                main_file = source_dir / candidate
                if main_file.exists():
                    return main_file
            
            # Look in src/
            src_dir = source_dir / 'src'
            if src_dir.exists():
                for candidate in candidates:
                    main_file = src_dir / candidate
                    if main_file.exists():
                        return main_file
            
            # Return first .py file
            if files:
                return files[0]
        
        elif language in ['c', 'cpp']:
            # Look for main.c, main.cpp
            candidates = ['main.c', 'main.cpp', 'app.c', 'app.cpp']
            
            for candidate in candidates:
                main_file = source_dir / candidate
                if main_file.exists():
                    return main_file
            
            # Look in src/
            src_dir = source_dir / 'src'
            if src_dir.exists():
                for candidate in candidates:
                    main_file = src_dir / candidate
                    if main_file.exists():
                        return main_file
            
            # Look for files with main() function
            for file in files:
                if file.suffix in {'.c', '.cpp'}:
                    try:
                        content = file.read_text()
                        if 'int main(' in content or 'void main(' in content:
                            return file
                    except:
                        continue
            
            # Return first source file
            if files:
                return files[0]
        
        elif language == 'java':
            # Look for Main.java, App.java, Application.java
            candidates = ['Main.java', 'App.java', 'Application.java']
            
            for candidate in candidates:
                for java_file in files:
                    if java_file.name == candidate:
                        return java_file
            
            # Look for files with main() method
            for file in files:
                try:
                    content = file.read_text()
                    if 'public static void main(' in content:
                        return file
                except:
                    continue
            
            # Return first Java file
            if files:
                return files[0]
        
        return None

    @classmethod
    def _detect_framework(cls, source_dir: Path, language: str, logger: logging.Logger) -> Optional[str]:
        """Detect framework based on project structure and files"""
        
        # Check for Django indicators
        if language == 'python':
            django_score = 0
            for indicator in cls.FRAMEWORK_INDICATORS['django']:
                if (source_dir / indicator).exists():
                    django_score += 1
            if django_score >= 2:  # At least 2 Django files
                return 'django'
            
            # Check for Flask
            flask_score = 0
            for indicator in cls.FRAMEWORK_INDICATORS['flask']:
                if (source_dir / indicator).exists():
                    flask_score += 1
            if flask_score >= 1:
                return 'flask'
        
        # Check for Spring Boot indicators
        elif language == 'java':
            spring_score = 0
            for indicator in cls.FRAMEWORK_INDICATORS['spring_boot']:
                if indicator == 'src/main/java':
                    if (source_dir / indicator).exists():
                        spring_score += 1
                elif (source_dir / indicator).exists():
                    spring_score += 1
            if spring_score >= 2:  # At least pom.xml/build.gradle and application.properties
                return 'spring_boot'
        
        return None

    @classmethod
    def find_entry_point(cls, files: list, language: str) -> Optional[Path]:
        """Public helper: find entry point given a list of Path objects and language."""
        # If detect already found an entry inside files list, prefer it
        # files may be a list of Path objects
        try:
            # Try to infer a common source root
            # Use parent of first file when available
            source_dir = files[0].parents[0] if files else Path('.')
        except Exception:
            source_dir = Path('.')

        # Delegate to internal finder which accepts source_dir context
        return cls._find_entry_point(source_dir, language, files)