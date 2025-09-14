#!/usr/bin/env python3
"""
Startup script for Crop Yield AI Platform
Government of Odisha - Electronics & IT Department
"""

import os
import sys
from backend.app import app

if __name__ == '__main__':
    # Set environment variables for development
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('data/uploads', exist_ok=True)
    
    print("=" * 60)
    print("🌾 CROP YIELD AI PLATFORM")
    print("   Government of Odisha | Electronics & IT Department")
    print("=" * 60)
    print("🚀 Starting the application...")
    print("📍 Access the platform at: http://localhost:5000")
    print("📱 Mobile friendly interface available")
    print("🌍 Languages supported: English, Hindi, Odia")
    print("=" * 60)
    print()
    print("🔧 FEATURES AVAILABLE:")
    print("   ✅ AI-powered yield prediction")
    print("   ✅ User registration & field management")
    print("   ✅ Universal access (no login required)")
    print("   ✅ Cost-benefit calculator")
    print("   ✅ Weather & market updates")
    print("   ✅ Regional language support")
    print("   ✅ Help & support system")
    print()
    print("🔮 COMING SOON:")
    print("   🔄 Pest detection by photo")
    print("   🔄 Multiple yield scenarios")
    print("   🔄 Market price predictions")
    print("   🔄 Advanced weather alerts")
    print()
    print("=" * 60)
    print("💡 Tips for testing:")
    print("   • Register a new account for full features")
    print("   • Try universal access for quick predictions")
    print("   • Test with different crop types and conditions")
    print("   • Explore cost calculator with realistic values")
    print("=" * 60)
    print()
    
    try:
        # Run the Flask application
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("👋 Application stopped by user")
        print("   Thank you for using Crop Yield AI Platform!")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        print("   Please check the error and try again.")
        sys.exit(1)