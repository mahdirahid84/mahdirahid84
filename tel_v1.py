import os
import csv
import asyncio
import sys
from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.channels import GetParticipantsRequest, InviteToChannelRequest
from telethon.tl.types import ChannelParticipantsSearch, InputChannel

api_id = 22817801  # Replace with your API ID
api_hash = '5def9cd85c79173fa5cd094368946410'  # Replace with your API Hash
session_name = 'user_session'

client = TelegramClient(session_name, api_id, api_hash)


async def fetch_groups():
    result = await client(GetDialogsRequest(
        offset_date=None,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=200,
        hash=0
    ))
    groups = []
    for chat in result.chats:
        if getattr(chat, 'megagroup', False):
            groups.append(chat)
    return groups


def display_groups(groups):
    print("\n📋 Group List:")
    for i, group in enumerate(groups):
        print(f"{i} - {group.title[::-1]}")  # Reverse to simulate RTL


async def extract_members(group):
    print(f"\nExtracting members from group: {group.title[::-1]}")
    offset = 0
    limit = 100
    all_participants = []

    while True:
        participants = await client(GetParticipantsRequest(
            InputChannel(group.id, group.access_hash),
            filter=ChannelParticipantsSearch(''),
            offset=offset,
            limit=limit,
            hash=0
        ))
        if not participants.users:
            break
        all_participants.extend(participants.users)
        offset += len(participants.users)

    with open("group_members.csv", "w", encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "username", "first_name", "last_name", "phone"])
        for user in all_participants:
            writer.writerow([
                user.id,
                user.username or '',
                user.first_name or '',
                user.last_name or '',
                user.phone or ''
            ])

    print("✅ Members extracted to group_members.csv")


async def add_members(target_group, filename):
    users = []
    with open(filename, encoding='utf-8') as f:
        rows = csv.reader(f)
        next(rows)
        for row in rows:
            users.append(row)

    count = int(input("🔢 How many members do you want to add? (0 = all): ") or "0")
    if count == 0:
        count = len(users)

    for i, user in enumerate(users[:count]):
        try:
            if user[1]:  # username exists
                print(f"➕ Adding @{user[1]}...")
                await client(InviteToChannelRequest(
                    InputChannel(target_group.id, target_group.access_hash),
                    [user[1]]
                ))
                await asyncio.sleep(10)
            else:
                print(f"⚠️ Skipping user {user[0]} (no username)")
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
            break
        except Exception as e:
            print(f"❌ Error adding {user[1]}: {e}")
            continue


async def main():
    await client.start()
    print("✅ Logged in!")

    while True:
        print("\n📌 What do you want to do?")
        print("1 - Extract group members")
        print("2 - Add members to a group")
        print("0 - Exit")

        choice = input("Enter your choice: ").strip()
        if choice == "0":
            print("👋 Exiting.")
            await client.disconnect()
            sys.exit(0)

        groups = await fetch_groups()
        display_groups(groups)

        try:
            idx = int(input("Select group index: "))
            group = groups[idx]
        except Exception:
            print("⚠️ Invalid index")
            continue

        if choice == "1":
            await extract_members(group)
        elif choice == "2":
            filename = input("Enter CSV filename (e.g., group_members.csv): ").strip()
            if not os.path.exists(filename):
                print("⚠️ File not found.")
                continue
            await add_members(group, filename)
        else:
            print("⚠️ Invalid choice.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ An error occurred: {e}")
