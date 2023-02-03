import imaplib
from email import message_from_bytes
from notion_client import Client as NotionClient
import env.configs

def get_emails_from_server(server, email, password):
    """Connect to email server and get all emails."""
    # Connect to email server
    try:
        mail = imaplib.IMAP4_SSL(server)
        mail.login(email, password)
        mail.select("inbox")
        result, data = mail.search(None, "ALL")
        email_ids = data[0].split()
    except Exception as e:
        print(f"Error connecting to email server: {e}")
        return []
  
    # Get details for each email
    emails = []
    for email_id in email_ids:
        result, data = mail.fetch(email_id, "(RFC822)")
        for response in data:
            if isinstance(response, tuple):
                msg = message_from_bytes(response[1])
                emails.append({
                    "id": email_id,
                    "subject": msg["subject"],
                    "from": msg["from"],
                    "to": msg["to"],
                    "body": msg.get_payload(),
                })
    return emails

def main():
    # Connect to Notion API
    notion = NotionClient(auth=env.configs.notion_token)
  
    # Connect to email servers and get emails
    email_servers = env.configs.email_servers
        
    all_emails = []
    for server_info in email_servers:
        emails = get_emails_from_server(**server_info)
        all_emails.extend(emails)
  
    # Save emails and attachments to Notion database
    database_id = env.configs.mail_dbid
    database = notion.databases.retrieve(database_id)
    existing_emails = {e["Email ID"]: e for e in database.get("records")}
    for email in all_emails:
        email_id = email["id"]
        if email_id in existing_emails:
            continue
        new_page = {
            "Email ID": email_id,
            "Subject": email["subject"],
            "From": email["from"],
            "To": email["to"],
            "Body": email["body"],
        }
        database.pages.create(new_page)

if __name__ == "__main__":
    main()
