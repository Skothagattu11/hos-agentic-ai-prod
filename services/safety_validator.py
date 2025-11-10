"""
Safety Validator Service - Ensures AI-generated plans comply with non-medical guidelines

Purpose:
- Prevent medical advice (medications, supplements, specific diagnoses)
- Prevent specific meal recommendations (e.g., "eat grilled salmon")
- Allow generalized routines (e.g., "have lunch", "eat protein-rich meal")
- Flag violations for monitoring and improvement

Author: HolisticOS Team
Date: 2025-11-10
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Configuration
SAFE_ROUTINE_MODE = os.getenv('SAFE_ROUTINE_MODE', 'true').lower() == 'true'
VALIDATE_GENERATED_PLANS = os.getenv('VALIDATE_GENERATED_PLANS', 'true').lower() == 'true'
BLOCK_UNSAFE_PLANS = os.getenv('BLOCK_UNSAFE_PLANS', 'false').lower() == 'true'
LOG_SAFETY_VIOLATIONS = os.getenv('LOG_SAFETY_VIOLATIONS', 'true').lower() == 'true'


class SafetyViolation:
    """Represents a safety violation found in generated content"""

    def __init__(self, category: str, severity: str, location: str, content: str, reason: str):
        self.category = category  # 'medical_advice', 'specific_meal', 'supplement'
        self.severity = severity  # 'high', 'medium', 'low'
        self.location = location  # Where in plan (e.g., 'plan_items[3].description')
        self.content = content    # The problematic text
        self.reason = reason      # Why it's flagged
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'category': self.category,
            'severity': self.severity,
            'location': self.location,
            'content': self.content,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat()
        }


class SafetyValidator:
    """
    Validates generated routine plans for safety compliance

    PROHIBITED:
    - Medical advice (diagnoses, medications, supplements)
    - Specific meal recommendations ("eat grilled salmon")
    - Dosage instructions ("take 500mg of...")

    ALLOWED:
    - Generalized routines ("have lunch", "eat protein-rich meal")
    - Activity recommendations ("morning meditation", "30-min walk")
    - Hydration reminders ("drink water")
    """

    # PROHIBITED PATTERNS

    # Medical terms that should NEVER appear
    MEDICAL_PROHIBITED = [
        # Medications
        r'\b(aspirin|ibuprofen|advil|tylenol|metformin|lisinopril|atorvastatin)\b',
        r'\b(prescription|medication|medicine|drug|pill|tablet|capsule)\b',
        r'\b(dosage|mg|milligram|mcg|microgram|ml|milliliter)\b',

        # Supplements (specific brands/dosages)
        r'\b(vitamin [A-Z]\d*|multivitamin|omega-3|fish oil|probiotics)\b',
        r'\b(supplement|supplementation|take.*capsule)\b',
        r'\b(\d+\s*mg|\d+\s*mcg|\d+\s*iu)\b',  # Dosages

        # Medical conditions/diagnoses
        r'\b(diagnose|diagnosis|treat|treatment|cure|disease|disorder|syndrome)\b',
        r'\b(diabetes|hypertension|depression|anxiety disorder|ADHD)\b',

        # Medical advice language
        r'\b(consult.*doctor|see.*physician|medical professional)\b',
        r'\b(prescribe|prescription required)\b',
    ]

    # Specific food items (too prescriptive)
    SPECIFIC_FOOD_PROHIBITED = [
        # Specific proteins
        r'\b(grilled salmon|chicken breast|turkey|steak|pork chop)\b',
        r'\b(tilapia|cod|tuna|shrimp|lobster)\b',

        # Specific meals/recipes
        r'\b(avocado toast|quinoa bowl|kale salad|smoothie bowl)\b',
        r'\b(overnight oats|greek yogurt|protein shake|energy bar)\b',
        r'\b(poached egg|scrambled egg|fried egg|boiled egg)\b',
        r'\b(mashed avocado|sliced banana|diced tomato)\b',

        # Specific grains/carbs
        r'\b(whole grain toast|white rice|brown rice|quinoa|oatmeal)\b',
        r'\b(whole wheat|multigrain|sourdough bread|toast|bread)\b',
        r'\b(pasta|noodles|cereal|granola)\b',

        # Specific vegetables/fruits - NO SPECIFIC FOOD NAMES
        r'\b(kale|spinach|arugula|romaine|lettuce|cabbage)\b',
        r'\b(blueberries|strawberries|raspberries|banana|apple|orange)\b',
        r'\b(tomato|cucumber|carrot|broccoli|cauliflower)\b',
        r'\b(avocado|lemon|lime|grapefruit|mango|pear)\b',
        r'\b(potato|sweet potato|yam|beet|onion|garlic)\b',

        # Proteins - NO SPECIFIC PROTEINS
        r'\b(egg|eggs|chicken|beef|pork|fish|salmon|tuna)\b',
        r'\b(tofu|tempeh|beans|lentils|chickpeas)\b',

        # Dairy/alternatives
        r'\b(milk|cheese|yogurt|butter|cream)\b',
        r'\b(almond milk|soy milk|oat milk)\b',

        # Beverages - specific types
        r'\b(green tea|black tea|herbal tea|coffee)\b',
        r'\b(juice|smoothie|shake)\b',

        # Specific ingredients with quantities
        r'\b(\d+\s*cups?\s+of|tablespoons?\s+of|ounces?\s+of)\b',
        r'\b(\d+\s*oz|2 eggs|3 oz chicken|1 cup rice)\b',

        # Temperature specifications
        r'\b(\d+\s*-?\s*\d*\s*°?[FC])\b',  # Catches "65-68°F", "20°C", etc.
        r'\b(set.*temperature|room temperature)\b',

        # Brand names
        r'\b(cheerios|kellogg|nature valley|quest bar)\b',

        # Recipe instructions (too specific)
        r'\b(prepare.*with|cook.*with|make.*with)\b',
        r'\b(slice|dice|chop|mash|blend|mix)\b',
    ]

    # ALLOWED PATTERNS (general guidance)
    ALLOWED_GENERAL = [
        r'\b(have lunch|eat lunch|lunch time|lunch)\b',
        r'\b(have dinner|eat dinner|dinner time|dinner)\b',
        r'\b(have breakfast|eat breakfast|morning meal|breakfast)\b',
        r'\b(have a snack|healthy snack|mid-day snack|snack)\b',
        r'\b(protein-rich meal|balanced meal|nutritious meal)\b',
        r'\b(meal with protein|meal with whole grains)\b',
        r'\b(healthy fats|lean protein|complex carbs)\b',  # Categories, not specific foods
        r'\b(hydrate|drink water|water intake|hydration)\b',
        r'\b(warm beverage|hot drink|cold drink)\b',  # Generic beverage types
        r'\b(mindful eating|portion control)\b',
    ]

    def __init__(self):
        """Initialize safety validator"""
        self.enabled = SAFE_ROUTINE_MODE
        self.validate_plans = VALIDATE_GENERATED_PLANS
        self.block_unsafe = BLOCK_UNSAFE_PLANS
        self.log_violations = LOG_SAFETY_VIOLATIONS

        # Compile regex patterns for performance
        self.medical_patterns = [re.compile(p, re.IGNORECASE) for p in self.MEDICAL_PROHIBITED]
        self.food_patterns = [re.compile(p, re.IGNORECASE) for p in self.SPECIFIC_FOOD_PROHIBITED]

        logger.info(f"[SAFETY] SafetyValidator initialized (enabled={self.enabled}, validate={self.validate_plans}, block={self.block_unsafe})")

    def validate_plan(self, plan_data: Dict[str, Any], user_id: str) -> Tuple[bool, List[SafetyViolation]]:
        """
        Validate entire routine plan for safety compliance

        Args:
            plan_data: Generated plan dictionary
            user_id: User identifier (for logging)

        Returns:
            (is_safe: bool, violations: List[SafetyViolation])
        """
        if not self.enabled or not self.validate_plans:
            return True, []  # Safety checks disabled

        violations = []

        # Check plan_items (individual tasks)
        plan_items = plan_data.get('plan_items', [])
        for idx, item in enumerate(plan_items):
            location = f"plan_items[{idx}]"

            # Check title
            title_violations = self._check_text(item.get('title', ''), f"{location}.title")
            violations.extend(title_violations)

            # Check description
            desc_violations = self._check_text(item.get('description', ''), f"{location}.description")
            violations.extend(desc_violations)

        # Check time_blocks (time block descriptions)
        time_blocks = plan_data.get('time_blocks', [])
        for idx, block in enumerate(time_blocks):
            location = f"time_blocks[{idx}]"

            # Check purpose
            purpose_violations = self._check_text(block.get('purpose', ''), f"{location}.purpose")
            violations.extend(purpose_violations)

            # Check why_it_matters
            why_violations = self._check_text(block.get('why_it_matters', ''), f"{location}.why_it_matters")
            violations.extend(why_violations)

        # Check markdown plan (if exists)
        markdown_plan = plan_data.get('markdown_plan', '')
        if markdown_plan:
            markdown_violations = self._check_text(markdown_plan, 'markdown_plan')
            violations.extend(markdown_violations)

        is_safe = len(violations) == 0

        # Log violations
        if not is_safe and self.log_violations:
            logger.warning(f"[SAFETY] [{user_id[:8]}] Plan validation found {len(violations)} violation(s)")
            for v in violations:
                logger.warning(f"[SAFETY]   - {v.category} ({v.severity}): {v.location} - {v.reason}")
                logger.warning(f"[SAFETY]     Content: {v.content[:100]}...")
        else:
            logger.info(f"[SAFETY] [{user_id[:8]}] Plan passed safety validation")

        return is_safe, violations

    def _check_text(self, text: str, location: str) -> List[SafetyViolation]:
        """Check a single text field for safety violations"""
        if not text:
            return []

        violations = []

        # Check for medical advice
        for pattern in self.medical_patterns:
            match = pattern.search(text)
            if match:
                violations.append(SafetyViolation(
                    category='medical_advice',
                    severity='high',
                    location=location,
                    content=text,
                    reason=f"Contains medical term: '{match.group()}'"
                ))

        # Check for specific food recommendations
        for pattern in self.food_patterns:
            match = pattern.search(text)
            if match:
                violations.append(SafetyViolation(
                    category='specific_meal',
                    severity='medium',
                    location=location,
                    content=text,
                    reason=f"Contains specific food item: '{match.group()}'"
                ))

        return violations

    def sanitize_plan(self, plan_data: Dict[str, Any], violations: List[SafetyViolation]) -> Dict[str, Any]:
        """
        Attempt to sanitize plan by replacing specific content with generic alternatives

        This is a fallback - ideally AI should generate safe content from the start
        """
        sanitized_plan = plan_data.copy()

        # Replacement mappings
        REPLACEMENTS = {
            # Medical
            r'take\s+\w+\s+(supplement|vitamin|medication)': 'consider general wellness practices',
            r'(\d+\s*mg|\d+\s*mcg)': 'appropriate amount',

            # Specific foods
            r'grilled salmon': 'protein-rich meal',
            r'chicken breast': 'lean protein',
            r'kale salad': 'green salad',
            r'quinoa bowl': 'grain bowl',
            r'greek yogurt': 'yogurt',
            r'\d+\s*cups?\s+of\s+\w+': 'serving of',
            r'\d+\s*oz\s+\w+': 'portion of',
        }

        # Apply replacements to plan_items
        for item in sanitized_plan.get('plan_items', []):
            for pattern, replacement in REPLACEMENTS.items():
                item['title'] = re.sub(pattern, replacement, item.get('title', ''), flags=re.IGNORECASE)
                item['description'] = re.sub(pattern, replacement, item.get('description', ''), flags=re.IGNORECASE)

        # Apply replacements to time_blocks
        for block in sanitized_plan.get('time_blocks', []):
            for pattern, replacement in REPLACEMENTS.items():
                block['purpose'] = re.sub(pattern, replacement, block.get('purpose', ''), flags=re.IGNORECASE)
                block['why_it_matters'] = re.sub(pattern, replacement, block.get('why_it_matters', ''), flags=re.IGNORECASE)

        logger.info(f"[SAFETY] Plan sanitized - replaced {len(violations)} violation(s)")

        return sanitized_plan

    def get_safe_prompt_guidelines(self) -> str:
        """
        Returns prompt text to instruct AI on safe content generation

        This should be added to the AI prompt to prevent violations at generation time
        """
        return """
