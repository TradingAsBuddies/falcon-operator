# Falcon Trading Platform - Makefile
# FHS-compliant installation system with service account

.PHONY: all install uninstall clean setup-user setup-dirs setup-venv setup-db setup-nginx \
        setup-ssl setup-services setup-config start stop restart status help validate

# FHS-compliant installation directories
PREFIX ?= /opt/falcon
CONFIG_DIR = /etc/falcon
DATA_DIR = /var/lib/falcon
CACHE_DIR = /var/cache/falcon
LOG_DIR = /var/log/falcon
SYSTEMD_DIR = /etc/systemd/system
NGINX_AVAILABLE = /etc/nginx/sites-available
NGINX_ENABLED = /etc/nginx/sites-enabled
SSL_DIR = /etc/nginx/ssl

# Service account
SERVICE_USER ?= falcon
SERVICE_GROUP ?= falcon

# Current directory (source)
SRC_DIR = $(shell pwd)

# Python virtual environment
VENV_DIR = $(PREFIX)/venv

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

# Default target
all: check-deps
	@echo "$(GREEN)✓ Falcon Trading Platform build complete$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run: sudo make install"
	@echo "  2. Configure API keys in $(CONFIG_DIR)/secrets.env"
	@echo "  3. Start services: sudo make start"
	@echo ""

# Check if running as root
check-root:
	@if [ "$$(id -u)" -ne 0 ]; then \
		echo "$(RED)✗ Error: This target must be run as root$(NC)"; \
		echo "  Please run: sudo make <target>"; \
		exit 1; \
	fi

# Check dependencies
check-deps:
	@echo "$(BLUE)Checking system dependencies...$(NC)"
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)✗ python3 not found$(NC)"; exit 1; }
	@command -v pip3 >/dev/null 2>&1 || { echo "$(RED)✗ pip3 not found$(NC)"; exit 1; }
	@command -v nginx >/dev/null 2>&1 || { echo "$(YELLOW)⚠ nginx not found (will install)$(NC)"; }
	@if [ -z "$$DOCKER_BUILD" ]; then \
		command -v systemctl >/dev/null 2>&1 || { echo "$(RED)✗ systemd not found$(NC)"; exit 1; }; \
	else \
		echo "$(YELLOW)⚠ Skipping systemctl check (Docker build)$(NC)"; \
	fi
	@echo "$(GREEN)✓ System dependencies OK$(NC)"

# Main installation target
install: check-root check-deps
	@echo "$(BLUE)=========================================="
	@echo "Installing Falcon Trading Platform"
	@echo "FHS-compliant with service account"
	@echo "==========================================$(NC)"
	@$(MAKE) install-nginx
	@$(MAKE) setup-user
	@$(MAKE) setup-dirs
	@$(MAKE) setup-venv
	@$(MAKE) setup-config
	@$(MAKE) setup-db
	@$(MAKE) setup-ssl
	@$(MAKE) setup-nginx
	@if [ -z "$$DOCKER_BUILD" ]; then \
		$(MAKE) setup-services; \
	else \
		echo "$(YELLOW)⚠ Skipping systemd service setup (Docker build)$(NC)"; \
	fi
	@echo ""
	@echo "$(GREEN)=========================================="
	@echo "✓ Installation Complete!"
	@echo "==========================================$(NC)"
	@echo ""
	@echo "Installation Summary:"
	@echo "  • Application: $(PREFIX)"
	@echo "  • Configuration: $(CONFIG_DIR)"
	@echo "  • Data: $(DATA_DIR)"
	@echo "  • Logs: $(LOG_DIR)"
	@echo "  • Service User: $(SERVICE_USER):$(SERVICE_GROUP)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Configure API keys: sudo nano $(CONFIG_DIR)/secrets.env"
	@echo "  2. (Optional) Configure PostgreSQL: sudo nano $(CONFIG_DIR)/config.conf"
	@echo "  3. Start services: sudo make start"
	@echo "  4. Check status: sudo make status"
	@echo "  5. Access at: https://localhost/ or https://your-ip/"
	@echo ""

