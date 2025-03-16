from flask import Flask
from flask import request
from flask import Response
import requests
import openai
import os
from reddit_scrapper import llm
# # Give OpenAI Key
# openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)
# Get BOT Token from telegram
token = os.environ.get("TELEGRAM_BOT_TOKEN")


# print(token)

def generate_answer(question):
   
    result=llm.invoke(question)

    # answer = response.choices[0].text.strip()
    return result.content


# To Get Chat ID and message which is sent by client
def message_parser(message):
    print("inside msg parsing")
    chat_id = message['message']['chat']['id']
    text = message['message']['text']
    print("Chat ID: ", chat_id)
    print("Message: ", text)
    return chat_id, text


# To send message using "SendMessage" API
def send_message_telegram(chat_id, text):
    print("inside send message")
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, json=payload)
    print(response)
    if response.status_code != 200:
        print(f"Error sending message: {response.status_code}, {response.text}")
    return response
    


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print("inside post")
        msg = request.get_json()
        chat_id, incoming_que = message_parser(msg)
        answer = generate_answer(incoming_que)
        # answer=fetch_reddit_posts_2(incoming_que)
        print(answer)
        send_message_telegram(chat_id, answer)
        return Response('ok', status=200)
    else:
        return "<h1>Something went wrong</h1>"


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False, port=5000)