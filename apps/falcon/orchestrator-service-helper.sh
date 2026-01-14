#!/bin/bash
#
# Falcon Orchestrator Service Helper
# Quick commands for managing the orchestrator systemd service
#

SERVICE_NAME="falcon-orchestrator-daemon.service"

case "${1:-help}" in
    start)
        echo "Starting orchestrator service..."
        sudo systemctl start $SERVICE_NAME
        sleep 2
        sudo systemctl status $SERVICE_NAME --no-pager -l | head -20
        ;;

    stop)
        echo "Stopping orchestrator service..."
        sudo systemctl stop $SERVICE_NAME
        echo "✓ Service stopped"
        ;;

    restart)
        echo "Restarting orchestrator service..."
        sudo systemctl restart $SERVICE_NAME
        sleep 2
        sudo systemctl status $SERVICE_NAME --no-pager -l | head -20
        ;;

    status)
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;

    logs)
        LINES="${2:-50}"
        echo "Showing last $LINES lines of logs..."
        echo "==========================================="
        sudo journalctl -u $SERVICE_NAME -n $LINES --no-pager
        ;;

    follow)
        echo "Following logs (Ctrl+C to exit)..."
        echo "==========================================="
        sudo journalctl -u $SERVICE_NAME -f
        ;;

    enable)
        echo "Enabling service to start on boot..."
        sudo systemctl enable $SERVICE_NAME
        echo "✓ Service enabled"
        ;;

    disable)
        echo "Disabling service from starting on boot..."
        sudo systemctl disable $SERVICE_NAME
        echo "✓ Service disabled"
        ;;

    reload)
        echo "Reloading service configuration..."
        sudo systemctl daemon-reload
        echo "✓ Configuration reloaded"
        ;;

    info)
        echo "========================================="
        echo "Falcon Orchestrator Service Information"
        echo "========================================="
        echo ""
        echo "Service Name: $SERVICE_NAME"
        echo "Service File: /etc/systemd/system/$SERVICE_NAME"
        echo ""
        echo "Status:"
        sudo systemctl is-active $SERVICE_NAME
        echo ""
        echo "Enabled:"
        sudo systemctl is-enabled $SERVICE_NAME
        echo ""
        echo "Main Process:"
        systemctl show $SERVICE_NAME -p MainPID | cut -d= -f2
        echo ""
        echo "Uptime:"
        systemctl show $SERVICE_NAME -p ActiveEnterTimestamp | cut -d= -f2
        ;;

    help|*)
        echo "Falcon Orchestrator Service Helper"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  start       Start the orchestrator service"
        echo "  stop        Stop the orchestrator service"
        echo "  restart     Restart the orchestrator service"
        echo "  status      Show service status"
        echo "  logs [N]    Show last N lines of logs (default: 50)"
        echo "  follow      Follow logs in real-time"
        echo "  enable      Enable service to start on boot"
        echo "  disable     Disable service from starting on boot"
        echo "  reload      Reload systemd configuration"
        echo "  info        Show service information"
        echo "  help        Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 logs 100"
        echo "  $0 follow"
        ;;
esac