# Install nginx if not present
install-nginx:
	@echo "$(BLUE)Checking nginx installation...$(NC)"
	@if ! command -v nginx >/dev/null 2>&1; then \
		echo "$(YELLOW)Installing nginx...$(NC)"; \
		apt-get update -qq && apt-get install -y -qq nginx || { \
			echo "$(RED)✗ Failed to install nginx$(NC)"; \
			exit 1; \
		}; \
		echo "$(GREEN)✓ nginx installed$(NC)"; \
	else \
		echo "$(GREEN)✓ nginx already installed$(NC)"; \
	fi

# Create service user and group
setup-user:
	@echo "$(BLUE)Setting up service account...$(NC)"
	@if ! id -u $(SERVICE_USER) >/dev/null 2>&1; then \
		useradd -r -s /bin/false -d $(DATA_DIR) -M $(SERVICE_USER) || { \
			echo "$(RED)✗ Failed to create user$(NC)"; \
			exit 1; \
		}; \
		echo "$(GREEN)✓ Created service user: $(SERVICE_USER)$(NC)"; \
	else \
		echo "$(GREEN)✓ Service user already exists: $(SERVICE_USER)$(NC)"; \
	fi

# Create FHS-compliant directory structure
setup-dirs:
	@echo "$(BLUE)Creating directory structure...$(NC)"
	@mkdir -p $(PREFIX)
	@mkdir -p $(CONFIG_DIR)
	@mkdir -p $(DATA_DIR)
	@mkdir -p $(DATA_DIR)/market_data
	@mkdir -p $(CACHE_DIR)
	@mkdir -p $(LOG_DIR)
	@echo "$(GREEN)✓ Directories created$(NC)"
	@echo "$(BLUE)Copying application files...$(NC)"
	@rsync -a --exclude='backtest/' --exclude='venv/' --exclude='__pycache__/' \
		--exclude='*.pyc' --exclude='*.db' --exclude='.git/' \
		$(SRC_DIR)/ $(PREFIX)/ || { \
		echo "$(RED)✗ Failed to copy files (try: apt-get install rsync)$(NC)"; \
		exit 1; \
	}
	@echo "$(GREEN)✓ Application files copied to $(PREFIX)$(NC)"
	@echo "$(BLUE)Setting permissions...$(NC)"
	@chown -R $(SERVICE_USER):$(SERVICE_GROUP) $(PREFIX)
	@chown root:$(SERVICE_GROUP) $(CONFIG_DIR)
	@chown -R $(SERVICE_USER):$(SERVICE_GROUP) $(DATA_DIR)
	@chown -R $(SERVICE_USER):$(SERVICE_GROUP) $(CACHE_DIR)
	@chown -R $(SERVICE_USER):$(SERVICE_GROUP) $(LOG_DIR)
	@chmod 755 $(PREFIX)
	@chmod 750 $(CONFIG_DIR)
	@chmod 750 $(DATA_DIR)
	@chmod 750 $(LOG_DIR)
	@echo "$(GREEN)✓ Permissions set$(NC)"

# Setup Python virtual environment
setup-venv:
	@echo "$(BLUE)Setting up Python virtual environment...$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		python3 -m venv $(VENV_DIR) || { \
			echo "$(RED)✗ Failed to create virtual environment$(NC)"; \
			exit 1; \
		}; \
	fi
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	@$(VENV_DIR)/bin/pip3 install --upgrade pip setuptools wheel -q || { \
		echo "$(RED)✗ Failed to upgrade pip$(NC)"; \
		exit 1; \
	}
	@$(VENV_DIR)/bin/pip3 install -r $(PREFIX)/requirements.txt -q || { \
		echo "$(RED)✗ Failed to install requirements$(NC)"; \
		exit 1; \
	}
	@chown -R $(SERVICE_USER):$(SERVICE_GROUP) $(VENV_DIR)
	@echo "$(GREEN)✓ Virtual environment ready$(NC)"

