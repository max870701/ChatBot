import openai
import requests
import logging
import sqlite3

# Initialize the logging module
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Initialize the database connection
conn = sqlite3.connect('chatbot.db')
cursor = conn.cursor()

# Create the database table to store information between sessions
table_create_sql = '''
CREATE TABLE IF NOT EXISTS user_info (
    user_id TEXT PRIMARY KEY,
    info TEXT
);
'''
cursor.execute(table_create_sql)
conn.commit()

# Initialize the ChatGPT model
openai.api_key = "your_openai_api_key"
model_engine = "text-davinci-002"

# Function to generate a response using ChatGPT
def generate_response(prompt, context):
    completions = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
        context=context
    )

    message = completions.choices[0].text
    return message

# Function to handle incoming messages from the LINE API
def handle_message(event):
    user_id = event["source"]["userId"]
    message = event["message"]["text"]

    # Retrieve any stored information for the user from the database
    cursor.execute('SELECT info FROM user_info WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    context = result[0] if result else ''

    response = generate_response(prompt=message, context=context)

    # Store the generated context back in the database
    cursor.execute('REPLACE INTO user_info (user_id, info) VALUES (?, ?)', (user_id, response))
    conn.commit()

    # Send the response back to the user through the LINE API
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer your_line_api_access_token",
    }
    data = {
        "to": user_id,
        "messages": [{"type": "text", "text": response}],
    }
    response = requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, data=data)

    # Log the response from the LINE API
    if response.status_code != 200:
        logging.error('Failed to send message: %s', response.text)

# Main function to listen for incoming events from the LINE API
def main():
    # Get the latest events from the LINE API
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer your_line_api_access_token",
    }
    response = requests.get("https://api.line.me/v2/bot/message/events", headers=headers)

    # Handle any errors from the LINE API
    if response.status_code != 200:
        logging.error('Failed to retrieve events: %s', response.text)
        return

    events = response.json()["events"]

    # Handle each event
    for event in events:
        handle_message(event)

if __name__ == "__main__":
    main()
