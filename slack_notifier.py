"""
MewaK E-Commerce Platform - Slack Webhook Notification Service
Sends real-time Slack alerts for new orders, order status changes, and low stock warnings.

Usage:
    from slack_notifier import send_new_order_alert, send_low_stock_alert, send_status_change_alert
"""

import os
import requests
import json

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

def send_slack_message(payload: dict, webhook_url: str = None) -> bool:
    """Generic function to post formatted block payloads to a Slack Incoming Webhook."""
    target_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL", "")
    if not target_url:
        print("[Slack Notifier] Notice: No SLACK_WEBHOOK_URL configured. Notification skipped.")
        return False

    try:
        response = requests.post(
            target_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        if response.status_code == 200:
            print("[Slack Notifier] Message sent successfully!")
            return True
        else:
            print(f"[Slack Notifier] Error: Slack returned status {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[Slack Notifier] Exception occurred: {str(e)}")
        return False


def send_new_order_alert(order_id: str, user_email: str, total_amount: float, shipping_address: str, items_count: int = 1, webhook_url: str = None) -> bool:
    """Send an instant Slack notification when a new customer order is placed."""
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎉 New MewaK Order Placed!",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Order ID:*\n`{order_id}`"},
                    {"type": "mrkdwn", "text": f"*Total Amount:*\n*₹{total_amount:,.2f}*"},
                    {"type": "mrkdwn", "text": f"*Customer:*\n{user_email}"},
                    {"type": "mrkdwn", "text": f"*Items Count:*\n{items_count} item(s)"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Shipping Address:*\n{shipping_address}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "⚡ *Action Required:* Open Admin Portal to process and package order."}
                ]
            },
            {"type": "divider"}
        ]
    }
    return send_slack_message(payload, webhook_url)


def send_low_stock_alert(product_title: str, product_id: str, remaining_stock: int, webhook_url: str = None) -> bool:
    """Send an urgent Slack notification when a product's stock drops below threshold."""
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠️ Low Stock Warning - Action Required",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Product *{product_title}* (`{product_id}`) is running low on stock!"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Remaining Units:*\n`{remaining_stock}` units"},
                    {"type": "mrkdwn", "text": "*Status:*\n🔴 *Restock Needed*"}
                ]
            },
            {"type": "divider"}
        ]
    }
    return send_slack_message(payload, webhook_url)


def send_status_change_alert(order_id: str, new_status: str, payment_status: str = "PAID", webhook_url: str = None) -> bool:
    """Send a Slack notification when an order's fulfillment state is updated."""
    status_emojis = {
        "CONFIRMED": "✅",
        "PROCESSING": "📦",
        "SHIPPED": "🚚",
        "DELIVERED": "🏠",
        "CANCELLED": "❌"
    }
    emoji = status_emojis.get(new_status, "🔄")
    
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Order Status Update: {order_id}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*New Order State:*\n`{new_status}`"},
                    {"type": "mrkdwn", "text": f"*Payment Status:*\n`{payment_status}`"}
                ]
            },
            {"type": "divider"}
        ]
    }
    return send_slack_message(payload, webhook_url)


if __name__ == "__main__":
    print("Testing Slack Notifier module...")
    test_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if test_url:
        send_new_order_alert("MWK-2026-9999", "test@mewak.com", 1499.00, "123 Tech Park, Bangalore", 2)
    else:
        print("Set SLACK_WEBHOOK_URL environment variable to run live Slack tests.")