# Setup configuration files
setup-config:
	@echo "$(BLUE)Setting up configuration...$(NC)"
	@if [ ! -f "$(CONFIG_DIR)/config.conf" ]; then \
		echo "# Falcon Trading Platform - Configuration" > $(CONFIG_DIR)/config.conf; \
		echo "# General settings" >> $(CONFIG_DIR)/config.conf; \
		echo "FALCON_ENV=production" >> $(CONFIG_DIR)/config.conf; \
		echo "" >> $(CONFIG_DIR)/config.conf; \
		echo "# Database (default: SQLite)" >> $(CONFIG_DIR)/config.conf; \
		echo "DB_TYPE=sqlite" >> $(CONFIG_DIR)/config.conf; \
		echo "DB_PATH=$(DATA_DIR)/paper_trading.db" >> $(CONFIG_DIR)/config.conf; \
		echo "" >> $(CONFIG_DIR)/config.conf; \
		echo "# PostgreSQL (uncomment to use)" >> $(CONFIG_DIR)/config.conf; \
		echo "#DB_TYPE=postgresql" >> $(CONFIG_DIR)/config.conf; \
		echo "#DB_HOST=localhost" >> $(CONFIG_DIR)/config.conf; \
		echo "#DB_PORT=5432" >> $(CONFIG_DIR)/config.conf; \
		echo "#DB_NAME=falcon" >> $(CONFIG_DIR)/config.conf; \
		echo "#DB_USER=falcon" >> $(CONFIG_DIR)/config.conf; \
		echo "" >> $(CONFIG_DIR)/config.conf; \
		echo "# Flask server" >> $(CONFIG_DIR)/config.conf; \
		echo "FLASK_HOST=127.0.0.1" >> $(CONFIG_DIR)/config.conf; \
		echo "FLASK_PORT=5000" >> $(CONFIG_DIR)/config.conf; \
		echo "FLASK_DEBUG=false" >> $(CONFIG_DIR)/config.conf; \
		chmod 644 $(CONFIG_DIR)/config.conf; \
		echo "$(GREEN)✓ Created config.conf$(NC)"; \
	else \
		echo "$(GREEN)✓ config.conf exists$(NC)"; \
	fi
	@if [ ! -f "$(CONFIG_DIR)/secrets.env" ]; then \
		echo "# Falcon Trading Platform - Secrets" > $(CONFIG_DIR)/secrets.env; \
		echo "# IMPORTANT: Add your API keys here" >> $(CONFIG_DIR)/secrets.env; \
		echo "" >> $(CONFIG_DIR)/secrets.env; \
		echo "# Required for paper trading" >> $(CONFIG_DIR)/secrets.env; \
		echo "MASSIVE_API_KEY=your_polygon_api_key_here" >> $(CONFIG_DIR)/secrets.env; \
		echo "" >> $(CONFIG_DIR)/secrets.env; \
		echo "# Required for AI features" >> $(CONFIG_DIR)/secrets.env; \
		echo "CLAUDE_API_KEY=your_claude_api_key_here" >> $(CONFIG_DIR)/secrets.env; \
		echo "" >> $(CONFIG_DIR)/secrets.env; \
		echo "# Optional for additional AI agents" >> $(CONFIG_DIR)/secrets.env; \
		echo "OPENAI_API_KEY=your_openai_key_here" >> $(CONFIG_DIR)/secrets.env; \
		echo "PERPLEXITY_API_KEY=your_perplexity_key_here" >> $(CONFIG_DIR)/secrets.env; \
		echo "" >> $(CONFIG_DIR)/secrets.env; \
		echo "# PostgreSQL password (if using PostgreSQL)" >> $(CONFIG_DIR)/secrets.env; \
		echo "#DB_PASSWORD=your_postgres_password" >> $(CONFIG_DIR)/secrets.env; \
		echo "" >> $(CONFIG_DIR)/secrets.env; \
		echo "# Optional: Custom Finviz screener" >> $(CONFIG_DIR)/secrets.env; \
		echo "#FINVIZ_SCREENER_URL=https://finviz.com/screener.ashx?v=..." >> $(CONFIG_DIR)/secrets.env; \
		chmod 640 $(CONFIG_DIR)/secrets.env; \
		chown root:$(SERVICE_GROUP) $(CONFIG_DIR)/secrets.env; \
		echo "$(GREEN)✓ Created secrets.env$(NC)"; \
		echo "$(YELLOW)⚠ Please edit $(CONFIG_DIR)/secrets.env to add your API keys$(NC)"; \
	else \
		echo "$(GREEN)✓ secrets.env exists$(NC)"; \
	fi

