from flask import Flask, request, jsonify
import hashlib
import json
import uuid
import time
import logging
from functools import wraps

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simple in-memory cache (you can replace with Redis for production)
haptic_pattern_cache = {}

class HapticTranslateService:
    """
    Service class that converts text to haptic vibration patterns
    according to the Shappe Haptic Communication System.
    """
    
    # Haptic pattern dictionary mapping letters to dot/dash patterns
    HAPTIC_PATTERNS = {
        'A': '•-', 'B': '•–•–', 'C': '••-•', 'D': '•••',
        'E': '•', 'F': '•••-', 'G': '--•',
        'H': '••••', 'I': '••', 'J': '•---',
        'K': '-•-', 'L': '•-••', 'M': '--',
        'N': '-•', 'O': '---', 'P': '•--•',
        'Q': '--•-', 'R': '•-•', 'S': '•–•',
        'T': '-', 'U': '••-', 'V': '•••-',
        'W': '•--', 'X': '-••-', 'Y': '-•--',
        'Z': '--••', ' ': ' ',
        '#': '-',  
        '0': '•-•',  
        '1': '•',   
        '2': '••',  
        '3': '•••', 
        '4': '••••',
        '5': '•••–',    
        '6': '-•',   
        '7': '-••',  
        '8': '-•••', 
        '9': '-••••' 
    }

    # Haptic timing configurations (in milliseconds)
    TIMING = {
        '•': 100,   
        '-': 300,    
        'letter_space': 200,   
        'word_space': 600,    
        'sentence_space': 900
    }

    def _generate_cache_key(self, text, speed_factor, intensity):
        """
        Generate a unique cache key based on text and preferences
        """
        # Create a parameters dictionary
        params_dict = {
            'speed': speed_factor,
            'intensity': intensity,
            'text': text.upper()  # Normalize text case for consistent caching
        }
        
        # Sort the parameters to ensure consistent key generation
        sorted_items = sorted(params_dict.items())
        param_str = json.dumps(sorted_items)
        
        # Create a hash of the parameters
        params_hash = hashlib.md5(param_str.encode()).hexdigest()
        
        # Combine to create a unique key
        return f"haptic_pattern:{params_hash}"

    def _generate_haptic_pattern(self, text, speed_factor=1.0, intensity=0.8, request_id=None):
        """
        Convert text into a sequence of haptic vibration instructions.
        
        Args:
            text (str): The text to convert
            speed_factor (float): Factor to adjust timing (lower = slower)
            intensity (float): Vibration intensity between 0.0 and 1.0
            request_id (str): ID for request tracking in logs
            
        Returns:
            tuple: (pattern list, total duration)
        """
        pattern = []
        total_duration = 0
        
        # Process each character in the text
        text = text.upper()  # Convert to uppercase
        
        logger.debug(f"[{request_id}] Converting {len(text)} characters to haptic pattern")
        
        # Track unsupported characters for logging
        unsupported_chars = set()
        
        for i, char in enumerate(text):
            # Handle end of sentence
            if char in ['.', '!', '?']:
                pause_duration = int(self.TIMING['sentence_space'] / speed_factor)
                pattern.append({
                    'type': 'pause',
                    'duration': pause_duration
                })
                total_duration += pause_duration
                logger.debug(f"[{request_id}] Added end of sentence pause: {pause_duration}ms")
                continue
                
            # Handle spaces (word boundaries)
            if char == ' ':
                pause_duration = int(self.TIMING['word_space'] / speed_factor)
                pattern.append({
                    'type': 'pause',
                    'duration': pause_duration
                })
                total_duration += pause_duration
                logger.debug(f"[{request_id}] Added word space: {pause_duration}ms")
                continue
            
            # Convert character to haptic pattern if it exists in our mapping
            if char in self.HAPTIC_PATTERNS:
                char_pattern = self.HAPTIC_PATTERNS[char]
                
                logger.debug(f"[{request_id}] Processing character '{char}' with pattern '{char_pattern}'")
                
                # Process each symbol in the character pattern
                for symbol in char_pattern:
                    if symbol in ['•', '-']:
                        # Add vibration
                        vibration_duration = int(self.TIMING[symbol] / speed_factor)
                        pattern.append({
                            'type': 'vibrate',
                            'duration': vibration_duration,
                            'intensity': intensity
                        })
                        total_duration += vibration_duration
                    
                    # Add brief pause between symbols within a character
                    if symbol != char_pattern[-1]:  # Not the last symbol
                        pattern.append({
                            'type': 'pause',
                            'duration': 50  # Brief pause between symbols
                        })
                        total_duration += 50
                
                # Add space between letters (but not after the last letter of a word)
                if i < len(text) - 1 and text[i + 1] != ' ':
                    letter_space = int(self.TIMING['letter_space'] / speed_factor)
                    pattern.append({
                        'type': 'pause',
                        'duration': letter_space
                    })
                    total_duration += letter_space
            else:
                # Track unsupported characters
                unsupported_chars.add(char)
                logger.warning(f"[{request_id}] Unsupported character '{char}' at position {i}, skipping")
        
        # Log summary of unsupported characters if any
        if unsupported_chars:
            logger.warning(f"[{request_id}] Found {len(unsupported_chars)} unsupported characters: {', '.join(unsupported_chars)}")
        
        # Add end of message pause
        end_pause = int(self.TIMING['sentence_space'] / speed_factor)
        pattern.append({
            'type': 'pause',
            'duration': end_pause
        })
        total_duration += end_pause
        
        logger.info(f"[{request_id}] Generated pattern with {len(pattern)} elements, " 
                   f"total duration: {total_duration}ms")
        
        return pattern, total_duration

    def translate_text_to_haptic(self, text, speed_factor=1.0, intensity=0.8, use_cache=True, request_id=None):
        """
        Main method to translate text to haptic patterns with caching support.
        """
        start_time = time.time()
        
        logger.info(f"[{request_id}] Processing text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        logger.debug(f"[{request_id}] User preferences: speed={speed_factor}, intensity={intensity}, use_cache={use_cache}")
        
        # Validate preference values
        if not (0.1 <= speed_factor <= 3.0):
            logger.warning(f"[{request_id}] Invalid speed factor: {speed_factor}. Using default 1.0")
            speed_factor = 1.0
            
        if not (0.0 <= intensity <= 1.0):
            logger.warning(f"[{request_id}] Invalid intensity: {intensity}. Using default 0.8")
            intensity = 0.8

        if use_cache:
            # Generate cache key
            cache_key = self._generate_cache_key(text, speed_factor, intensity)
            # Try to get result from cache
            cached_result = haptic_pattern_cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"[{request_id}] Cache HIT for haptic pattern")
                cached_result['cached'] = True
                # Log cache hit timing
                processing_time = (time.time() - start_time) * 1000
                logger.info(f"[{request_id}] Returned cached result in {processing_time:.2f}ms")
                return cached_result
            logger.info(f"[{request_id}] Cache MISS for haptic pattern")
        else:
            logger.info(f"[{request_id}] Cache bypassed as requested")
        
        # Generate haptic pattern
        logger.debug(f"[{request_id}] Generating haptic pattern")
        pattern, total_duration = self._generate_haptic_pattern(
            text, speed_factor, intensity, request_id
        )
        
        # Prepare response data
        response_data = {
            'pattern': pattern,
            'totalDuration': total_duration,
            'characterCount': len(text),
            'text': text,  # echo back the original text
            'cached': False
        }
        
        # Cache the result if caching is enabled
        if use_cache:
            haptic_pattern_cache[cache_key] = response_data.copy()
            logger.info(f"[{request_id}] Cached haptic pattern result")
        
        # Log successful processing with timing information
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        logger.info(f"[{request_id}] Successfully processed haptic translation in {processing_time:.2f}ms. " 
                    f"Pattern length: {len(pattern)}, Duration: {total_duration}ms")
        
        return response_data

