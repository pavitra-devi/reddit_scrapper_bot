import praw
import os
from dotenv  import load_dotenv
from langchain_groq import ChatGroq
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler
from flask import Flask, request, jsonify
from telegram import Bot
from flask import Response
import requests

app = Flask(__name__)
load_dotenv()



reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent= os.getenv("REDDIT_USER_AGENT")
    )

token=os.getenv('TELEGRAM_BOT_TOKEN')


def fetch_reddit_posts_2(subreddit_name,limit=5):
    subreddit = reddit.subreddit(subreddit_name)
    results=subreddit.hot(limit=limit)
    print(results)
    posts=[]

    for post in results:
        posts.append({
            'title':post.title,
            'url':post.url,
            'text':post.selftext[:500], #limts to 500 chars
            'score':post.score,
            'comments':post.num_comments
        })
    return posts


def fetch_reddit_posts(subreddit_name, keyword, limit=5):
    subreddit = reddit.subreddit(subreddit_name)
    posts=[]

    for post in subreddit.search(keyword,limit):
        posts.append({
            'title':post.title,
            'url':post.url,
            'text':post.selftext[:500], #limts to 500 chars
            'score':post.score,
            'comments':post.num_comments
        })
    return posts




llm=ChatGroq(
    temperature=0,
    # model_name='deepseek-r1-distill-llama-70b',
    model_name=os.getenv('MODEL_NAME'),
    groq_api_key=os.getenv('GROQ_API_KEY'),
)

# result=llm.invoke("what is 2+ 2.00?")
# print(result)

def format_posts_for_prompt(posts):
    formatted_posts = ""
    for post in posts:
        formatted_posts += f"Title: {post['title']}\n"
        formatted_posts += f"URL: {post['url']}\n"
        formatted_posts += f"Text: {post['text']}...\n"
        formatted_posts += f"Score: {post['score']}\n"
        formatted_posts += f"Comments: {post['comments']}\n\n"
    return formatted_posts


def summarize_posts_content(posts_content):
    prompt="You are given with reddits posts, understang all posts data, give me a final summarization that is easily unserstanble and well structured. "
    formatted_posts = format_posts_for_prompt(posts_content)
    result=llm.invoke(prompt +"\n\n use this posts content to frame the formatted response :"+formatted_posts)
    print(result.content)
    return result.content


# summarize_posts_content(posts)


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
        subreddit, keyword = incoming_que.split(",")
        print("searching for these:",subreddit, keyword)
        posts = fetch_reddit_posts(subreddit, keyword)
        print(posts)
        answer = summarize_posts_content(posts)
        print(answer)
        send_message_telegram(chat_id, posts)
        return Response('ok', status=200)
    else:
        return "<h1>Something went wrong</h1>"


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False, port=5000)

