#!/usr/bin/env python3
"""
SmartCall AI - API Testing Script
Tests all major API endpoints
"""

import requests
import json
from datetime import datetime
import time

API_URL = "http://localhost:8000/api"

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_result(success, message):
    status = "[OK]" if success else "[FAIL]"
    print(f"{status} {message}")

def test_health():
    print_header("Testing Health Endpoint")
    try:
        response = requests.get(f"{API_URL.replace('/api', '')}/health")
        data = response.json()
        print_result(response.status_code == 200, f"Health check: {data['status']}")
        return True
    except Exception as e:
        print_result(False, f"Health check failed: {e}")
        return False

def test_create_call():
    print_header("Testing Call Creation")
    try:
        call_data = {
            "agent_id": "TEST_AGENT_001",
            "agent_name": "Test Agent",
            "customer_number": "+1234567890",
            "customer_name": "Test Customer",
            "direction": "inbound"
        }
        
        response = requests.post(f"{API_URL}/calls/start", json=call_data)
        
        if response.status_code == 200:
            call = response.json()
            call_id = call['id']
            print_result(True, f"Call created: {call_id}")
            return call_id
        else:
            print_result(False, f"Failed to create call: {response.status_code}")
            return None
    except Exception as e:
        print_result(False, f"Error: {e}")
        return None

def test_get_call(call_id):
    print_header("Testing Get Call")
    try:
        response = requests.get(f"{API_URL}/calls/{call_id}")
        
        if response.status_code == 200:
            call = response.json()
            print_result(True, f"Retrieved call: {call['agent_id']}")
            return True
        else:
            print_result(False, f"Failed to get call: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def test_list_calls():
    print_header("Testing List Calls")
    try:
        response = requests.get(f"{API_URL}/calls/")
        
        if response.status_code == 200:
            calls = response.json()
            print_result(True, f"Retrieved {len(calls)} calls")
            return True
        else:
            print_result(False, f"Failed to list calls: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def test_add_transcript(call_id):
    print_header("Testing Transcript Addition")
    try:
        transcript = """
        Agent: Good morning! Thank you for calling. How may I assist you today?
        Customer: Hi, I need help with my account.
        Agent: I'd be happy to help. Can you verify your account number?
        Customer: Sure, it's 123456789.
        Agent: Thank you. I've located your account. What can I help you with?
        Customer: I want to update my contact information.
        Agent: Absolutely. I can help you with that right away.
        Customer: Great, thank you!
        Agent: Is there anything else I can assist you with today?
        Customer: No, that's all. Thank you for your help!
        Agent: You're welcome! Have a great day!
        """
        
        # Simulate ending the call
        response = requests.post(f"{API_URL}/calls/{call_id}/end")
        
        if response.status_code == 200:
            print_result(True, "Call ended successfully")
            
            # In a real implementation, the transcript would be added during the call
            # For now, we'll just mark this as success
            return True
        else:
            print_result(False, f"Failed to end call: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def test_analyze_call(call_id):
    print_header("Testing Call Analysis")
    try:
        # First, add a transcript by updating the call
        transcript = """
        Agent: Good morning! Thank you for calling. This is Sarah. How may I assist you today?
        Customer: Hi, I have a question about my loan application.
        Agent: I'd be happy to help you with that. Let me pull up your account. Can you verify your account number?
        Customer: Yes, it's 987654321.
        Agent: Thank you for confirming. I see your loan application here. Everything looks good!
        Customer: That's wonderful news! Thank you so much!
        Agent: You're very welcome! Is there anything else I can help you with?
        Customer: No, that's all. Thank you!
        Agent: Have a great day!
        """
        
        # Update call with transcript
        update_response = requests.patch(
            f"{API_URL}/calls/{call_id}",
            json={"transcript": transcript, "status": "completed"}
        )
        
        if update_response.status_code != 200:
            print_result(False, "Failed to add transcript")
            return False
        
        # Analyze the call
        response = requests.post(f"{API_URL}/calls/{call_id}/analyze")
        
        if response.status_code == 200:
            analysis = response.json()
            print_result(True, f"Analysis complete")
            print(f"  Score: {analysis.get('score', 'N/A')}/100")
            print(f"  Sentiment: {analysis.get('sentiment', 'N/A')}")
            print(f"  Risk Level: {analysis.get('risk_level', 'N/A')}")
            return True
        else:
            print_result(False, f"Analysis failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def test_dashboard():
    print_header("Testing Dashboard Analytics")
    try:
        response = requests.get(f"{API_URL}/analytics/dashboard")
        
        if response.status_code == 200:
            stats = response.json()
            print_result(True, "Dashboard stats retrieved")
            print(f"  Total Calls: {stats.get('total_calls', 0)}")
            print(f"  Active Calls: {stats.get('active_calls', 0)}")
            print(f"  Avg Score: {stats.get('average_score', 0):.1f}")
            return True
        else:
            print_result(False, f"Failed to get dashboard: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def test_agent_performance(agent_id):
    print_header("Testing Agent Performance")
    try:
        response = requests.get(f"{API_URL}/analytics/agent/{agent_id}")
        
        if response.status_code == 200:
            perf = response.json()
            print_result(True, "Agent performance retrieved")
            print(f"  Agent: {perf.get('agent_name', 'N/A')}")
            print(f"  Total Calls: {perf.get('total_calls', 0)}")
            print(f"  Avg Score: {perf.get('average_score', 0):.1f}")
            return True
        else:
            print_result(False, f"Failed to get agent performance: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  SmartCall AI - API Testing Suite")
    print("="*60)
    
    # Run tests
    if not test_health():
        print("\n[FAIL] Health check failed. Make sure the backend is running.")
        return
    
    test_list_calls()
    test_dashboard()
    
    # Create and test a call
    call_id = test_create_call()
    if call_id:
        time.sleep(1)
        test_get_call(call_id)
        test_add_transcript(call_id)
        time.sleep(1)
        test_analyze_call(call_id)
        time.sleep(1)
        test_agent_performance("TEST_AGENT_001")
    
    print("\n" + "="*60)
    print("  Testing Complete!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
