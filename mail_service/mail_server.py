# mail_server.py
import smtpd
import asyncore
import threading

class DebuggingServer(smtpd.DebuggingServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        print("\n" + "="*20 + " [DEBUG EMAIL RECEIVED] " + "="*20)
        print(f"From: {mailfrom}")
        print(f"To: {rcpttos}")
        print("-" * 64)
        print(data.decode('utf-8', errors='ignore'))
        print("="*66 + "\n")

def run_smtp_server():
    print(">>> Starting local SMTP debug server on port 8025...")
    server = DebuggingServer(('0.0.0.0', 8025), None)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    server_thread = threading.Thread(target=run_smtp_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Keep the main thread alive to see the output
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nShutting down SMTP server.")