🛡️ CRITICAL SAFETY GUIDELINES (MUST FOLLOW):

PROHIBITED CONTENT (DO NOT INCLUDE):
1. Medical Advice:
   ❌ Specific medications (aspirin, ibuprofen, metformin, etc.)
   ❌ Dosage instructions (500mg, 2 tablets, etc.)
   ❌ Supplements with dosages (Vitamin D 2000 IU, Omega-3 1000mg)
   ❌ Medical diagnoses or conditions
   ❌ "Consult your doctor" or medical referrals

2. Specific Meal Plans:
   ❌ Specific proteins: "grilled salmon", "chicken breast", "turkey", "poached egg"
   ❌ Specific recipes: "avocado toast", "quinoa bowl with kale", "overnight oats"
   ❌ Specific ingredients: "whole grain toast", "mashed avocado", "greek yogurt"
   ❌ Specific foods: "kale", "spinach", "blueberries", "banana"
   ❌ Quantities: "2 eggs", "3 oz chicken", "1 cup rice"
   ❌ Temperatures: "65-68°F", "room temperature", "set temperature"
   ❌ Recipe instructions: "prepare with", "cook with", "slice", "dice", "mash"
   ❌ Brand names: "Cheerios", "Quest bar", "Nature Valley"

ALLOWED CONTENT (USE THESE):
1. General Meal References (NO FOOD NAMES):
   ✅ "Have lunch", "Eat dinner", "Morning meal", "Breakfast"
   ✅ "Protein-rich meal", "Balanced meal", "Nutritious snack"
   ✅ "Meal with healthy fats and protein"
   ✅ "Meal with lean protein, whole grains, and vegetables"  (categories OK, specific foods NOT OK)
   ✅ "Hydrate", "Drink water", "Hydration break"
   ✅ "Warm beverage", "Hot drink" (NOT "green tea", "coffee")

