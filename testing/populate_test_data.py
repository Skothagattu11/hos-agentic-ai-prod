#!/usr/bin/env python3
"""
Populate test health data for HolisticOS testing
Creates realistic scores and biomarkers for a test user
"""

import sys
import os
from datetime import datetime, timedelta, timezone
import random
import json
from uuid import uuid4

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TEST_USER_ID = "35pDPUIfAoRl2Y700bFkxPKYjjf2"

def create_supabase_client() -> Client:
    """Create Supabase client"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing Supabase credentials in .env file")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_scores_data(days_back: int = 30, scores_per_day: int = 5):
    """Generate realistic health scores data"""
    scores = []
    now = datetime.now(timezone.utc)
    
    score_types = ['wellbeing', 'activity', 'sleep', 'mental', 'energy']
    
    for day in range(days_back):
        date = now - timedelta(days=day)
        
        for score_type in score_types:
            # Create realistic score patterns
            base_score = random.uniform(60, 85)
            
            # Add some daily variation
            if day % 7 in [0, 6]:  # Weekends
                base_score -= random.uniform(5, 10)
            
            score = {
                'id': str(uuid4()),
                'profile_id': TEST_USER_ID,
                'type': score_type,
                'score': round(base_score + random.uniform(-10, 10), 2),
                'state': 'good' if base_score > 70 else 'moderate',
                'data': {
                    'source': 'wearable',
                    'confidence': round(random.uniform(0.7, 0.95), 2),
                    'factors': {
                        'primary': random.choice(['sleep_quality', 'activity_level', 'stress']),
                        'secondary': random.choice(['nutrition', 'hydration', 'social'])
                    }
                },
                'score_date_time': date.isoformat(),
                'created_at': date.isoformat(),
                'updated_at': date.isoformat()
            }
            scores.append(score)
    
    return scores

def generate_biomarkers_data(days_back: int = 30):
    """Generate realistic biomarkers data"""
    biomarkers = []
    now = datetime.now(timezone.utc)
    
    biomarker_configs = [
        {'category': 'activity', 'type': 'steps', 'unit': 'count', 'min': 3000, 'max': 15000},
        {'category': 'activity', 'type': 'active_minutes', 'unit': 'minutes', 'min': 10, 'max': 120},
        {'category': 'sleep', 'type': 'duration', 'unit': 'hours', 'min': 5, 'max': 9},
        {'category': 'sleep', 'type': 'efficiency', 'unit': 'percentage', 'min': 70, 'max': 95},
        {'category': 'vitals', 'type': 'heart_rate', 'unit': 'bpm', 'min': 55, 'max': 75},
        {'category': 'vitals', 'type': 'hrv', 'unit': 'ms', 'min': 30, 'max': 60},
        {'category': 'mental', 'type': 'stress_level', 'unit': 'score', 'min': 1, 'max': 5},
        {'category': 'nutrition', 'type': 'calories', 'unit': 'kcal', 'min': 1800, 'max': 2500}
    ]
    
    for day in range(days_back):
        date = now - timedelta(days=day)
        
        for config in biomarker_configs:
            # Create realistic patterns
            value = random.uniform(config['min'], config['max'])
            
            # Add weekly patterns
            if config['type'] == 'steps' and day % 7 in [0, 6]:  # Less steps on weekends
                value *= 0.7
            elif config['type'] == 'sleep' and day % 7 in [5, 6]:  # More sleep on weekends
                value *= 1.1
            
            biomarker = {
                'id': str(uuid4()),
                'profile_id': TEST_USER_ID,
                'category': config['category'],
                'type': config['type'],
                'value': str(round(value, 2)),
                'unit': config['unit'],
                'value_type': 'daily_average',
                'periodicity': 'daily',
                'aggregation': 'mean',
                'data': {
                    'source': 'wearable',
                    'device': 'apple_watch',
                    'confidence': round(random.uniform(0.8, 0.98), 2)
                },
                'start_date_time': date.isoformat(),
                'end_date_time': (date + timedelta(days=1)).isoformat(),
                'created_at': date.isoformat(),
                'updated_at': date.isoformat()
            }
            biomarkers.append(biomarker)
    
    return biomarkers

def main():
    """Main function to populate test data"""
    print("🚀 POPULATING TEST DATA FOR HOLISTICOS")
    print("=" * 60)
    print(f"User ID: {TEST_USER_ID[:8]}...")
    
    try:
        # Create Supabase client
        supabase = create_supabase_client()
        print("✅ Connected to Supabase")
        
        # Check if user exists in profiles
        profile = supabase.table('profiles').select('id').eq('id', TEST_USER_ID).execute()
        if not profile.data:
            print(f"⚠️  User {TEST_USER_ID[:8]}... not found in profiles table")
            print("Creating profile entry...")
            supabase.table('profiles').insert({
                'id': TEST_USER_ID,
                'data': {'test_user': True},
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            print("✅ Profile created")
        else:
            print("✅ User exists in profiles")
        
        # Clear existing data for clean test
        print("\n🧹 Clearing existing test data...")
        
        # Clear scores
        result = supabase.table('scores').delete().eq('profile_id', TEST_USER_ID).execute()
        print(f"   Deleted existing scores")
        
        # Clear biomarkers
        result = supabase.table('biomarkers').delete().eq('profile_id', TEST_USER_ID).execute()
        print(f"   Deleted existing biomarkers")
        
        # Generate new test data
        print("\n📊 Generating test data...")
        
        # Generate 30 days of scores (5 types per day = 150 total)
        scores = generate_scores_data(days_back=30, scores_per_day=5)
        print(f"   Generated {len(scores)} score records")
        
        # Generate 30 days of biomarkers (8 types per day = 240 total)
        biomarkers = generate_biomarkers_data(days_back=30)
        print(f"   Generated {len(biomarkers)} biomarker records")
        
        # Insert scores in batches
        print("\n💾 Inserting scores...")
        batch_size = 50
        for i in range(0, len(scores), batch_size):
            batch = scores[i:i+batch_size]
            supabase.table('scores').insert(batch).execute()
            print(f"   Inserted batch {i//batch_size + 1}/{(len(scores)-1)//batch_size + 1}")
        
        # Insert biomarkers in batches
        print("\n💾 Inserting biomarkers...")
        for i in range(0, len(biomarkers), batch_size):
            batch = biomarkers[i:i+batch_size]
            supabase.table('biomarkers').insert(batch).execute()
            print(f"   Inserted batch {i//batch_size + 1}/{(len(biomarkers)-1)//batch_size + 1}")
        
        # Verify data was inserted
        print("\n✅ Verifying data...")
        
        # Count scores
        score_count = supabase.table('scores').select('id', count='exact', head=True).eq('profile_id', TEST_USER_ID).execute()
        print(f"   Total scores: {score_count.count}")
        
        # Count biomarkers
        biomarker_count = supabase.table('biomarkers').select('id', count='exact', head=True).eq('profile_id', TEST_USER_ID).execute()
        print(f"   Total biomarkers: {biomarker_count.count}")
        
        # Show recent data samples
        print("\n📋 Recent Data Samples:")
        
        recent_scores = supabase.table('scores').select('type, score, created_at').eq('profile_id', TEST_USER_ID).order('created_at', desc=True).limit(3).execute()
        print("   Recent Scores:")
        for score in recent_scores.data:
            print(f"     • {score['type']}: {score['score']} ({score['created_at'][:10]})")
        
        recent_biomarkers = supabase.table('biomarkers').select('type, value, unit, created_at').eq('profile_id', TEST_USER_ID).order('created_at', desc=True).limit(3).execute()
        print("   Recent Biomarkers:")
        for bio in recent_biomarkers.data:
            print(f"     • {bio['type']}: {bio['value']} {bio['unit']} ({bio['created_at'][:10]})")
        
        print("\n" + "=" * 60)
        print("✅ TEST DATA POPULATION COMPLETE!")
        print(f"   Total data points: {score_count.count + biomarker_count.count}")
        print("\n🎯 Next Steps:")
        print("   1. Clear memory tables if needed")
        print("   2. Set last_analysis_at to NULL in profiles")
        print("   3. Run your test script")
        print("   4. System should now detect this as new user with data")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())