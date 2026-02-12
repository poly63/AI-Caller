#!/bin/bash

# SmartCall AI Setup Script
# This script helps set up and test the SmartCall AI system

set -e

echo "╔════════════════════════════════════════════╗"
echo "║      SmartCall AI - Setup Script          ║"
echo "╔════════════════════════════════════════════╗"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker installed: $(docker --version)"
    else
        print_error "Docker not found. Please install Docker."
        exit 1
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose installed: $(docker-compose --version)"
    else
        print_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        print_success "Python installed: $(python3 --version)"
    else
        print_warning "Python not found. Required for local development."
    fi
    
    # Check Node.js
    if command -v node &> /dev/null; then
        print_success "Node.js installed: $(node --version)"
    else
        print_warning "Node.js not found. Required for frontend development."
    fi
}

# Create environment file
create_env_file() {
    print_status "Creating environment file..."
    
    if [ ! -f "backend/.env" ]; then
        cat > backend/.env << EOF
DATABASE_URL=postgresql://smartcall:smartcall123@localhost:5432/smartcall_ai
SECRET_KEY=$(openssl rand -hex 32)
OPENAI_API_KEY=your-openai-key-here-optional
EOF
        print_success "Created backend/.env file"
    else
        print_warning "backend/.env already exists"
    fi
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Start only PostgreSQL
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    sleep 5
    
    # Initialize database
    cd backend
    python3 -m app.database
    cd ..
    
    print_success "Database initialized"
}

# Build and start services
start_services() {
    print_status "Building and starting services..."
    
    docker-compose up --build -d
    
    print_success "Services started successfully"
    print_status "Backend API: http://localhost:8000"
    print_status "API Docs: http://localhost:8000/docs"
    print_status "Frontend: http://localhost:3000"
}

# Create test data
create_test_data() {
    print_status "Creating test data..."
    
    # Wait for backend to be ready
    sleep 10
    
    # Create test calls using Python
    python3 << 'PYTHON'
import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000/api"

# Test call data
test_calls = [
    {
        "agent_id": "AGENT001",
        "agent_name": "John Smith",
        "customer_number": "+1234567890",
        "customer_name": "Alice Johnson",
        "direction": "inbound"
    },
    {
        "agent_id": "AGENT002",
        "agent_name": "Sarah Williams",
        "customer_number": "+9876543210",
        "customer_name": "Bob Davis",
        "direction": "inbound"
    },
    {
        "agent_id": "AGENT001",
        "agent_name": "John Smith",
        "customer_number": "+5555555555",
        "customer_name": "Charlie Brown",
        "direction": "outbound"
    }
]

# Sample transcripts
sample_transcripts = [
    "Agent: Good morning! Thank you for calling. This is John. How may I assist you today? Customer: Hi, I have a question about my recent loan application. Agent: I'd be happy to help you with that. Let me pull up your account. Can you please verify your account number? Customer: Yes, it's 12345678. Agent: Thank you for confirming. I see your loan application here. Everything looks good, and it's been approved! Customer: That's great news! Thank you so much! Agent: You're welcome! You should receive the documentation within 3 business days. Is there anything else I can help you with? Customer: No, that's all. Thank you! Agent: Have a great day!",
    
    "Agent: Hello, this is Sarah from customer service. How can I help you? Customer: I'm calling because there's been an error on my bill. Agent: I apologize for the inconvenience. Let me look into that for you. Can you tell me more about the error? Customer: I was charged twice for the same transaction. Agent: I understand your frustration. Let me verify this right away. I can see the duplicate charge. I'll process a refund immediately. Customer: Thank you for resolving this quickly. Agent: You're welcome! The refund will appear in 3-5 business days. Is there anything else? Customer: No, that's all. Agent: Have a wonderful day!",
    
    "Agent: Good afternoon. This is John calling from the sales team. Is this Charlie? Customer: Yes, speaking. Agent: I wanted to follow up on the product demo we discussed last week. Customer: Oh yes, I've been meaning to get back to you about that. Agent: Great! Do you have any questions about the product? Customer: Actually, I think we're ready to move forward with a purchase. Agent: Excellent! Let me walk you through the next steps. Customer: Sounds good. Agent: Perfect, I'll send you the contract details today. Customer: Thank you!"
]

print("Creating test calls...")
for i, call_data in enumerate(test_calls):
    try:
        # Create call
        response = requests.post(f"{API_URL}/calls/start", json=call_data)
        if response.status_code == 200:
            call = response.json()
            call_id = call['id']
            print(f"✓ Created call {i+1}: {call_id}")
            
            # Add transcript
            requests.patch(
                f"{API_URL}/calls/{call_id}",
                json={"transcript": sample_transcripts[i], "status": "completed"}
            )
            
            # Trigger analysis
            requests.post(f"{API_URL}/calls/{call_id}/analyze")
            print(f"✓ Analyzed call {i+1}")
        else:
            print(f"✗ Failed to create call {i+1}: {response.status_code}")
    except Exception as e:
        print(f"✗ Error creating call {i+1}: {e}")

print("\n✓ Test data created successfully!")
PYTHON
    
    print_success "Test data created"
}

# Display status
display_status() {
    echo ""
    echo "╔════════════════════════════════════════════╗"
    echo "║         SmartCall AI - Status              ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""
    
    docker-compose ps
    
    echo ""
    print_success "SmartCall AI is running!"
    echo ""
    echo "Access points:"
    echo "  • Backend API:    http://localhost:8000"
    echo "  • API Docs:       http://localhost:8000/docs"
    echo "  • Frontend:       http://localhost:3000"
    echo "  • Database:       localhost:5432"
    echo ""
    echo "Useful commands:"
    echo "  • View logs:      docker-compose logs -f"
    echo "  • Stop services:  docker-compose down"
    echo "  • Restart:        docker-compose restart"
    echo ""
}

# Main menu
main_menu() {
    echo "What would you like to do?"
    echo "1) Full setup (recommended for first time)"
    echo "2) Start services only"
    echo "3) Stop services"
    echo "4) Create test data"
    echo "5) View logs"
    echo "6) Clean everything (delete data)"
    echo "7) Exit"
    echo ""
    read -p "Enter choice [1-7]: " choice
    
    case $choice in
        1)
            check_prerequisites
            create_env_file
            start_services
            create_test_data
            display_status
            ;;
        2)
            start_services
            display_status
            ;;
        3)
            print_status "Stopping services..."
            docker-compose down
            print_success "Services stopped"
            ;;
        4)
            create_test_data
            ;;
        5)
            docker-compose logs -f
            ;;
        6)
            print_warning "This will delete all data!"
            read -p "Are you sure? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                docker-compose down -v
                rm -f backend/.env
                print_success "Everything cleaned"
            fi
            ;;
        7)
            print_status "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            main_menu
            ;;
    esac
}

# Run main menu
main_menu