2. General Health Practices:
   ✅ "Morning meditation (10 min)"
   ✅ "Evening walk (30 min)"
   ✅ "Stretching routine"
   ✅ "Mindful eating"
   ✅ "Adequate sleep"
   ✅ "Optimize bedroom environment"  (NOT "Set temperature to 65°F")

3. General Guidance (Categories Only):
   ✅ "Focus on protein-rich foods"  (category)
   ✅ "Include whole grains in meals"  (category)
   ✅ "Stay hydrated throughout the day"
   ✅ "Practice portion control"

EXAMPLES OF SAFE VS UNSAFE:

❌ UNSAFE: "Take Omega-3 supplement (1000mg) with breakfast"
✅ SAFE: "Morning wellness routine"

❌ UNSAFE: "Avocado Toast with Egg - Prepare with whole grain toast, mashed avocado, and poached egg"
✅ SAFE: "Nutritious breakfast with healthy fats and protein"

❌ UNSAFE: "Eat grilled salmon (6 oz) with quinoa (1 cup) and steamed broccoli"
✅ SAFE: "Protein-rich lunch with vegetables and whole grains"

❌ UNSAFE: "Set your room to 65-68°F for optimal sleep"
✅ SAFE: "Optimize bedroom environment for better sleep"

❌ UNSAFE: "Take Vitamin D supplement for mood support"
✅ SAFE: "Morning routine to support energy levels"

