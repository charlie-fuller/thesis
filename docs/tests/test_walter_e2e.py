#!/usr/bin/env python3
"""
Thesis End-to-End Testing Script

Tests the complete Thesis L&D Assistant workflow:
1. Backend health check
2. User authentication
3. Document upload
4. RAG-powered chat
5. Image generation with Nano Banana
6. System instructions (Thesis persona) verification

Usage:
    python3 test_thesis_e2e.py

Requirements:
    - Backend running on http://localhost:8000
    - Frontend running on http://localhost:3000
    - Test documents in ./test-documents/
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from typing import Dict, Optional

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TEST_EMAIL = os.getenv("TEST_EMAIL", "test@example.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "TestPassword123!")
TEST_DOCUMENT_PATH = "./test-documents/customer_service_excellence_program.md"

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message: str):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")

def print_warning(message: str):
    """Print a warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

class ThesisTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }

    def test_backend_health(self) -> bool:
        """Test 1: Backend Health Check"""
        print_header("TEST 1: Backend Health Check")

        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)

            if response.status_code == 200:
                data = response.json()
                print_success(f"Backend is healthy: {json.dumps(data, indent=2)}")

                if data.get("database") == "connected":
                    print_success("Database connection verified")
                else:
                    print_warning("Database connection status unclear")
                    self.test_results["warnings"] += 1

                self.test_results["passed"] += 1
                return True
            else:
                print_error(f"Health check failed with status {response.status_code}")
                self.test_results["failed"] += 1
                return False

        except requests.exceptions.RequestException as e:
            print_error(f"Failed to connect to backend: {e}")
            print_info(f"Make sure backend is running on {self.backend_url}")
            self.test_results["failed"] += 1
            return False

    def test_user_authentication(self) -> bool:
        """Test 2: User Authentication"""
        print_header("TEST 2: User Authentication")

        # First, try to create test user (may fail if already exists - that's OK)
        print_info("Attempting to create test user...")

        signup_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": "Thesis Test User"
        }

        try:
            response = requests.post(
                f"{self.backend_url}/api/auth/signup",
                json=signup_data,
                timeout=10
            )

            if response.status_code == 200:
                print_success("Test user created successfully")
            elif response.status_code == 400:
                print_info("Test user already exists (this is OK)")
            else:
                print_warning(f"Signup returned status {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            print_warning(f"Signup request failed: {e}")

        # Now try to login
        print_info("Attempting to login...")

        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }

        try:
            response = requests.post(
                f"{self.backend_url}/api/auth/login",
                json=login_data,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")

                print_success("Login successful")
                print_info(f"User ID: {self.user_id}")
                print_info(f"Access Token: {self.access_token[:20]}...")

                self.test_results["passed"] += 1
                return True
            else:
                print_error(f"Login failed with status {response.status_code}: {response.text}")
                self.test_results["failed"] += 1
                return False

        except requests.exceptions.RequestException as e:
            print_error(f"Login request failed: {e}")
            self.test_results["failed"] += 1
            return False

    def test_document_upload(self) -> Optional[str]:
        """Test 3: Document Upload & RAG Processing"""
        print_header("TEST 3: Document Upload & RAG Processing")

        if not self.access_token:
            print_error("Skipping: Not authenticated")
            self.test_results["failed"] += 1
            return None

        # Check if test document exists
        if not os.path.exists(TEST_DOCUMENT_PATH):
            print_error(f"Test document not found: {TEST_DOCUMENT_PATH}")
            print_info("Run this script from the thesis/ root directory")
            self.test_results["failed"] += 1
            return None

        print_info(f"Uploading: {TEST_DOCUMENT_PATH}")

        try:
            with open(TEST_DOCUMENT_PATH, 'rb') as f:
                files = {'file': (os.path.basename(TEST_DOCUMENT_PATH), f, 'text/markdown')}
                headers = {'Authorization': f'Bearer {self.access_token}'}

                response = requests.post(
                    f"{self.backend_url}/api/documents/upload",
                    files=files,
                    headers=headers,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    document_id = data.get("document", {}).get("id")

                    print_success("Document uploaded successfully")
                    print_info(f"Document ID: {document_id}")

                    # Wait for processing
                    print_info("Waiting for document processing (max 30 seconds)...")

                    for i in range(6):  # Check 6 times (30 seconds total)
                        time.sleep(5)

                        status_response = requests.get(
                            f"{self.backend_url}/api/documents/{document_id}",
                            headers=headers,
                            timeout=10
                        )

                        if status_response.status_code == 200:
                            doc_data = status_response.json()
                            status = doc_data.get("processing_status")
                            chunk_count = doc_data.get("chunk_count", 0)

                            print_info(f"Status: {status}, Chunks: {chunk_count}")

                            if status == "completed" and chunk_count > 0:
                                print_success(f"Document processed: {chunk_count} chunks created")
                                self.test_results["passed"] += 1
                                return document_id
                            elif status == "error":
                                print_error(f"Processing error: {doc_data.get('processing_error')}")
                                self.test_results["failed"] += 1
                                return None

                    print_warning("Document processing timeout (check manually)")
                    self.test_results["warnings"] += 1
                    return document_id

                else:
                    print_error(f"Upload failed with status {response.status_code}: {response.text}")
                    self.test_results["failed"] += 1
                    return None

        except requests.exceptions.RequestException as e:
            print_error(f"Upload request failed: {e}")
            self.test_results["failed"] += 1
            return None

    def test_rag_chat(self, document_id: Optional[str]) -> bool:
        """Test 4: RAG-Powered Chat"""
        print_header("TEST 4: RAG-Powered Chat")

        if not self.access_token:
            print_error("Skipping: Not authenticated")
            self.test_results["failed"] += 1
            return False

        # Test query that should use the uploaded document
        test_query = "What are the success metrics for the customer service program?"

        print_info(f"Query: {test_query}")

        try:
            chat_data = {
                "message": test_query,
                "use_rag": True,  # Enable RAG
                "conversation_id": None  # New conversation
            }

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.backend_url}/api/chat",
                json=chat_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "")
                sources = data.get("sources", [])

                print_success("Chat response received")
                print_info(f"Response length: {len(reply)} characters")
                print_info(f"Sources used: {len(sources)}")

                # Check if response contains expected metrics from the document
                expected_keywords = ["CSAT", "4.5", "85%", "escalation", "ROI"]
                found_keywords = [kw for kw in expected_keywords if kw.lower() in reply.lower()]

                if len(found_keywords) >= 2:
                    print_success(f"Response contains expected metrics: {', '.join(found_keywords)}")
                    print_info("Preview: " + reply[:200] + "...")
                    self.test_results["passed"] += 1
                    return True
                else:
                    print_warning("Response doesn't contain expected document-specific metrics")
                    print_warning("RAG may not be working correctly")
                    print_info("Preview: " + reply[:200] + "...")
                    self.test_results["warnings"] += 1
                    return False

            else:
                print_error(f"Chat failed with status {response.status_code}: {response.text}")
                self.test_results["failed"] += 1
                return False

        except requests.exceptions.RequestException as e:
            print_error(f"Chat request failed: {e}")
            self.test_results["failed"] += 1
            return False

    def test_thesis_persona(self) -> bool:
        """Test 5: Thesis L&D Persona Verification"""
        print_header("TEST 5: Thesis L&D Persona Verification")

        if not self.access_token:
            print_error("Skipping: Not authenticated")
            self.test_results["failed"] += 1
            return False

        # Query that should trigger Thesis's ROI-first approach
        test_query = "I need to create a training program for our team. Where should I start?"

        print_info(f"Query: {test_query}")

        try:
            chat_data = {
                "message": test_query,
                "use_rag": False,  # Test system instructions only
                "conversation_id": None
            }

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.backend_url}/api/chat",
                json=chat_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "")

                print_success("Chat response received")

                # Check for Thesis persona indicators
                thesis_indicators = {
                    "ROI-first": ["ROI", "business problem", "KPI", "performance gap"],
                    "DDLD Framework": ["DDLD", "data", "desired state", "learning gap", "difference"],
                    "Behavior focus": ["behavior", "on the job", "performance"],
                    "Warm tone": ["let's", "we", "together", "help", "guide"]
                }

                found_indicators = {}
                for category, keywords in thesis_indicators.items():
                    matches = [kw for kw in keywords if kw.lower() in reply.lower()]
                    if matches:
                        found_indicators[category] = matches

                if len(found_indicators) >= 2:
                    print_success("Thesis persona verified!")
                    for category, matches in found_indicators.items():
                        print_info(f"  {category}: {', '.join(matches)}")
                    print_info("Preview: " + reply[:300] + "...")
                    self.test_results["passed"] += 1
                    return True
                else:
                    print_warning("Thesis persona not strongly detected")
                    print_warning("Found indicators: " + str(found_indicators))
                    print_info("Preview: " + reply[:300] + "...")
                    self.test_results["warnings"] += 1
                    return False

            else:
                print_error(f"Chat failed with status {response.status_code}: {response.text}")
                self.test_results["failed"] += 1
                return False

        except requests.exceptions.RequestException as e:
            print_error(f"Chat request failed: {e}")
            self.test_results["failed"] += 1
            return False

    def test_image_generation(self) -> bool:
        """Test 6: Image Generation with Nano Banana"""
        print_header("TEST 6: Image Generation with Nano Banana")

        if not self.access_token:
            print_error("Skipping: Not authenticated")
            self.test_results["failed"] += 1
            return False

        test_prompt = "A friendly learning professional coaching a team, professional illustration"

        print_info(f"Prompt: {test_prompt}")

        try:
            image_data = {
                "prompt": test_prompt
            }

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.backend_url}/api/images/generate",
                json=image_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                image_url = data.get("image_url", "")
                model = data.get("model", "")

                print_success("Image generated successfully")
                print_info(f"Model: {model}")
                print_info(f"Image data length: {len(image_url)} characters")

                if image_url.startswith("data:image"):
                    print_success("Image is base64 encoded (expected format)")
                    self.test_results["passed"] += 1
                    return True
                else:
                    print_warning("Unexpected image format")
                    self.test_results["warnings"] += 1
                    return False

            else:
                print_error(f"Image generation failed with status {response.status_code}: {response.text}")
                self.test_results["failed"] += 1
                return False

        except requests.exceptions.RequestException as e:
            print_error(f"Image generation request failed: {e}")
            self.test_results["failed"] += 1
            return False

    def print_summary(self):
        """Print test results summary"""
        print_header("TEST SUMMARY")

        total_tests = self.test_results["passed"] + self.test_results["failed"] + self.test_results["warnings"]

        print(f"Total Tests: {total_tests}")
        print_success(f"Passed: {self.test_results['passed']}")
        print_warning(f"Warnings: {self.test_results['warnings']}")
        print_error(f"Failed: {self.test_results['failed']}")

        if self.test_results["failed"] == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ ALL CRITICAL TESTS PASSED!{Colors.ENDC}")
            if self.test_results["warnings"] > 0:
                print(f"{Colors.WARNING}⚠ Review warnings above{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.ENDC}")
            print(f"{Colors.FAIL}Review errors above and fix before deployment{Colors.ENDC}")

def main():
    """Run all tests"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║         THESIS L&D ASSISTANT - END-TO-END TEST SUITE           ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

    print_info(f"Backend URL: {BACKEND_URL}")
    print_info(f"Test User: {TEST_EMAIL}")
    print_info(f"Timestamp: {datetime.now().isoformat()}")

    tester = ThesisTester()

    # Run tests in sequence
    if not tester.test_backend_health():
        print_error("Backend health check failed - stopping tests")
        tester.print_summary()
        sys.exit(1)

    if not tester.test_user_authentication():
        print_error("Authentication failed - stopping tests")
        tester.print_summary()
        sys.exit(1)

    document_id = tester.test_document_upload()
    tester.test_rag_chat(document_id)
    tester.test_thesis_persona()
    tester.test_image_generation()

    # Print summary
    tester.print_summary()

    # Exit with appropriate code
    sys.exit(0 if tester.test_results["failed"] == 0 else 1)

if __name__ == "__main__":
    main()