# Initialize haptic service
haptic_service = HapticTranslateService()

# Error handler decorator
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as ve:
            logger.error(f"Value error: {str(ve)}")
            return jsonify({'error': f'Invalid input: {str(ve)}'}), 400
        except Exception as e:
            logger.exception(f"Unexpected error: {str(e)}")
            return jsonify({'error': 'Failed to process haptic translation. Please try again later.'}), 500
    return decorated_function

@app.route('/')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Haptic Feedback API',
        'version': '1.0.0'
    })

@app.route('/haptic_translate/', methods=['POST'])
@handle_errors
def haptic_translate():
    """
    API endpoint that converts text to haptic vibration patterns
    according to the Shappe Haptic Communication System.
    
    Expected JSON payload:
    {
        "text": "Hello World",
        "preferences": {
            "speed": 1.0,
            "intensity": 0.8
        },
        "use_cache": true
    }
    """
    # Generate a unique request ID for tracking this request through logs
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    logger.info(f"[{request_id}] Received haptic translation request")
    
    # Get JSON data from request
    data = request.get_json()
    
    if not data:
        logger.warning(f"[{request_id}] No JSON data provided")
        return jsonify({'error': 'JSON data is required'}), 400
    
    # Extract text from request
    text = data.get('text', '')
    if not text:
        logger.warning(f"[{request_id}] Missing 'text' field in request data")
        return jsonify({'error': 'Text field is required'}), 400
    
    # Get user preferences if provided
    preferences = data.get('preferences', {})
    speed_factor = float(preferences.get('speed', 1.0))
    intensity = float(preferences.get('intensity', 0.8))
    
    # Should we use cache? Allow client to bypass cache if needed
    use_cache = data.get('use_cache', True)
    
    # Process the translation
    result = haptic_service.translate_text_to_haptic(
        text=text,
        speed_factor=speed_factor,
        intensity=intensity,
        use_cache=use_cache,
        request_id=request_id
    )
    
    return jsonify(result), 200

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the haptic pattern cache"""
    global haptic_pattern_cache
    cache_size = len(haptic_pattern_cache)
    haptic_pattern_cache.clear()
    logger.info(f"Cache cleared. Removed {cache_size} entries.")
    return jsonify({
        'message': f'Cache cleared successfully. Removed {cache_size} entries.',
        'cache_size': 0
    })

@app.route('/cache/status', methods=['GET'])
def cache_status():
    """Get cache status information"""
    return jsonify({
        'cache_entries': len(haptic_pattern_cache),
        'cache_keys': list(haptic_pattern_cache.keys())[:10]  # Show first 10 keys
    })

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