❌ UNSAFE: "Chicken breast salad with 3 oz grilled chicken"
✅ SAFE: "Lean protein salad"

❌ UNSAFE: "Green Tea Ritual - Enjoy a cup of antioxidant-rich green tea"
✅ SAFE: "Hydration break with warm beverage"

CRITICAL RULES - ABSOLUTE REQUIREMENTS:

1. ZERO TOLERANCE FOR SPECIFIC FOOD NAMES:
   ❌ NO: "Avocado", "Eggs", "Salmon", "Chicken", "Toast", "Quinoa", "Spinach"
   ❌ NO: "Green tea", "Coffee", "Smoothie", "Yogurt", "Oatmeal"
   ✅ YES: "Breakfast", "Lunch", "Dinner", "Snack", "Meal", "Beverage"

2. ZERO TOLERANCE FOR RECIPES OR COOKING INSTRUCTIONS:
   ❌ NO: "Prepare...", "Cook...", "Mash...", "Slice...", "Mix..."
   ❌ NO: "Avocado toast with egg", "Protein shake with berries"
   ✅ YES: "Nutritious breakfast", "Protein-rich meal"

3. ZERO TOLERANCE FOR SPECIFIC MEASUREMENTS:
   ❌ NO: "2 eggs", "3 oz", "1 cup", "2 tablespoons"
   ❌ NO: "65-68°F", "20°C"
   ✅ YES: "Appropriate portion", "Comfortable temperature"

4. USE GENERAL CATEGORIES ONLY:
   ✅ "Protein", "Whole grains", "Healthy fats", "Lean protein"
   ✅ "Balanced meal", "Nutritious snack", "Warm beverage"

REMEMBER: You are a wellness routine planner, NOT a doctor, dietitian, or nutritionist.
Your role is to suggest GENERAL healthy habits, not specific meals or medical advice.

IF IN DOUBT: Use "Breakfast/Lunch/Dinner/Snack" - NEVER use specific food names!
"""


# Singleton instance
_safety_validator_instance = None

def get_safety_validator() -> SafetyValidator:
    """Get singleton safety validator instance"""
    global _safety_validator_instance
    if _safety_validator_instance is None:
        _safety_validator_instance = SafetyValidator()
    return _safety_validator_instance