# Initialize database
setup-db:
	@echo "$(BLUE)Initializing database...$(NC)"
	@if [ ! -f "$(DATA_DIR)/paper_trading.db" ]; then \
		cd $(PREFIX) && FALCON_ENV=production $(VENV_DIR)/bin/python3 db_manager.py || { \
			echo "$(RED)✗ Failed to initialize database$(NC)"; \
			exit 1; \
		}; \
		chown $(SERVICE_USER):$(SERVICE_GROUP) $(DATA_DIR)/paper_trading.db; \
		echo "$(GREEN)✓ Database initialized$(NC)"; \
	else \
		echo "$(GREEN)✓ Database already exists$(NC)"; \
	fi

# Setup SSL certificates
setup-ssl:
	@echo "$(BLUE)Setting up SSL certificates...$(NC)"
	@mkdir -p $(SSL_DIR)
	@if [ ! -f "$(SSL_DIR)/falcon.crt" ] || [ ! -f "$(SSL_DIR)/falcon.key" ]; then \
		echo "$(YELLOW)Generating self-signed SSL certificate...$(NC)"; \
		openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
			-keyout $(SSL_DIR)/falcon.key \
			-out $(SSL_DIR)/falcon.crt \
			-subj "/C=US/ST=State/L=City/O=Falcon/CN=localhost" \
			>/dev/null 2>&1 || { \
			echo "$(RED)✗ Failed to generate SSL certificate$(NC)"; \
			exit 1; \
		}; \
		chmod 600 $(SSL_DIR)/falcon.key; \
		chmod 644 $(SSL_DIR)/falcon.crt; \
		echo "$(GREEN)✓ SSL certificate generated$(NC)"; \
	else \
		echo "$(GREEN)✓ SSL certificate already exists$(NC)"; \
	fi

# Setup nginx configuration
setup-nginx:
	@echo "$(BLUE)Configuring nginx...$(NC)"
	@mkdir -p $(NGINX_AVAILABLE) $(NGINX_ENABLED)
	@bash $(SRC_DIR)/scripts/install-nginx.sh $(PREFIX) $(DATA_DIR) || { \
		echo "$(RED)✗ Failed to configure nginx$(NC)"; \
		exit 1; \
	}
	@echo "$(BLUE)Testing nginx configuration...$(NC)"
	@nginx -t >/dev/null 2>&1 || { \
		echo "$(RED)✗ nginx configuration test failed$(NC)"; \
		echo "  Run: nginx -t"; \
		exit 1; \
	}
	@echo "$(GREEN)✓ nginx configured successfully$(NC)"

# Setup systemd services
setup-services:
	@echo "$(BLUE)Setting up systemd services...$(NC)"
	@bash $(SRC_DIR)/scripts/install-service.sh $(PREFIX) $(CONFIG_DIR) $(SERVICE_USER) || { \
		echo "$(RED)✗ Failed to setup services$(NC)"; \
		exit 1; \
	}
	@if [ -z "$$DOCKER_BUILD" ]; then \
		systemctl daemon-reload; \
	else \
		echo "$(YELLOW)⚠ Skipping systemctl daemon-reload (Docker build)$(NC)"; \
	fi
	@echo "$(GREEN)✓ Services configured$(NC)"

# Start all services
start: check-root
	@echo "$(BLUE)Starting Falcon services...$(NC)"
	@systemctl enable falcon-dashboard >/dev/null 2>&1
	@systemctl start falcon-dashboard || { \
		echo "$(RED)✗ Failed to start falcon-dashboard$(NC)"; \
		journalctl -u falcon-dashboard -n 20 --no-pager; \
		exit 1; \
	}
	@systemctl restart nginx || { \
		echo "$(RED)✗ Failed to restart nginx$(NC)"; \
		exit 1; \
	}
	@echo "$(GREEN)✓ Services started$(NC)"
	@$(MAKE) status

# Stop all services
stop: check-root
	@echo "$(BLUE)Stopping Falcon services...$(NC)"
	@systemctl stop falcon-dashboard || true
	@echo "$(GREEN)✓ Services stopped$(NC)"

# Restart all services
restart: check-root
	@$(MAKE) stop
	@sleep 2
	@$(MAKE) start

