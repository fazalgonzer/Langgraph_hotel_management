from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import uuid
from langchain_core.messages import ToolMessage
from Graph import Graphing
from utilities import _print_event
import os 
from langchain_groq import ChatGroq



#initalize_rag()


# Set environment variable for API key
os.environ['TAVILY_API_KEY'] = "t"

# Initialize the chatbot model
llm = ChatGroq(api_key="", model="llama-3.2-11b-vision-preview")

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize the graph with the model
gr=Graphing()
graph=gr.build()
# Initialize thread id for each user session
thread_id = str(uuid.uuid4())

# Config settings (can be customized per user)
config = {
    "configurable": {
        # The passenger_id is used in our flight tools to
        # fetch the user's flight information
        "user_id": 1,
        # Checkpoints are accessed by thread_id
        "thread_id": thread_id,
    }
}
_printed = set()

@app.route('/')
def chat():
    return render_template('chat.html')

@socketio.on('message')
def handle_message(message):
    """Handle incoming messages from the user and send chatbot responses."""
    print(message)
    # Stream chatbot events and collect responses
    events = graph.stream({"messages": ("user", message)}, config, stream_mode="values")
    
    chatbot_responses = []  # Collect responses in a list
    for event in events:
        chatbot_response = _print_event(event, _printed)
        chatbot_responses.append(chatbot_response)  # Append each response
    
    emit('response', {'messages': chatbot_responses})  # Send the list of responses back to the client

   

if __name__ == '__main__':
    socketio.run(app, debug=True)