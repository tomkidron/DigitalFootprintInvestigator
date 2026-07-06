import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv


def main():
    print("=========================================")
    print("Telegram Session Setup for OSINT Tool")
    print("=========================================\n")

    # Load environment variables
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        print(f"[ERROR] Could not find .env file at {env_path}")
        print("Please copy .env.example to .env and configure it.")
        return

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")

    if not api_id or not api_hash:
        print("[ERROR] TELEGRAM_API_ID and/or TELEGRAM_API_HASH are not set in your .env file.")
        print("Please get them from https://my.telegram.org and add them to .env")
        return

    if not phone:
        print("[WARN] TELEGRAM_PHONE is not set in your .env file.")
        phone = input("Please enter your phone number with country code (e.g. +1234567890): ").strip()
        if not phone:
            print("[ERROR] Phone number is required.")
            return

    try:
        from telethon.sync import TelegramClient
    except ImportError:
        print("[ERROR] Telethon is not installed. Please run: pip install -r requirements.txt")
        return

    # Use 'anon' session name in the project root
    session_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "anon")

    print("\nInitializing Telegram client...")
    print(f"Session will be saved as: {session_path}.session")

    client = TelegramClient(session_path, int(api_id), api_hash)
    client.connect()

    if not client.is_user_authorized():
        print("\n[INFO] You are not logged in. Sending request to Telegram...")
        try:
            client.send_code_request(phone)
            print("\n[ACTION REQUIRED]")
            print("Telegram just sent a code to your Telegram app (or via SMS if app is not available).")
            code = input("Please enter the code you received: ").strip()

            client.sign_in(phone, code)
            print("\n[SUCCESS] Successfully authenticated!")
            print("The session file has been created. The OSINT tool can now use Telegram search.")
        except Exception as e:
            print(f"\n[ERROR] Authentication failed: {str(e)}")
            if "PhoneCodeInvalid" in str(e):
                print("The code you entered is invalid.")
            elif "Two-steps verification is enabled" in str(e) or "SessionPasswordNeededError" in str(e):
                print("\n[ACTION REQUIRED]")
                print("Two-step verification is enabled for your account.")
                # Fallback to standard input if getpass fails in background tasks
                try:
                    import getpass

                    password = getpass.getpass("Please enter your 2FA password: ")
                except Exception:
                    password = input("Please enter your 2FA password: ").strip()

                try:
                    client.sign_in(password=password)
                    print("\n[SUCCESS] Successfully authenticated with 2FA!")
                    print("The session file has been created. The OSINT tool can now use Telegram search.")
                except Exception as e2:
                    print(f"\n[ERROR] 2FA authentication failed: {str(e2)}")
    else:
        print("\n[SUCCESS] You are already authenticated!")
        print("The session file is ready to use.")

    client.disconnect()


if __name__ == "__main__":
    main()