# Check service status
status:
	@echo "$(BLUE)=========================================="
	@echo "Falcon Service Status"
	@echo "==========================================$(NC)"
	@echo ""
	@echo "Dashboard Service:"
	@systemctl is-active falcon-dashboard >/dev/null 2>&1 && \
		echo "  $(GREEN)✓ Running$(NC)" || \
		echo "  $(RED)✗ Stopped$(NC)"
	@echo ""
	@echo "Nginx Service:"
	@systemctl is-active nginx >/dev/null 2>&1 && \
		echo "  $(GREEN)✓ Running$(NC)" || \
		echo "  $(RED)✗ Stopped$(NC)"
	@echo ""
	@echo "Recent logs (falcon-dashboard):"
	@journalctl -u falcon-dashboard -n 5 --no-pager 2>/dev/null || true
	@echo ""

# Validate configuration
validate:
	@echo "$(BLUE)Validating configuration...$(NC)"
	@if [ -f "$(PREFIX)/config.py" ]; then \
		cd $(PREFIX) && FALCON_ENV=production $(VENV_DIR)/bin/python3 config.py --validate || { \
			echo "$(RED)✗ Configuration validation failed$(NC)"; \
			exit 1; \
		}; \
	else \
		echo "$(YELLOW)⚠ Configuration module not found$(NC)"; \
	fi

# Uninstall
uninstall: check-root
	@echo "$(BLUE)Uninstalling Falcon Trading Platform...$(NC)"
	@systemctl stop falcon-dashboard >/dev/null 2>&1 || true
	@systemctl disable falcon-dashboard >/dev/null 2>&1 || true
	@rm -f $(SYSTEMD_DIR)/falcon-dashboard.service
	@rm -f $(NGINX_ENABLED)/falcon
	@rm -f $(NGINX_AVAILABLE)/falcon
	@systemctl daemon-reload
	@systemctl restart nginx >/dev/null 2>&1 || true
	@echo "$(GREEN)✓ Services removed$(NC)"
	@echo "$(YELLOW)Note: Preserved directories:$(NC)"
	@echo "  • $(PREFIX) (application)"
	@echo "  • $(CONFIG_DIR) (configuration)"
	@echo "  • $(DATA_DIR) (database and data)"
	@echo "  • $(LOG_DIR) (logs)"
	@echo ""
	@echo "To completely remove (WARNING: deletes all data):"
	@echo "  sudo rm -rf $(PREFIX) $(CONFIG_DIR) $(DATA_DIR) $(LOG_DIR)"
	@echo "  sudo userdel $(SERVICE_USER)"

# Clean build artifacts
clean:
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Clean complete$(NC)"

# Help target
help:
	@echo "$(BLUE)Falcon Trading Platform - Makefile Commands$(NC)"
	@echo ""
	@echo "Build Commands:"
	@echo "  make              - Check dependencies and prepare for install"
	@echo "  make clean        - Clean build artifacts"
	@echo ""
	@echo "Installation Commands (require root):"
	@echo "  sudo make install    - Full FHS-compliant installation"
	@echo "  sudo make uninstall  - Remove installation (preserves data)"
	@echo ""
	@echo "Service Commands (require root):"
	@echo "  sudo make start   - Start all services"
	@echo "  sudo make stop    - Stop all services"
	@echo "  sudo make restart - Restart all services"
	@echo "  sudo make status  - Check service status"
	@echo "  sudo make validate - Validate configuration"
	@echo ""
	@echo "Installation Directories (FHS-compliant):"
	@echo "  • Application: $(PREFIX)"
	@echo "  • Configuration: $(CONFIG_DIR)"
	@echo "  • Data: $(DATA_DIR)"
	@echo "  • Cache: $(CACHE_DIR)"
	@echo "  • Logs: $(LOG_DIR)"
	@echo ""
	@echo "Configuration:"
	@echo "  • Edit config: sudo nano $(CONFIG_DIR)/config.conf"
	@echo "  • Edit secrets: sudo nano $(CONFIG_DIR)/secrets.env"
	@echo "  • Service logs: journalctl -u falcon-dashboard -f"
	@echo "  • Nginx logs: tail -f /var/log/nginx/falcon_*.log"
	@echo ""
